"""
Aether-1 Engine — FastAPI Backend
Runs strategy.py backtests, stores results in Neon PostgreSQL,
serves data to React frontend.
"""

import sys
import os
import warnings
import asyncio
from datetime import datetime
from typing import List

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

load_dotenv(os.path.join(PARENT_DIR, ".env"))

app = FastAPI(title="Aether-1 Engine API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.getenv("DB_URL")

# ─── Database ───────────────────────────────────────────────

def get_conn():
    return psycopg.connect(DB_URL, row_factory=dict_row)



async def continuous_trading_agent():
    while True:
        try:
            print("Starting live trading agent cycle...")
            req = BacktestRequest()
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, run_backtest, req)
            print("Live trading agent cycle completed. Waiting for 24 hours...")
        except Exception as e:
            print(f"Error in trading agent loop: {e}")
        
        # Sleep for 24 hours (8640000 seconds)
        await asyncio.sleep(8640000)

@app.on_event("startup")
async def startup_event():
    # Start the continuous agent in the background
    asyncio.create_task(continuous_trading_agent())
    print("Agent started in continuous mode for tickers.")


# ─── Models ─────────────────────────────────────────────────

class BacktestRequest(BaseModel):
    tickers: List[str] = ["SPY", "GME", "BTC-USD"]
    start: str = "2018-01-01"
    end: str = datetime.today().strftime('%Y-%m-%d')
    capital: float = 10000.0


# ─── Helpers ────────────────────────────────────────────────

def serialize_equity(eq: pd.Series, max_pts: int = 500) -> list:
    if len(eq) > max_pts:
        eq = eq.iloc[:: len(eq) // max_pts]
    return [
        {"date": d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d),
         "value": round(float(v), 2)}
        for d, v in eq.items()
    ]


def serialize_trades(trades: list) -> list:
    return [
        {"entry_day": t["entry_day"].strftime("%Y-%m-%d") if hasattr(t["entry_day"], "strftime") else str(t["entry_day"]),
         "exit_day": t["exit_day"].strftime("%Y-%m-%d") if hasattr(t["exit_day"], "strftime") else str(t["exit_day"]),
         "entry_price": round(float(t["entry_price"]), 2),
         "exit_price": round(float(t["exit_price"]), 2),
         "ret": round(float(t["ret"]) * 100, 4)}
        for t in trades
    ]


def metrics_dict(m: dict) -> dict:
    return {k: round(float(v), 4) if isinstance(v, (float, np.floating)) else int(v)
            for k, v in m.items()}


# ─── Endpoints ──────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "engine": "Aether-1", "version": "4.2"}


@app.post("/api/backtest")
def run_backtest(req: BacktestRequest):
    conn = get_conn()
    cur = conn.cursor()
    try:
        tickers_str = ",".join(req.tickers)
        cur.execute(
            "INSERT INTO backtest_runs (tickers,start_date,end_date,capital_per_ticker,status) "
            "VALUES (%s,%s,%s,%s,'running') RETURNING id",
            (tickers_str, req.start, req.end, req.capital))
        run_id = cur.fetchone()["id"]
        conn.commit()

        portfolio_df = pd.DataFrame()
        ticker_out = []

        for ticker in req.tickers:
            try:
                df_raw = strategy.load_data(ticker, start=req.start, end=req.end)
                if len(df_raw) < 500:
                    continue
                df_ml = strategy.engineer_features(df_raw)
                acc = strategy.evaluate_signal_quality(df_ml)
                eq, trades = strategy.run_walk_forward_backtest(df_ml, starting_capital=req.capital)
                portfolio_df[ticker] = eq
                m = strategy.calculate_metrics(eq, trades)
                eq_json = serialize_equity(eq)
                tr_json = serialize_trades(trades)

                cur.execute(
                    "INSERT INTO ticker_results "
                    "(run_id,ticker,total_return,cagr,volatility,sharpe,sortino,"
                    "max_dd,calmar,total_trades,win_rate,avg_win,avg_loss,"
                    "profit_factor,expectancy,trade_sharpe,xgb_accuracy,equity_curve,trades) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (run_id, ticker, float(m["total_return"]), float(m["cagr"]),
                     float(m["volatility"]), float(m["sharpe"]), float(m["sortino"]),
                     float(m["max_dd"]), float(m["calmar"]), int(m["total_trades"]),
                     float(m["win_rate"]), float(m["avg_win"]), float(m["avg_loss"]),
                     float(m["profit_factor"]), float(m["expectancy"]),
                     float(m.get("trade_sharpe", 0.0)), float(acc), Jsonb(eq_json), Jsonb(tr_json)))
                conn.commit()

                ticker_out.append({
                    "ticker": ticker, "xgb_accuracy": round(float(acc), 4),
                    "metrics": metrics_dict(m),
                    "equity_curve": eq_json, "trades": tr_json})
            except Exception as e:
                print(f"Error {ticker}: {e}")

        # Portfolio aggregate
        port_out = {}
        if not portfolio_df.empty:
            portfolio_df.ffill(inplace=True)
            portfolio_df.fillna(req.capital, inplace=True)
            port_eq = portfolio_df.sum(axis=1)
            pm = strategy.calculate_metrics(port_eq)
            peq_json = serialize_equity(port_eq)
            cur.execute(
                "INSERT INTO portfolio_results "
                "(run_id,total_return,cagr,volatility,sharpe,sortino,max_dd,calmar,equity_curve) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (run_id, float(pm["total_return"]), float(pm["cagr"]),
                 float(pm["volatility"]), float(pm["sharpe"]), float(pm["sortino"]),
                 float(pm["max_dd"]), float(pm["calmar"]), Jsonb(peq_json)))
            conn.commit()
            port_out = {"metrics": metrics_dict(pm), "equity_curve": peq_json}

        cur.execute("UPDATE backtest_runs SET status='completed' WHERE id=%s", (run_id,))
        conn.commit()

        return {"id": run_id, "status": "completed", "tickers": req.tickers,
                "ticker_results": ticker_out, "portfolio": port_out}

    except Exception as e:
        cur.execute("UPDATE backtest_runs SET status='failed' WHERE id=%s", (run_id,))
        conn.commit()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.get("/api/runs")
def list_runs():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id,tickers,start_date,end_date,capital_per_ticker,status,created_at "
                "FROM backtest_runs ORDER BY created_at DESC LIMIT 20")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/runs/{run_id}")
def get_run(run_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM backtest_runs WHERE id=%s", (run_id,))
    run = cur.fetchone()
    if not run:
        cur.close()
        conn.close()
        raise HTTPException(404, "Run not found")

    cur.execute("SELECT * FROM ticker_results WHERE run_id=%s", (run_id,))
    tickers = cur.fetchall()
    cur.execute("SELECT * FROM portfolio_results WHERE run_id=%s", (run_id,))
    portfolio = cur.fetchone()
    cur.close()
    conn.close()

    return {
        "id": run["id"], "status": run["status"],
        "tickers": run["tickers"].split(","),
        "start_date": run["start_date"], "end_date": run["end_date"],
        "capital_per_ticker": run["capital_per_ticker"],
        "ticker_results": [
            {"ticker": t["ticker"], "xgb_accuracy": t["xgb_accuracy"],
             "metrics": {
                 "total_return": t["total_return"], "cagr": t["cagr"],
                 "volatility": t["volatility"], "sharpe": t["sharpe"],
                 "sortino": t["sortino"], "max_dd": t["max_dd"],
                 "calmar": t["calmar"], "total_trades": t["total_trades"],
                 "win_rate": t["win_rate"], "avg_win": t["avg_win"],
                 "avg_loss": t["avg_loss"], "profit_factor": t["profit_factor"],
                 "expectancy": t["expectancy"], "trade_sharpe": t["trade_sharpe"]},
             "equity_curve": t["equity_curve"], "trades": t["trades"]}
            for t in tickers],
        "portfolio": {
            "metrics": {
                "total_return": portfolio["total_return"], "cagr": portfolio["cagr"],
                "volatility": portfolio["volatility"], "sharpe": portfolio["sharpe"],
                "sortino": portfolio["sortino"], "max_dd": portfolio["max_dd"],
                "calmar": portfolio["calmar"]} if portfolio else {},
            "equity_curve": portfolio["equity_curve"] if portfolio else []}}


@app.get("/api/latest")
def get_latest():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM backtest_runs WHERE status='completed' ORDER BY created_at DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return {"id": None, "status": "no_runs"}
    return get_run(row["id"])
