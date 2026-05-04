#!/usr/bin/env python3
"""
Real-Time Trading Client
Command-line tool to manage and monitor Aether-1 real-time trading sessions.
"""

import requests
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any
import sys


class RealtimeTradingClient:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url.rstrip("/")
        self.session_id = None
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.api_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            return {}
    
    def health(self) -> bool:
        """Check API health."""
        result = self._request("GET", "/api/health")
        if result:
            print(f"✓ API Health: {result}")
            return True
        return False
    
    def start_trading(self, tickers: list, initial_capital: float = 100000.0, 
                     interval_seconds: int = 3600) -> bool:
        """Start real-time trading."""
        data = {
            "tickers": tickers,
            "initial_capital": initial_capital,
            "interval_seconds": interval_seconds
        }
        
        result = self._request("POST", "/api/trading/start", data)
        if result and "session_id" in result:
            self.session_id = result["session_id"]
            print(f"✓ Trading started!")
            print(f"  Session ID: {result['session_id']}")
            print(f"  Tickers: {', '.join(result['tickers'])}")
            print(f"  Initial Capital: ${result['initial_capital']:,.2f}")
            print(f"  Update Interval: {result['interval']}s")
            return True
        
        print("✗ Failed to start trading")
        return False
    
    def stop_trading(self) -> bool:
        """Stop real-time trading."""
        result = self._request("POST", "/api/trading/stop")
        if result and "status" in result:
            print(f"✓ Trading stopped")
            print(f"  Session ID: {result['session_id']}")
            return True
        
        print("✗ Failed to stop trading")
        return False
    
    def status(self) -> Dict[str, Any]:
        """Get current trading status."""
        return self._request("GET", "/api/trading/status")
    
    def print_status(self, detailed: bool = False):
        """Print trading status nicely."""
        status = self.status()
        
        if not status:
            print("✗ No trading status available")
            return
        
        running = status.get("running", False)
        running_symbol = "🔴 RUNNING" if running else "⚫ IDLE"
        
        print(f"\n{running_symbol}")
        print(f"Session ID: {status.get('session_id', 'N/A')}")
        print(f"Equity: ${status.get('equity', 0):,.2f}")
        print(f"Cash: ${status.get('cash', 0):,.2f}")
        print(f"Total Return: ${status.get('total_return', 0):,.2f} ({status.get('return_pct', 0):.2f}%)")
        print(f"Positions: {status.get('positions_count', 0)}")
        print(f"Total Trades: {status.get('total_trades', 0)}")
        print(f"Win Rate: {status.get('win_rate', 0):.1f}%")
        print(f"Max Drawdown: {status.get('max_dd', 0):.2f}%")
        print(f"Profit Factor: {status.get('profit_factor', 0):.2f}")
        
        if detailed and status.get('positions'):
            print(f"\nOpen Positions:")
            for pos in status['positions']:
                pnl = pos.get('unrealized_pnl', 0)
                pnl_pct = pos.get('unrealized_pnl_pct', 0)
                pnl_symbol = "📈" if pnl > 0 else "📉" if pnl < 0 else "➡️"
                print(f"  {pnl_symbol} {pos['ticker']}: {pos['shares']} shares @ ${pos['entry_price']:.2f}")
                print(f"     Current: ${pos['current_price']:.2f} | P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
        
        print(f"Last Update: {status.get('last_update', 'N/A')}")
    
    def monitor(self, interval: int = 30, duration: int = None):
        """Monitor trading in real-time."""
        print(f"Monitoring trading (interval: {interval}s)")
        print("Press Ctrl+C to stop\n")
        
        start_time = time.time()
        
        try:
            while True:
                self.print_status(detailed=True)
                
                if duration and (time.time() - start_time) > duration:
                    print(f"\nMonitoring duration ({duration}s) reached")
                    break
                
                print(f"\nNext update in {interval}s...")
                time.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
    
    def get_session(self, session_id: int):
        """Get session details."""
        result = self._request("GET", f"/api/trading/sessions/{session_id}")
        
        if not result:
            print(f"✗ Failed to get session {session_id}")
            return
        
        session = result.get("session", {})
        print(f"\nSession {session['id']}:")
        print(f"  Status: {session.get('status', 'N/A')}")
        print(f"  Tickers: {session.get('tickers', 'N/A')}")
        print(f"  Capital: ${session.get('capital', 0):,.2f}")
        print(f"  Created: {session.get('created_at', 'N/A')}")
        print(f"  Final Equity: ${session.get('final_equity', 'N/A')}")
        print(f"  Total Trades: {session.get('total_trades', 'N/A')}")
        print(f"  Total Return: ${session.get('total_return', 'N/A')}")
    
    def get_history(self, limit: int = 20):
        """Get session history."""
        result = self._request("GET", f"/api/trading/history?limit={limit}")
        
        if not result or "sessions" not in result:
            print("✗ Failed to get history")
            return
        
        sessions = result["sessions"]
        print(f"\nRecent Trading Sessions (last {limit}):")
        print("-" * 100)
        print(f"{'ID':<5} {'Status':<10} {'Tickers':<20} {'Capital':<15} {'Return':<15} {'Trades':<8}")
        print("-" * 100)
        
        for session in sessions:
            session_id = session.get('id', 'N/A')
            status = session.get('status', 'N/A')
            tickers = session.get('tickers', 'N/A')[:20]
            capital = f"${session.get('capital', 0):,.0f}" if session.get('capital') else 'N/A'
            total_return = session.get('total_return', 'N/A')
            if total_return != 'N/A':
                total_return = f"${total_return:,.2f}"
            trades = session.get('total_trades', 'N/A')
            
            print(f"{session_id:<5} {status:<10} {str(tickers):<20} {capital:<15} {str(total_return):<15} {str(trades):<8}")
        
        print("-" * 100)
    
    def start_30day(self, tickers: list, initial_capital: float = 100000.0) -> bool:
        """Start 30-day continuous trading agent."""
        data = {
            "tickers": tickers,
            "initial_capital": initial_capital,
            "interval_seconds": 3600
        }
        
        result = self._request("POST", "/api/trading/start-30days", data)
        if result and "status" in result:
            print(f"✓ 30-Day Trading Agent started!")
            print(f"  Tickers: {', '.join(result['tickers'])}")
            print(f"  Initial Capital: ${result['initial_capital']:,.2f}")
            print(f"  Duration: {result['duration_days']} days (720 hours)")
            print(f"  {result['message']}")
            return True
        
        print("✗ Failed to start 30-day agent")
        return False
    
    def stop_30day(self) -> bool:
        """Stop 30-day continuous trading agent."""
        result = self._request("POST", "/api/trading/stop-30days")
        if result and "status" in result:
            print(f"✓ 30-Day agent stopped")
            print(f"  Session ID: {result['session_id']}")
            return True
        
        print("✗ Failed to stop 30-day agent")
        return False
    
    def get_30day_status(self):
        """Get 30-day agent status."""
        result = self._request("GET", "/api/trading/30days-status")
        
        if not result:
            print("✗ Failed to get 30-day status")
            return
        
        if not result.get("running"):
            print("⚫ 30-Day Agent: NOT RUNNING")
            return
        
        print("🔴 30-Day Agent: RUNNING")
        print(f"Session ID: {result.get('session_id', 'N/A')}")
        print(f"Tickers: {', '.join(result.get('tickers', []))}")
        print(f"Started: {result.get('created_at', 'N/A')}")
        print(f"Equity: ${result.get('equity', 0):,.2f}")
        print(f"Cash: ${result.get('cash', 0):,.2f}")
        print(f"Positions: {result.get('positions_count', 0)}")
        
        if result.get("metrics"):
            metrics = result["metrics"]
            print(f"Return: {metrics.get('return_pct', 0):.2f}%")
            print(f"Trades: {metrics.get('total_trades', 0)}")
            print(f"Win Rate: {metrics.get('win_rate', 0):.1f}%")
        
        print(f"Last Update: {result.get('last_update', 'N/A')}")
    
    def get_30day_log(self, limit: int = 50):
        """Get 30-day agent trade log."""
        result = self._request("GET", f"/api/trading/30days-log?limit={limit}")
        
        if not result or "trades" not in result:
            print("✗ Failed to get 30-day log")
            return
        
        trades = result["trades"]
        print(f"\n30-Day Agent Trade Log (Session {result.get('session_id', 'N/A')}):")
        print(f"Total trades shown: {result.get('count', 0)}")
        print("-" * 100)
        print(f"{'Timestamp':<20} {'Ticker':<10} {'Type':<10} {'Price':<12} {'Shares':<12} {'Confidence':<12}")
        print("-" * 100)
        
        for trade in trades:
            timestamp = trade.get('timestamp', 'N/A')
            if timestamp and hasattr(timestamp, 'isoformat'):
                timestamp = timestamp.isoformat()[:19]
            
            ticker = trade.get('ticker', 'N/A')
            event_type = trade.get('event_type', 'N/A')
            price = f"${trade.get('price', 0):.2f}" if trade.get('price') else 'N/A'
            shares = f"{trade.get('shares', 0):.2f}"
            confidence = f"{trade.get('confidence', 0):.4f}"
            
            print(f"{str(timestamp):<20} {ticker:<10} {event_type:<10} {price:<12} {shares:<12} {confidence:<12}")
        
        print("-" * 100)

    parser = argparse.ArgumentParser(description="Aether-1 Real-Time Trading Client")
    parser.add_argument("--api", default="http://localhost:8000", help="API URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health check
    subparsers.add_parser("health", help="Check API health")
    
    # Start trading
    start_parser = subparsers.add_parser("start", help="Start trading")
    start_parser.add_argument("--tickers", nargs="+", default=["SPY", "QQQ", "IWM"], help="Tickers to trade")
    start_parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital")
    start_parser.add_argument("--interval", type=int, default=3600, help="Update interval in seconds")
    
    # Stop trading
    subparsers.add_parser("stop", help="Stop trading")
    
    # Status
    subparsers.add_parser("status", help="Get current status")
    
    # Monitor
    monitor_parser = subparsers.add_parser("monitor", help="Monitor trading in real-time")
    monitor_parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds")
    monitor_parser.add_argument("--duration", type=int, help="Duration in seconds (default: infinite)")
    
    # Session
    session_parser = subparsers.add_parser("session", help="Get session details")
    session_parser.add_argument("session_id", type=int, help="Session ID")
    
    # History
    history_parser = subparsers.add_parser("history", help="Get session history")
    history_parser.add_argument("--limit", type=int, default=20, help="Number of sessions to show")
    
    # 30-day agent
    start_30day_parser = subparsers.add_parser("start-30days", help="Start 30-day continuous trading")
    start_30day_parser.add_argument("--tickers", nargs="+", default=["SPY", "QQQ", "IWM"], help="Tickers to trade")
    start_30day_parser.add_argument("--capital", type=float, default=100000.0, help="Initial capital")
    
    subparsers.add_parser("stop-30days", help="Stop 30-day agent")
    subparsers.add_parser("30days-status", help="Get 30-day agent status")
    
    log_30day_parser = subparsers.add_parser("30days-log", help="Get 30-day agent trade log")
    log_30day_parser.add_argument("--limit", type=int, default=50, help="Number of trades to show")
    
    args = parser.parse_args()
    
    client = RealtimeTradingClient(args.api)
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == "health":
        client.health()
    
    elif args.command == "start":
        client.start_trading(args.tickers, args.capital, args.interval)
    
    elif args.command == "stop":
        client.stop_trading()
    
    elif args.command == "status":
        client.print_status(detailed=True)
    
    elif args.command == "monitor":
        client.monitor(args.interval, args.duration)
    
    elif args.command == "session":
        client.get_session(args.session_id)
    
    elif args.command == "history":
        client.get_history(args.limit)
    
    elif args.command == "start-30days":
        client.start_30day(args.tickers, args.capital)
    
    elif args.command == "stop-30days":
        client.stop_30day()
    
    elif args.command == "30days-status":
        client.get_30day_status()
    
    elif args.command == "30days-log":
        client.get_30day_log(args.limit)


if __name__ == "__main__":
    main()
