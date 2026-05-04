"""
Aether-1 Engine — FastAPI Backend
Runs real-time trading with continuous signal generation and position management.
Stores real-time results in Neon PostgreSQL, serves data to React frontend.
"""

import sys
import os
import warnings
import asyncio
import threading
from datetime import datetime
from typing import List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)
import strategy
from realtime_engine import RealtimeTradingEngine

load_dotenv(os.path.join(PARENT_DIR, ".env"))

app = FastAPI(title="Aether-1 Engine API - Real-Time Trading", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.getenv("DB_URL")

# ─── Global State ───────────────────────────────────────────

trading_engine: Optional[RealtimeTradingEngine] = None
engine_task: Optional[asyncio.Task] = None
engine_lock = threading.Lock()

# ─── Database ───────────────────────────────────────────────

def get_conn():
    return psycopg.connect(DB_URL, row_factory=dict_row)

def init_db():
    """Initialize database schema for real-time trading."""
    conn = get_conn()
    cur = conn.cursor()
    
    # Create tables if they don't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS realtime_sessions (
            id SERIAL PRIMARY KEY,
            tickers TEXT NOT NULL,
            status VARCHAR(20),
            capital NUMERIC(15,2),
            created_at TIMESTAMP DEFAULT NOW(),
            final_equity NUMERIC(15,2),
            total_trades INT,
            total_return NUMERIC(15,4)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS realtime_trades (
            id SERIAL PRIMARY KEY,
            session_id INT REFERENCES realtime_sessions(id),
            ticker VARCHAR(10),
            event_type VARCHAR(20),
            price NUMERIC(15,4),
            shares NUMERIC(15,4),
            confidence NUMERIC(5,4),
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS realtime_snapshots (
            id SERIAL PRIMARY KEY,
            session_id INT REFERENCES realtime_sessions(id),
            equity NUMERIC(15,2),
            cash NUMERIC(15,2),
            positions JSONB,
            metrics JSONB,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_config (
            id SERIAL PRIMARY KEY,
            session_id INT REFERENCES realtime_sessions(id),
            is_active BOOLEAN DEFAULT FALSE,
            tickers TEXT,
            initial_capital NUMERIC(15,2),
            interval_seconds INT DEFAULT 3600,
            last_run_at TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

async def run_trading_engine(tickers: List[str], initial_capital: float, interval_seconds: int):
    """Run the real-time trading engine."""
    global trading_engine
    
    with engine_lock:
        trading_engine = RealtimeTradingEngine(DB_URL, tickers, initial_capital)
    
    await trading_engine.run(interval_seconds=interval_seconds)

    await trading_engine.run(interval_seconds=interval_seconds)

@app.on_event("startup")
async def startup_event():
    print("Initializing database...")
    init_db()
    print("Aether-1 Real-Time Trading Engine started")


# ─── Models ─────────────────────────────────────────────────

class BacktestRequest(BaseModel):
    tickers: List[str] = ["SPY", "QQQ", "IWM"]
    start: str = "2018-01-01"
    end: str = datetime.today().strftime('%Y-%m-%d')
    capital: float = 10000.0

class StartTradingRequest(BaseModel):
    tickers: List[str]
    initial_capital: float = 100000.0
    interval_seconds: int = 3600  # 1 hour

class TradeResponse(BaseModel):
    timestamp: datetime
    ticker: str
    event_type: str
    price: float
    shares: float
    confidence: float



# ─── Real-Time Trading Endpoints ────────────────────────────

@app.get("/api/health")
def health():
    status = "trading" if trading_engine and trading_engine.running else "idle"
    return {"status": "ok", "engine": "Aether-1", "version": "2.0.0", "mode": "realtime", "trading_status": status}

@app.post("/api/trading/start")
async def start_trading(req: StartTradingRequest):
    """Start real-time trading session."""
    global trading_engine, engine_task
    
    with engine_lock:
        if trading_engine and trading_engine.running:
            raise HTTPException(status_code=400, detail="Trading already running")
        
        # Create and start new engine
        engine_task = asyncio.create_task(
            run_trading_engine(req.tickers, req.initial_capital, req.interval_seconds)
        )
        
        # Get session ID
        await asyncio.sleep(1)
        if trading_engine and trading_engine.session_id:
            return {
                "status": "started",
                "session_id": trading_engine.session_id,
                "tickers": req.tickers,
                "initial_capital": req.initial_capital,
                "interval": req.interval_seconds
            }
    
    raise HTTPException(status_code=500, detail="Failed to start trading engine")

@app.post("/api/trading/stop")
def stop_trading():
    """Stop real-time trading session."""
    global trading_engine
    
    with engine_lock:
        if not trading_engine or not trading_engine.running:
            raise HTTPException(status_code=400, detail="Trading not running")
        
        session_id = trading_engine.session_id
        trading_engine.stop()
        
        return {
            "status": "stopped",
            "session_id": session_id
        }

@app.get("/api/trading/status")
def get_trading_status():
    """Get current trading status."""
    with engine_lock:
        if not trading_engine:
            return {
                "running": False,
                "session_id": None,
                "positions": [],
                "metrics": {}
            }
        
        metrics = trading_engine.portfolio.get_metrics()
        positions = trading_engine.portfolio.get_all_positions()
        
        positions_data = []
        for ticker, pos in positions.items():
            positions_data.append({
                "ticker": ticker,
                "shares": pos["shares"],
                "entry_price": float(pos["entry_price"]),
                "current_price": float(pos["current_price"]),
                "entry_date": pos["entry_date"].isoformat(),
                "unrealized_pnl": float((pos["current_price"] - pos["entry_price"]) * pos["shares"]),
                "unrealized_pnl_pct": float(((pos["current_price"] - pos["entry_price"]) / pos["entry_price"]) * 100) if pos["entry_price"] > 0 else 0
            })
        
        return {
            "running": trading_engine.running,
            "session_id": trading_engine.session_id,
            "equity": round(metrics["equity"], 2),
            "cash": round(trading_engine.portfolio.cash, 2),
            "total_return": round(metrics["total_return"], 2),
            "return_pct": round(metrics["return_pct"], 4),
            "positions": positions_data,
            "positions_count": len(positions),
            "total_trades": metrics["total_trades"],
            "winning_trades": metrics["winning_trades"],
            "losing_trades": metrics["losing_trades"],
            "win_rate": round(metrics["win_rate"], 2),
            "max_dd": round(metrics["max_dd"], 2),
            "profit_factor": round(metrics["profit_factor"], 2),
            "last_update": trading_engine.portfolio.last_update.isoformat()
        }

@app.get("/api/trading/sessions/{session_id}")
def get_session_details(session_id: int):
    """Get details of a trading session."""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM realtime_sessions WHERE id=%s", (session_id,))
    session = cur.fetchone()
    
    if not session:
        cur.close()
        conn.close()
        raise HTTPException(404, "Session not found")
    
    # Get trades
    cur.execute(
        "SELECT * FROM realtime_trades WHERE session_id=%s ORDER BY timestamp DESC",
        (session_id,)
    )
    trades = cur.fetchall()
    
    # Get latest snapshot
    cur.execute(
        "SELECT * FROM realtime_snapshots WHERE session_id=%s ORDER BY timestamp DESC LIMIT 1",
        (session_id,)
    )
    latest_snapshot = cur.fetchone()
    
    cur.close()
    conn.close()
    
    return {
        "session": dict(session),
        "trades": [dict(t) for t in trades],
        "latest_snapshot": dict(latest_snapshot) if latest_snapshot else None
    }

@app.get("/api/trading/trades/{session_id}")
def get_session_trades(session_id: int, limit: int = 100):
    """Get trades from a session."""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT * FROM realtime_trades WHERE session_id=%s ORDER BY timestamp DESC LIMIT %s",
        (session_id, limit)
    )
    trades = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "trades": [dict(t) for t in trades],
        "count": len(trades)
    }

@app.get("/api/trading/positions/{session_id}")
def get_session_positions(session_id: int):
    """Get latest positions from a session."""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT positions FROM realtime_snapshots WHERE session_id=%s ORDER BY timestamp DESC LIMIT 1",
        (session_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if not result:
        return {"positions": {}}
    
    return {"positions": result["positions"]}

@app.get("/api/trading/history")
def get_sessions_history(limit: int = 20):
    """Get recent trading sessions."""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute(
        "SELECT id, tickers, status, capital, created_at, final_equity, total_trades, total_return "
        "FROM realtime_sessions ORDER BY created_at DESC LIMIT %s",
        (limit,)
    )
    sessions = cur.fetchall()
    cur.close()
    conn.close()
    
    return {
        "sessions": [dict(s) for s in sessions],
        "count": len(sessions)
    }


# ─── 30-Day Continuous Agent Endpoints ──────────────────────

@app.post("/api/trading/start-30days")
async def start_30day_trading(req: StartTradingRequest):
    """Start 30-day continuous trading agent by updating agent_config."""
    conn = get_conn()
    cur = conn.cursor()
    
    try:
        # Check if already active
        cur.execute("SELECT id FROM agent_config WHERE is_active = TRUE")
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="30-day agent already running")
        
        # Create new session
        tickers_str = ",".join(req.tickers)
        cur.execute(
            "INSERT INTO realtime_sessions (tickers, status, capital) VALUES (%s, %s, %s) RETURNING id",
            (tickers_str, "active_agent", req.initial_capital)
        )
        session_id = cur.fetchone()["id"]
        
        # Update/Insert agent_config
        cur.execute("SELECT id FROM agent_config LIMIT 1")
        config = cur.fetchone()
        
        if config:
            cur.execute(
                "UPDATE agent_config SET session_id=%s, is_active=TRUE, tickers=%s, "
                "initial_capital=%s, interval_seconds=%s, last_run_at=NULL WHERE id=%s",
                (session_id, tickers_str, req.initial_capital, req.interval_seconds, config["id"])
            )
        else:
            cur.execute(
                "INSERT INTO agent_config (session_id, is_active, tickers, initial_capital, interval_seconds) "
                "VALUES (%s, TRUE, %s, %s, %s)",
                (session_id, tickers_str, req.initial_capital, req.interval_seconds)
            )
        
        conn.commit()
        return {
            "status": "started",
            "session_id": session_id,
            "message": "Persistent agent initialized. worker.py will begin cycles shortly."
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@app.post("/api/trading/stop-30days")
def stop_30day_trading():
    """Stop 30-day continuous trading agent."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT session_id FROM agent_config WHERE is_active = TRUE")
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=400, detail="30-day agent not running")
        
        session_id = row["session_id"]
        cur.execute("UPDATE agent_config SET is_active = FALSE")
        cur.execute("UPDATE realtime_sessions SET status = 'closed' WHERE id = %s", (session_id,))
        
        conn.commit()
        return {"status": "stopped", "session_id": session_id}
    finally:
        cur.close()
        conn.close()

@app.get("/api/trading/30days-status")
def get_30day_status():
    """Get status of 30-day continuous agent from DB."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM agent_config LIMIT 1")
        config = cur.fetchone()
        
        if not config or not config["is_active"]:
            return {"running": False, "message": "No active agent configuration"}
        
        session_id = config["session_id"]
        
        # Get session details
        cur.execute("SELECT * FROM realtime_sessions WHERE id=%s", (session_id,))
        session = cur.fetchone()
        
        # Get latest snapshot
        cur.execute(
            "SELECT * FROM realtime_snapshots WHERE session_id=%s ORDER BY timestamp DESC LIMIT 1",
            (session_id,)
        )
        snapshot = cur.fetchone()
        
        if not session:
            return {"running": True, "session_id": session_id, "error": "Session missing"}

        return {
            "running": config["is_active"],
            "session_id": session_id,
            "tickers": config["tickers"].split(","),
            "status": session["status"],
            "created_at": session["created_at"].isoformat() if session["created_at"] else None,
            "equity": snapshot["equity"] if snapshot else 0,
            "cash": snapshot["cash"] if snapshot else 0,
            "positions_count": len(snapshot["positions"]) if snapshot and snapshot["positions"] else 0,
            "metrics": snapshot["metrics"] if snapshot else {},
            "last_update": snapshot["timestamp"].isoformat() if snapshot and snapshot["timestamp"] else None,
            "last_run_at": config["last_run_at"].isoformat() if config["last_run_at"] else None
        }
    finally:
        cur.close()
        conn.close()

@app.get("/api/trading/30days-log")
def get_30day_log(limit: int = 50):
    """Get recent trades from 30-day agent."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT session_id FROM agent_config WHERE is_active = TRUE")
        row = cur.fetchone()
        if not row:
            return {"trades": [], "count": 0, "message": "No active session"}
            
        session_id = row["session_id"]
        cur.execute(
            "SELECT * FROM realtime_trades WHERE session_id=%s ORDER BY timestamp DESC LIMIT %s",
            (session_id, limit)
        )
        trades = cur.fetchall()
        return {
            "trades": [dict(t) for t in trades],
            "count": len(trades),
            "session_id": session_id
        }
    finally:
        cur.close()
        conn.close()
