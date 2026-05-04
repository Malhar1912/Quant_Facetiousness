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

# 30-day continuous agent state
continuous_agent_task: Optional[asyncio.Task] = None
continuous_agent_running: bool = False
continuous_agent_session_id: Optional[int] = None
continuous_agent_lock = threading.Lock()

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
    
    conn.commit()
    cur.close()
    conn.close()

async def run_trading_engine(tickers: List[str], initial_capital: float, interval_seconds: int):
    """Run the real-time trading engine."""
    global trading_engine
    
    with engine_lock:
        trading_engine = RealtimeTradingEngine(DB_URL, tickers, initial_capital)
    
    await trading_engine.run(interval_seconds=interval_seconds)

async def run_continuous_agent(tickers: List[str], initial_capital: float, duration_days: int = 30):
    """Run continuous trading agent for specified days."""
    global continuous_agent_running, continuous_agent_session_id
    
    print(f"\n{'='*60}")
    print(f"Starting 30-Day Continuous Trading Agent")
    print(f"Tickers: {', '.join(tickers)}")
    print(f"Initial Capital: ${initial_capital:,.2f}")
    print(f"Duration: {duration_days} days")
    print(f"{'='*60}\n")
    
    engine = RealtimeTradingEngine(DB_URL, tickers, initial_capital)
    continuous_agent_session_id = engine.start_session()
    continuous_agent_running = True
    
    try:
        # Run for 30 days with 1-hour intervals
        # 30 days * 24 hours = 720 hours
        cycles = 30 * 24
        interval_seconds = 3600  # 1 hour
        
        start_time = datetime.now()
        
        for cycle in range(cycles):
            if not continuous_agent_running:
                print("Continuous agent stopped by user")
                break
            
            elapsed = datetime.now() - start_time
            days_elapsed = elapsed.total_seconds() / (24 * 3600)
            
            print(f"\n[Day {days_elapsed:.1f}/{duration_days}] Continuous Agent Cycle {cycle + 1}/{cycles}")
            
            try:
                # Fetch data
                data = engine.fetch_live_data()
                
                # Generate signals
                signals = engine.generate_signals(data)
                
                # Execute trades
                engine.execute_trades(signals)
                
                # Save snapshot
                engine.save_snapshot()
                
                # Print status
                metrics = engine.portfolio.get_metrics()
                print(f"✓ Portfolio Equity: ${metrics['equity']:,.2f} | "
                      f"Return: {metrics['return_pct']:.2f}% | "
                      f"Trades: {metrics['total_trades']} | "
                      f"Positions: {len(engine.portfolio.get_all_positions())}")
                
            except Exception as e:
                print(f"✗ Error in trading cycle: {e}")
            
            # Wait before next cycle (1 hour)
            print(f"Sleeping for {interval_seconds}s until next cycle...")
            await asyncio.sleep(interval_seconds)
        
        print(f"\n✓ 30-Day continuous agent completed successfully")
        
    except Exception as e:
        print(f"✗ Error in continuous agent: {e}")
    
    finally:
        continuous_agent_running = False
        engine.end_session()
        print(f"Session {continuous_agent_session_id} closed")

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
    """Start 30-day continuous trading agent (runs in background)."""
    global continuous_agent_task, continuous_agent_running
    
    with continuous_agent_lock:
        if continuous_agent_running:
            raise HTTPException(status_code=400, detail="30-day agent already running")
        
        # Create background task
        continuous_agent_task = asyncio.create_task(
            run_continuous_agent(req.tickers, req.initial_capital, duration_days=30)
        )
        
        return {
            "status": "started",
            "mode": "30-day-continuous",
            "tickers": req.tickers,
            "initial_capital": req.initial_capital,
            "duration_days": 30,
            "message": "Trading will continue for 30 days even if browser closes"
        }

@app.post("/api/trading/stop-30days")
def stop_30day_trading():
    """Stop 30-day continuous trading agent."""
    global continuous_agent_running, continuous_agent_session_id
    
    with continuous_agent_lock:
        if not continuous_agent_running:
            raise HTTPException(status_code=400, detail="30-day agent not running")
        
        continuous_agent_running = False
        session_id = continuous_agent_session_id
        
        return {
            "status": "stopped",
            "session_id": session_id,
            "message": "30-day agent has been stopped"
        }

@app.get("/api/trading/30days-status")
def get_30day_status():
    """Get status of 30-day continuous agent."""
    with continuous_agent_lock:
        if not continuous_agent_running or not continuous_agent_session_id:
            return {
                "running": False,
                "session_id": None,
                "message": "No 30-day agent currently running"
            }
        
        # Get session details from database
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM realtime_sessions WHERE id=%s", (continuous_agent_session_id,))
        session = cur.fetchone()
        
        # Get latest snapshot
        cur.execute(
            "SELECT * FROM realtime_snapshots WHERE session_id=%s ORDER BY timestamp DESC LIMIT 1",
            (continuous_agent_session_id,)
        )
        latest_snapshot = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not session:
            return {
                "running": continuous_agent_running,
                "session_id": continuous_agent_session_id,
                "error": "Session not found"
            }
        
        session_dict = dict(session)
        snapshot = dict(latest_snapshot) if latest_snapshot else {}
        
        return {
            "running": continuous_agent_running,
            "session_id": continuous_agent_session_id,
            "tickers": session_dict.get("tickers", "").split(","),
            "status": session_dict.get("status", "active"),
            "created_at": session_dict.get("created_at", "").isoformat() if session_dict.get("created_at") else None,
            "equity": snapshot.get("equity", 0),
            "cash": snapshot.get("cash", 0),
            "positions_count": len(snapshot.get("positions", {})) if snapshot.get("positions") else 0,
            "metrics": snapshot.get("metrics", {}),
            "last_update": snapshot.get("timestamp", "").isoformat() if snapshot.get("timestamp") else None
        }

@app.get("/api/trading/30days-log")
def get_30day_log(limit: int = 50):
    """Get recent trades from 30-day agent."""
    with continuous_agent_lock:
        if not continuous_agent_session_id:
            return {
                "trades": [],
                "count": 0,
                "message": "No 30-day session available"
            }
        
        conn = get_conn()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT * FROM realtime_trades WHERE session_id=%s ORDER BY timestamp DESC LIMIT %s",
            (continuous_agent_session_id, limit)
        )
        trades = cur.fetchall()
        cur.close()
        conn.close()
        
        return {
            "trades": [dict(t) for t in trades],
            "count": len(trades),
            "session_id": continuous_agent_session_id
        }
