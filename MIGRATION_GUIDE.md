# Migration: Backtest → Real-Time Trading

## Summary of Changes

The Aether-1 system has been converted from a historical backtesting engine to a **real-time trading system** with continuous signal generation, live position management, and real-time performance tracking.

## What Changed

### 1. Backend Architecture

#### Before (Backtesting)
- One-time backtests on historical data
- Results stored after completion
- No continuous monitoring
- Manual interval-based runs (30-day cycles)

#### After (Real-Time)
- Continuous trading loop
- Live data fetching at configured intervals
- Real-time position tracking
- Signal generation every cycle
- Immediate trade execution and recording

### 2. New Files Created

#### `backend/realtime_engine.py`
Core real-time trading engine with:
- `RealtimePortfolio`: Tracks positions, equity, trades
- `RealtimeTradingEngine`: Main orchestrator
  - Live data fetching
  - Signal generation
  - Trade execution
  - Database persistence

**Key Classes:**
```python
class RealtimePortfolio:
    - get_equity()
    - open_position()
    - close_position()
    - update_prices()
    - get_metrics()

class RealtimeTradingEngine:
    - start_session()
    - fetch_live_data()
    - generate_signals()
    - execute_trades()
    - run()  # Main loop
```

#### `backend/trading_client.py`
Command-line client for easy management:
```bash
python trading_client.py start --tickers SPY QQQ --capital 100000
python trading_client.py monitor --interval 30
python trading_client.py stop
python trading_client.py status
```

#### `backend/example_trading.py`
Simple example showing how to start trading programmatically

### 3. Updated Files

#### `backend/main.py`
- **Removed**: Old backtest endpoints
- **Removed**: `run_backtest()`, `list_runs()`, `get_run()`, `get_latest()`
- **Removed**: Helper functions (serialize_equity, serialize_trades, metrics_dict)
- **Added**: Real-time trading endpoints
- **Added**: Global trading engine state management
- **Added**: Database schema initialization

**New Endpoints:**
```
POST  /api/trading/start              → Start trading session
POST  /api/trading/stop               → Stop current session
GET   /api/trading/status             → Current status + positions
GET   /api/trading/sessions/{id}      → Session details
GET   /api/trading/trades/{id}        → Trade history
GET   /api/trading/positions/{id}     → Current positions
GET   /api/trading/history            → Recent sessions
```

#### `backend/requirements.txt`
- Changed: `psycopg2-binary` → `psycopg` (modern async driver)
- Added: `websockets` (for future WebSocket support)
- Added: `aiohttp` (for async HTTP requests)

### 4. New Database Tables

```sql
CREATE TABLE realtime_sessions (
    id SERIAL PRIMARY KEY,
    tickers TEXT,
    status VARCHAR(20),
    capital NUMERIC(15,2),
    created_at TIMESTAMP,
    final_equity NUMERIC(15,2),
    total_trades INT,
    total_return NUMERIC(15,4)
);

CREATE TABLE realtime_trades (
    id SERIAL PRIMARY KEY,
    session_id INT,
    ticker VARCHAR(10),
    event_type VARCHAR(20),  -- OPEN or CLOSE
    price NUMERIC(15,4),
    shares NUMERIC(15,4),
    confidence NUMERIC(5,4),
    timestamp TIMESTAMP
);

CREATE TABLE realtime_snapshots (
    id SERIAL PRIMARY KEY,
    session_id INT,
    equity NUMERIC(15,2),
    cash NUMERIC(15,2),
    positions JSONB,        -- Open positions
    metrics JSONB,          -- Performance metrics
    timestamp TIMESTAMP
);
```

## How to Use

### Quick Start

1. **Start Backend**
```bash
cd backend
python -m uvicorn main:app --reload
```

2. **Start Trading** (via CLI)
```bash
python trading_client.py start --tickers SPY QQQ IWM --capital 100000 --interval 3600
```

3. **Monitor** (via CLI)
```bash
python trading_client.py monitor --interval 30
```

4. **Stop Trading**
```bash
python trading_client.py stop
```

### Via API

**Start:**
```bash
curl -X POST http://localhost:8000/api/trading/start \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["SPY", "QQQ"],
    "initial_capital": 100000,
    "interval_seconds": 3600
  }'
```

**Check Status:**
```bash
curl http://localhost:8000/api/trading/status
```

**Stop:**
```bash
curl -X POST http://localhost:8000/api/trading/stop
```

### Via Frontend

Frontend can integrate new endpoints:
```javascript
// Start trading
const response = await fetch('/api/trading/start', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tickers: ['SPY', 'QQQ'],
    initial_capital: 100000,
    interval_seconds: 3600
  })
});

// Get status
const status = await fetch('/api/trading/status').then(r => r.json());

// Update UI with real-time data
setInterval(() => {
  fetch('/api/trading/status')
    .then(r => r.json())
    .then(data => updateDashboard(data));
}, 30000);  // Update every 30 seconds
```

## Key Features

### 1. Real-Time Signal Generation

Signals generated at each update cycle:
- **RSI-based**: Identify oversold/overbought conditions
- **Momentum-based**: Trend following
- **MA-based**: Support/resistance levels
- **Confidence scores**: 0-1 scale for position sizing

### 2. Automatic Trade Execution

When signal confidence > 55%:
- Calculate position size based on confidence
- Check available cash
- Open position
- Record trade event

When signal confidence < 45%:
- Close existing position
- Record exit trade
- Realize P&L

### 3. Live Position Tracking

Every update cycle:
- Update market prices
- Calculate unrealized P&L
- Track position metrics
- Save snapshot to database

### 4. Performance Metrics

Continuously calculated:
- **Total Return**: $ and %
- **Win Rate**: % of winning trades
- **Profit Factor**: Total Wins / Total Losses
- **Max Drawdown**: Peak-to-trough decline
- **Unrealized P&L**: Open position gains/losses

## Configuration

### Update Interval

Default: 3600 seconds (1 hour)
- Shorter = more trading activity
- Longer = fewer updates (lower costs)

```python
await engine.run(interval_seconds=300)  # 5 minutes
```

### Initial Capital

Default: $100,000

```python
engine = RealtimeTradingEngine(db_url, tickers, 100000)
```

### Tickers

Default: SPY, QQQ, IWM

```python
tickers = ["SPY", "AAPL", "MSFT", "GOOGL", "TSLA"]
```

### Risk Management

Current position sizing: 2% of portfolio per trade
- Edit `_calculate_position_size()` in realtime_engine.py
- Adjust confidence multiplier
- Add stop-loss logic

## Monitoring

### Console Output
```
[2026-05-04 10:00:00] Fetching live data...
[2026-05-04 10:00:05] Generating signals...
[2026-05-04 10:00:10] Executing trades...
[2026-05-04 10:00:15] Saving snapshot...
Portfolio Equity: $102,500.50 | Return: 2.50% | Trades: 5 | Positions: 1
```

### API Status Endpoint
```json
{
  "running": true,
  "session_id": 1,
  "equity": 102500.50,
  "positions_count": 2,
  "total_trades": 5,
  "win_rate": 60.0,
  "return_pct": 2.50,
  "max_dd": -5.5
}
```

### Database Queries
```sql
-- Latest session
SELECT * FROM realtime_sessions ORDER BY created_at DESC LIMIT 1;

-- Today's trades
SELECT * FROM realtime_trades 
WHERE session_id = 1 
ORDER BY timestamp DESC;

-- Performance history
SELECT equity, metrics FROM realtime_snapshots 
WHERE session_id = 1 
ORDER BY timestamp;
```

## Future Enhancements

- [ ] Broker API integration (live trading)
- [ ] WebSocket for real-time price updates
- [ ] Advanced risk management (stops, limits)
- [ ] Multi-timeframe analysis
- [ ] News sentiment scoring
- [ ] Options strategy support
- [ ] Portfolio correlation analysis
- [ ] ML model retraining
- [ ] Email/SMS alerts
- [ ] Dashboard visualizations

## Troubleshooting

### Trading not starting
- Check DB_URL in .env
- Verify PostgreSQL is running
- Check logs for connection errors

### No trades executing
- Verify tickers have sufficient data
- Check signal confidence thresholds
- Review portfolio cash balance

### Performance issues
- Reduce ticker count
- Increase update interval
- Check database query performance
- Monitor system resources

## Rollback to Backtesting

If you need backtesting:
1. Restore old main.py from version control
2. Run backtests manually
3. Store results in separate database

Or create a hybrid system:
- /api/trading/* for real-time
- /api/backtest/* for historical analysis

---

**Real-Time Trading Version 2.0** | May 2026
