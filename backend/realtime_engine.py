"""
Real-Time Trading Engine
Executes live trading with continuous signal generation and position management.
"""

import sys
import os
import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
import yfinance as yf
from collections import deque
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)
import strategy


class RealtimePortfolio:
    """Tracks real-time positions, equity, and trades."""
    
    def __init__(self, db_url: str, initial_capital: float = 100000.0):
        self.db_url = db_url
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, dict] = {}  # ticker -> {shares, entry_price, entry_date, current_price}
        self.trade_history: List[dict] = []
        self.equity_history: deque = deque(maxlen=10000)
        self.price_cache: Dict[str, float] = {}
        self.signal_cache: Dict[str, dict] = {}
        self.last_update = datetime.now()
        self._lock = threading.Lock()
        
    def load_from_snapshot(self, snapshot: dict):
        """Restore portfolio state from a database snapshot."""
        with self._lock:
            self.cash = float(snapshot.get("cash", self.initial_capital))
            self.positions = {}
            
            positions_data = snapshot.get("positions", {})
            for ticker, pos in positions_data.items():
                self.positions[ticker] = {
                    "shares": float(pos["shares"]),
                    "entry_price": float(pos["entry_price"]),
                    "entry_date": datetime.fromisoformat(pos["entry_date"]),
                    "current_price": float(pos["current_price"]),
                    "signal_confidence": float(pos.get("signal_confidence", 0.5)),
                    "status": "open"
                }
            
            self.last_update = datetime.now()
        
    def get_equity(self) -> float:
        """Calculate current portfolio equity."""
        with self._lock:
            equity = self.cash
            for ticker, pos in self.positions.items():
                if ticker in self.price_cache:
                    equity += pos["shares"] * self.price_cache[ticker]
            return equity
    
    def get_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        equity = self.get_equity()
        return equity - self.initial_capital
    
    def get_return_pct(self) -> float:
        """Calculate return percentage."""
        equity = self.get_equity()
        if self.initial_capital == 0:
            return 0.0
        return ((equity - self.initial_capital) / self.initial_capital) * 100
    
    def open_position(self, ticker: str, shares: float, price: float, signal_confidence: float) -> bool:
        """Open a long position."""
        with self._lock:
            cost = shares * price
            if cost > self.cash:
                return False
            
            self.cash -= cost
            if ticker not in self.positions:
                self.positions[ticker] = {
                    "shares": shares,
                    "entry_price": price,
                    "entry_date": datetime.now(),
                    "current_price": price,
                    "signal_confidence": signal_confidence,
                    "status": "open"
                }
            else:
                self.positions[ticker]["shares"] += shares
            
            return True
    
    def close_position(self, ticker: str, price: float, exit_reason: str = "signal") -> Optional[dict]:
        """Close a position and record trade."""
        with self._lock:
            if ticker not in self.positions:
                return None
            
            pos = self.positions[ticker]
            shares = pos["shares"]
            entry_price = pos["entry_price"]
            entry_date = pos["entry_date"]
            
            if shares <= 0:
                return None
            
            proceeds = shares * price
            cost = shares * entry_price
            pnl = proceeds - cost
            pnl_pct = (pnl / cost) * 100 if cost != 0 else 0
            
            self.cash += proceeds
            
            trade = {
                "ticker": ticker,
                "entry_date": entry_date,
                "exit_date": datetime.now(),
                "entry_price": entry_price,
                "exit_price": price,
                "shares": shares,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "exit_reason": exit_reason
            }
            
            self.trade_history.append(trade)
            del self.positions[ticker]
            
            return trade
    
    def update_prices(self, price_data: Dict[str, float]):
        """Update current prices for all positions."""
        with self._lock:
            self.price_cache.update(price_data)
            for ticker in self.positions:
                if ticker in price_data:
                    self.positions[ticker]["current_price"] = price_data[ticker]
            
            equity = self.get_equity()
            self.equity_history.append({
                "timestamp": datetime.now(),
                "equity": equity,
                "cash": self.cash,
                "positions_count": len(self.positions)
            })
            self.last_update = datetime.now()
    
    def get_position(self, ticker: str) -> Optional[dict]:
        """Get position details."""
        with self._lock:
            return self.positions.get(ticker)
    
    def get_all_positions(self) -> Dict[str, dict]:
        """Get all open positions."""
        with self._lock:
            return dict(self.positions)
    
    def get_metrics(self) -> dict:
        """Calculate performance metrics."""
        with self._lock:
            equity = self.get_equity()
            total_return = equity - self.initial_capital
            return_pct = (total_return / self.initial_capital) * 100 if self.initial_capital > 0 else 0
            
            if len(self.trade_history) == 0:
                return {
                    "total_return": total_return,
                    "return_pct": return_pct,
                    "equity": equity,
                    "cash": self.cash,
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "avg_win": 0.0,
                    "avg_loss": 0.0,
                    "profit_factor": 0.0,
                    "max_dd": 0.0
                }
            
            wins = [t["pnl"] for t in self.trade_history if t["pnl"] > 0]
            losses = [t["pnl"] for t in self.trade_history if t["pnl"] < 0]
            total_wins = sum(wins) if wins else 0
            total_losses = abs(sum(losses)) if losses else 0
            
            return {
                "total_return": total_return,
                "return_pct": return_pct,
                "equity": equity,
                "cash": self.cash,
                "total_trades": len(self.trade_history),
                "winning_trades": len(wins),
                "losing_trades": len(losses),
                "win_rate": (len(wins) / len(self.trade_history)) * 100 if len(self.trade_history) > 0 else 0,
                "avg_win": np.mean(wins) if wins else 0,
                "avg_loss": np.mean(losses) if losses else 0,
                "profit_factor": total_wins / total_losses if total_losses > 0 else 0,
                "max_dd": self._calculate_max_dd()
            }
    
    def _calculate_max_dd(self) -> float:
        """Calculate maximum drawdown."""
        if len(self.equity_history) < 2:
            return 0.0
        
        peak = self.initial_capital
        max_dd = 0.0
        
        for entry in self.equity_history:
            if entry["equity"] > peak:
                peak = entry["equity"]
            dd = (peak - entry["equity"]) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
        
        return max_dd


class RealtimeTradingEngine:
    """Main real-time trading engine."""
    
    def __init__(self, db_url: str, tickers: List[str], initial_capital: float = 100000.0):
        self.db_url = db_url
        self.tickers = tickers
        self.portfolio = RealtimePortfolio(db_url, initial_capital)
        self.running = False
        self.session_id = None
        self.session_start = datetime.now()
        self.is_market_open = True
        
    def start_session(self) -> int:
        """Start a new trading session."""
        conn = psycopg.connect(self.db_url, row_factory=dict_row)
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO realtime_sessions (tickers, status, capital, created_at) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (",".join(self.tickers), "active", self.portfolio.initial_capital, datetime.now())
        )
        self.session_id = cur.fetchone()["id"]
        conn.commit()
        cur.close()
        conn.close()
        
        return self.session_id
    
    def load_session(self, session_id: int):
        """Load an existing trading session from the database."""
        self.session_id = session_id
        
        try:
            conn = psycopg.connect(self.db_url, row_factory=dict_row)
            cur = conn.cursor()
            
            # Get session info
            cur.execute("SELECT * FROM realtime_sessions WHERE id=%s", (session_id,))
            session = cur.fetchone()
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            self.tickers = session["tickers"].split(",")
            self.portfolio.initial_capital = float(session["capital"])
            
            # Get latest snapshot
            cur.execute(
                "SELECT * FROM realtime_snapshots WHERE session_id=%s ORDER BY timestamp DESC LIMIT 1",
                (session_id,)
            )
            snapshot = cur.fetchone()
            if snapshot:
                self.portfolio.load_from_snapshot(snapshot)
            
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return False
    
    def end_session(self):
        """End the trading session."""
        if not self.session_id:
            return
        
        conn = psycopg.connect(self.db_url, row_factory=dict_row)
        cur = conn.cursor()
        
        metrics = self.portfolio.get_metrics()
        cur.execute(
            "UPDATE realtime_sessions SET status='closed', final_equity=%s, "
            "total_trades=%s, total_return=%s WHERE id=%s",
            (metrics["equity"], metrics["total_trades"], metrics["total_return"], self.session_id)
        )
        conn.commit()
        cur.close()
        conn.close()
    
    def fetch_live_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch latest market data for all tickers."""
        data = {}
        for ticker in self.tickers:
            try:
                # Fetch 1 year of data for feature engineering
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                df = yf.download(ticker, start=start_date, end=end_date, interval="1d", auto_adjust=True)
                if len(df) > 0:
                    data[ticker] = df
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
        
        return data
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, dict]:
        """Generate trading signals for all tickers."""
        signals = {}
        
        for ticker, df in data.items():
            try:
                if len(df) < 252:
                    continue
                
                # Engineer features
                df_ml = strategy.engineer_features(df)
                
                # Get latest features
                latest = df_ml.iloc[-1]
                current_price = df["Close"].iloc[-1]
                
                # Simple signal logic (can be enhanced)
                # Use features to generate confidence score
                features = {
                    "rsi": latest.get("rsi", 50),
                    "momentum": latest.get("momentum", 0),
                    "ma_dist": latest.get("ma_dist", 0),
                    "feat_vol": latest.get("feat_vol", 0)
                }
                
                # Calculate signal confidence (0-1)
                confidence = self._calculate_confidence(features)
                
                signal_type = "BUY" if confidence > 0.55 else ("SELL" if confidence < 0.45 else "HOLD")
                
                signals[ticker] = {
                    "signal": signal_type,
                    "confidence": confidence,
                    "price": float(current_price),
                    "features": {k: float(v) for k, v in features.items()},
                    "timestamp": datetime.now()
                }
                
            except Exception as e:
                print(f"Error generating signal for {ticker}: {e}")
                signals[ticker] = {"signal": "HOLD", "confidence": 0.5, "price": 0, "error": str(e)}
        
        return signals
    
    def _calculate_confidence(self, features: dict) -> float:
        """Calculate trading confidence from features."""
        score = 0.5  # Start at 50% neutral
        
        # RSI contribution
        rsi = features.get("rsi", 50)
        if rsi < 30:
            score += 0.15  # Oversold, bullish
        elif rsi > 70:
            score -= 0.15  # Overbought, bearish
        
        # Momentum contribution
        momentum = features.get("momentum", 0)
        if momentum > 0.01:
            score += 0.1
        elif momentum < -0.01:
            score -= 0.1
        
        # MA distance contribution
        ma_dist = features.get("ma_dist", 0)
        if -0.05 < ma_dist < 0.05:
            score += 0.05  # Close to MA, healthy
        
        return np.clip(score, 0.0, 1.0)
    
    def execute_trades(self, signals: Dict[str, dict]):
        """Execute trades based on signals."""
        current_prices = {ticker: sig["price"] for ticker, sig in signals.items()}
        self.portfolio.update_prices(current_prices)
        
        for ticker, sig in signals.items():
            if sig["signal"] == "HOLD" or "error" in sig:
                continue
            
            pos = self.portfolio.get_position(ticker)
            price = sig["price"]
            confidence = sig["confidence"]
            
            # Position sizing based on confidence and volatility
            position_size = self._calculate_position_size(confidence, price)
            
            if sig["signal"] == "BUY" and not pos:
                # Open position
                self.portfolio.open_position(ticker, position_size, price, confidence)
                self._record_trade_event("OPEN", ticker, price, position_size, confidence)
                
            elif sig["signal"] == "SELL" and pos and pos["shares"] > 0:
                # Close position
                trade = self.portfolio.close_position(ticker, price, "signal")
                if trade:
                    self._record_trade_event("CLOSE", ticker, price, pos["shares"], confidence)
    
    def _calculate_position_size(self, confidence: float, price: float) -> float:
        """Calculate position size based on confidence and risk management."""
        # Risk 2% of portfolio per trade
        portfolio_value = self.portfolio.get_equity()
        risk_amount = portfolio_value * 0.02
        
        # Position size scales with confidence
        base_shares = risk_amount / price if price > 0 else 0
        size = base_shares * confidence
        
        return max(1.0, size)
    
    def _record_trade_event(self, event_type: str, ticker: str, price: float, shares: float, confidence: float):
        """Record trade event in database."""
        if not self.session_id:
            return
        
        try:
            conn = psycopg.connect(self.db_url, row_factory=dict_row)
            cur = conn.cursor()
            
            cur.execute(
                "INSERT INTO realtime_trades (session_id, ticker, event_type, price, shares, confidence, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (self.session_id, ticker, event_type, price, shares, confidence, datetime.now())
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error recording trade event: {e}")
    
    def save_snapshot(self):
        """Save portfolio snapshot to database."""
        if not self.session_id:
            return
        
        try:
            conn = psycopg.connect(self.db_url, row_factory=dict_row)
            cur = conn.cursor()
            
            metrics = self.portfolio.get_metrics()
            positions = self.portfolio.get_all_positions()
            
            # Convert positions to JSON-serializable format
            positions_json = {}
            for ticker, pos in positions.items():
                positions_json[ticker] = {
                    "shares": pos["shares"],
                    "entry_price": float(pos["entry_price"]),
                    "current_price": float(pos["current_price"]),
                    "entry_date": pos["entry_date"].isoformat(),
                    "unrealized_pnl": float((pos["current_price"] - pos["entry_price"]) * pos["shares"])
                }
            
            cur.execute(
                "INSERT INTO realtime_snapshots (session_id, equity, cash, positions, metrics, timestamp) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    self.session_id,
                    metrics["equity"],
                    self.portfolio.cash,
                    Jsonb(positions_json),
                    Jsonb({k: float(v) if isinstance(v, (int, float, np.number)) else v for k, v in metrics.items()}),
                    datetime.now()
                )
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error saving snapshot: {e}")
    
    async def run(self, interval_seconds: int = 3600):
        """Run the trading engine."""
        self.running = True
        self.start_session()
        
        try:
            while self.running:
                try:
                    print(f"[{datetime.now()}] Fetching live data...")
                    data = self.fetch_live_data()
                    
                    print(f"[{datetime.now()}] Generating signals...")
                    signals = self.generate_signals(data)
                    
                    print(f"[{datetime.now()}] Executing trades...")
                    self.execute_trades(signals)
                    
                    print(f"[{datetime.now()}] Saving snapshot...")
                    self.save_snapshot()
                    
                    # Print current status
                    metrics = self.portfolio.get_metrics()
                    print(f"Portfolio Equity: ${metrics['equity']:.2f} | "
                          f"Return: {metrics['return_pct']:.2f}% | "
                          f"Trades: {metrics['total_trades']} | "
                          f"Positions: {len(self.portfolio.get_all_positions())}")
                    
                except Exception as e:
                    print(f"Error in trading cycle: {e}")
                
                # Wait before next cycle
                print(f"Sleeping for {interval_seconds} seconds...")
                await asyncio.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("Trading engine stopped by user")
        finally:
            self.running = False
            self.end_session()
    
    def run_single_cycle(self):
        """Execute one complete trading cycle (fetch -> signals -> trades -> snapshot)."""
        if not self.session_id:
            raise ValueError("No session ID loaded")
            
        try:
            print(f"[{datetime.now()}] Fetching live data...")
            data = self.fetch_live_data()
            
            print(f"[{datetime.now()}] Generating signals...")
            signals = self.generate_signals(data)
            
            print(f"[{datetime.now()}] Executing trades...")
            self.execute_trades(signals)
            
            print(f"[{datetime.now()}] Saving snapshot...")
            self.save_snapshot()
            
            metrics = self.portfolio.get_metrics()
            print(f"✓ Cycle complete: Equity ${metrics['equity']:.2f} | Return {metrics['return_pct']:.2f}%")
            return metrics
        except Exception as e:
            print(f"✗ Error in trading cycle: {e}")
            raise e
    
    def stop(self):
        """Stop the trading engine."""
        self.running = False
