#!/usr/bin/env python3
"""
Example: Start Real-Time Trading

This script demonstrates how to start the Aether-1 real-time trading engine.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PARENT_DIR, "backend"))

from realtime_engine import RealtimeTradingEngine

load_dotenv(os.path.join(PARENT_DIR, ".env"))


async def main():
    """Run the trading engine."""
    
    # Configuration
    DB_URL = os.getenv("DB_URL")
    if not DB_URL:
        print("Error: DB_URL not set in .env")
        sys.exit(1)
    
    TICKERS = ["SPY", "QQQ", "IWM"]  # Stocks to trade
    INITIAL_CAPITAL = 100000.0  # Starting capital
    UPDATE_INTERVAL = 3600  # Update every hour (3600 seconds)
    
    print("=" * 60)
    print("Aether-1 Real-Time Trading Engine")
    print("=" * 60)
    print(f"Trading Tickers: {', '.join(TICKERS)}")
    print(f"Initial Capital: ${INITIAL_CAPITAL:,.2f}")
    print(f"Update Interval: {UPDATE_INTERVAL}s ({UPDATE_INTERVAL/3600:.1f}h)")
    print("=" * 60)
    print()
    
    # Create engine
    engine = RealtimeTradingEngine(DB_URL, TICKERS, INITIAL_CAPITAL)
    
    # Run engine
    try:
        await engine.run(interval_seconds=UPDATE_INTERVAL)
    except KeyboardInterrupt:
        print("\n\nStopping trading engine...")
        engine.stop()
        print("Trading engine stopped")


if __name__ == "__main__":
    asyncio.run(main())
