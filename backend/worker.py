"""
Persistent Trading Worker
Monitors the database for active trading sessions and executes cycles.
"""

import sys
import os
import time
import asyncio
import psycopg
from datetime import datetime, timedelta
from psycopg.rows import dict_row
from dotenv import load_dotenv

# Add parent directory to path to import engine and strategy
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)

from realtime_engine import RealtimeTradingEngine

load_dotenv(os.path.join(PARENT_DIR, ".env"))
DB_URL = os.getenv("DB_URL")

def get_active_configs():
    """Fetch active agent configurations from database."""
    conn = psycopg.connect(DB_URL, row_factory=dict_row)
    cur = conn.cursor()
    cur.execute("SELECT * FROM agent_config WHERE is_active = TRUE")
    configs = cur.fetchall()
    cur.close()
    conn.close()
    return configs

def update_last_run(config_id: int):
    """Update last_run_at timestamp for a config."""
    conn = psycopg.connect(DB_URL, row_factory=dict_row)
    cur = conn.cursor()
    cur.execute(
        "UPDATE agent_config SET last_run_at = %s WHERE id = %s",
        (datetime.now(), config_id)
    )
    conn.commit()
    cur.close()
    conn.close()

async def run_worker():
    """Main worker loop."""
    print(f"[{datetime.now()}] Aether-1 Trading Worker started")
    print(f"Connecting to: {DB_URL.split('@')[-1]}") # Log host only for safety

    while True:
        try:
            configs = get_active_configs()
            
            for config in configs:
                session_id = config["session_id"]
                interval = config["interval_seconds"]
                last_run = config["last_run_at"]
                
                # Check if it's time to run
                should_run = False
                if last_run is None:
                    should_run = True
                else:
                    elapsed = (datetime.now() - last_run).total_seconds()
                    if elapsed >= interval:
                        should_run = True
                
                if should_run:
                    print(f"\n[{datetime.now()}] Running cycle for Session {session_id}...")
                    
                    # Initialize engine and load session
                    engine = RealtimeTradingEngine(DB_URL, [], 0) # Tickers/capital reloaded from DB
                    if engine.load_session(session_id):
                        try:
                            engine.run_single_cycle()
                            update_last_run(config["id"])
                        except Exception as e:
                            print(f"Error executing cycle for session {session_id}: {e}")
                    else:
                        print(f"Failed to load session {session_id}")
            
        except Exception as e:
            print(f"Worker Error: {e}")
        
        # Sleep before checking for new configs (e.g., 10 seconds)
        await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("Worker stopped by user")
