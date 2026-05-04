# 30-Day Continuous Trading Mode

## Overview

The **30-Day Continuous Trading Mode** starts an autonomous trading agent that runs for 30 days without stopping, even if you close the browser or disconnect from the API. The agent:

- ✅ Runs continuously for 30 days (720 hourly cycles)
- ✅ Updates every 1 hour automatically
- ✅ Executes trades 24/7
- ✅ Persists all trades to database
- ✅ Continues even if browser closes
- ✅ Can be monitored/stopped at any time

## Starting the 30-Day Agent

### Via CLI (Command Line)

```bash
# Start with default settings
python trading_client.py start-30days

# Start with custom tickers and capital
python trading_client.py start-30days --tickers AAPL MSFT GOOGL --capital 500000
```

### Via API

```bash
curl -X POST http://localhost:8000/api/trading/start-30days \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["SPY", "QQQ", "IWM"],
    "initial_capital": 100000
  }'
```

Response:
```json
{
  "status": "started",
  "mode": "30-day-continuous",
  "tickers": ["SPY", "QQQ", "IWM"],
  "initial_capital": 100000,
  "duration_days": 30,
  "message": "Trading will continue for 30 days even if browser closes"
}
```

### Via Frontend (React)

```javascript
// Start 30-day agent
const response = await fetch('/api/trading/start-30days', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    tickers: ['SPY', 'QQQ', 'IWM'],
    initial_capital: 100000
  })
});

const result = await response.json();
console.log(`Trading started! Session: ${result.status}`);
```

## Monitoring the 30-Day Agent

### Check Status (CLI)

```bash
python trading_client.py 30days-status
```

Output:
```
🔴 30-Day Agent: RUNNING
Session ID: 42
Tickers: SPY, QQQ, IWM
Started: 2026-05-04T10:00:00
Equity: $102,500.00
Cash: $52,500.00
Positions: 1
Return: 2.50%
Trades: 5
Win Rate: 60.0%
Last Update: 2026-05-04T11:05:32
```

### Check Status (API)

```bash
curl http://localhost:8000/api/trading/30days-status
```

Response:
```json
{
  "running": true,
  "session_id": 42,
  "tickers": ["SPY", "QQQ", "IWM"],
  "status": "active",
  "created_at": "2026-05-04T10:00:00",
  "equity": 102500.0,
  "cash": 52500.0,
  "positions_count": 1,
  "metrics": {
    "total_return": 2500.0,
    "return_pct": 2.50,
    "total_trades": 5,
    "winning_trades": 3,
    "win_rate": 60.0
  },
  "last_update": "2026-05-04T11:05:32"
}
```

### Get Trade Log (CLI)

```bash
# Get recent 50 trades
python trading_client.py 30days-log --limit 50

# Get more trades
python trading_client.py 30days-log --limit 200
```

Output:
```
30-Day Agent Trade Log (Session 42):
Total trades shown: 50
────────────────────────────────────────────────────────────────────────────────
Timestamp            │ Ticker     │ Type       │ Price        │ Shares       │ Confidence
────────────────────────────────────────────────────────────────────────────────
2026-05-04T11:05:32  │ SPY        │ OPEN       │ $500.00      │ 50.00        │ 0.6234
2026-05-04T10:05:15  │ QQQ        │ CLOSE      │ $350.00      │ 75.00        │ 0.3821
2026-05-04T09:00:45  │ IWM        │ OPEN       │ $200.00      │ 100.00       │ 0.5890
────────────────────────────────────────────────────────────────────────────────
```

### Get Trade Log (API)

```bash
# Get last 50 trades
curl http://localhost:8000/api/trading/30days-log?limit=50

# Get last 200 trades
curl http://localhost:8000/api/trading/30days-log?limit=200
```

## Stopping the 30-Day Agent

### Via CLI

```bash
python trading_client.py stop-30days
```

Output:
```
✓ 30-Day agent stopped
  Session ID: 42
```

### Via API

```bash
curl -X POST http://localhost:8000/api/trading/stop-30days
```

Response:
```json
{
  "status": "stopped",
  "session_id": 42,
  "message": "30-day agent has been stopped"
}
```

## How It Works

### Execution Flow

1. **Start**: User clicks "Start 30-Day Trading" button
2. **Session Creation**: Database session created (e.g., session_id = 42)
3. **Background Task**: Trading engine starts in background
4. **Continuous Loop**: For 30 days, every hour:
   - Fetch latest market data
   - Generate trading signals
   - Execute trades based on signals
   - Save portfolio snapshot
   - Wait 1 hour
5. **Browser Closed**: Agent continues running (background process)
6. **Status Polling**: Frontend/CLI can query progress anytime
7. **Manual Stop**: User can stop at any time
8. **Auto-Completion**: Automatically stops after 30 days

### Key Differences from Regular Trading

| Aspect | Regular Trading | 30-Day Mode |
|--------|-----------------|-----------|
| Duration | User controls | Automatic 30 days |
| Background | Stops if API stops | Continues in background |
| Browser | Depends on API connection | Independent of browser |
| Monitoring | Real-time polling | Queryable anytime |
| Default Interval | Configurable | Fixed 1 hour |
| Stopping | Manual only | Automatic after 30 days or manual stop |

## Frontend Integration Example

### React Component

```javascript
import React, { useState, useEffect } from 'react';

export function TradingPanel() {
  const [agent, setAgent] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  // Start 30-day agent
  const handleStart30Days = async () => {
    try {
      const response = await fetch('/api/trading/start-30days', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tickers: ['SPY', 'QQQ', 'IWM'],
          initial_capital: 100000
        })
      });
      const data = await response.json();
      setAgent(data);
      setIsMonitoring(true);
    } catch (error) {
      console.error('Failed to start 30-day agent:', error);
    }
  };

  // Check status periodically
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(async () => {
      try {
        const response = await fetch('/api/trading/30days-status');
        const status = await response.json();
        setAgent(status);
        
        // Stop monitoring if agent stopped
        if (!status.running) {
          setIsMonitoring(false);
        }
      } catch (error) {
        console.error('Failed to fetch status:', error);
      }
    }, 60000); // Check every minute

    return () => clearInterval(interval);
  }, [isMonitoring]);

  // Stop agent
  const handleStop30Days = async () => {
    try {
      await fetch('/api/trading/stop-30days', { method: 'POST' });
      setIsMonitoring(false);
    } catch (error) {
      console.error('Failed to stop agent:', error);
    }
  };

  return (
    <div className="trading-panel">
      <h2>30-Day Trading Agent</h2>
      
      {!isMonitoring ? (
        <button onClick={handleStart30Days} className="btn btn-primary">
          🚀 Start 30-Day Trading
        </button>
      ) : (
        <div>
          <div className="status">
            <p>🔴 RUNNING</p>
            <p>Session ID: {agent?.session_id}</p>
            <p>Equity: ${agent?.equity?.toFixed(2)}</p>
            <p>Return: {agent?.metrics?.return_pct?.toFixed(2)}%</p>
            <p>Trades: {agent?.metrics?.total_trades}</p>
          </div>
          <button onClick={handleStop30Days} className="btn btn-danger">
            ⏹️ Stop Agent
          </button>
        </div>
      )}
    </div>
  );
}
```

## Database Queries

### Check if Agent is Running

```sql
SELECT * FROM realtime_sessions 
WHERE status = 'active' 
ORDER BY created_at DESC 
LIMIT 1;
```

### Get All 30-Day Sessions

```sql
SELECT id, tickers, created_at, final_equity, total_trades, total_return
FROM realtime_sessions 
WHERE DATE(created_at) >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY created_at DESC;
```

### Get Real-Time Metrics

```sql
SELECT equity, cash, metrics, timestamp
FROM realtime_snapshots 
WHERE session_id = 42
ORDER BY timestamp DESC 
LIMIT 10;
```

### Calculate Session Performance

```sql
SELECT 
  rs.id,
  rs.tickers,
  rs.capital,
  rs.final_equity,
  (rs.final_equity - rs.capital) as total_return,
  ((rs.final_equity - rs.capital) / rs.capital * 100) as return_pct,
  rs.total_trades,
  DATE_PART('day', rs.created_at) as duration_days
FROM realtime_sessions rs
WHERE rs.status = 'closed'
ORDER BY ((rs.final_equity - rs.capital) / rs.capital) DESC;
```

## Common Scenarios

### Scenario 1: Start Trading, Close Browser

1. User starts 30-day agent via frontend
2. Agent session created in database
3. User closes browser tab
4. ✅ Agent continues trading in background
5. User can re-open frontend and query status anytime

### Scenario 2: Monitor While Trading

1. 30-day agent running
2. User periodically checks `/api/trading/30days-status`
3. Status shows live equity, trades, positions
4. User can see trade log with `/api/trading/30days-log`

### Scenario 3: Stop Before 30 Days

1. 30-day agent running (e.g., day 15)
2. User calls `/api/trading/stop-30days`
3. Agent stops immediately
4. Session saved to database with final equity
5. Can view final results

### Scenario 4: Restart After Crash

1. Backend crashes mid-trading
2. Agent stops automatically
3. User restarts backend
4. Can query old session: `/api/trading/sessions/{id}`
5. Can start new 30-day agent

## Performance Considerations

- **CPU**: Low (idle between cycles)
- **Memory**: ~50-100MB
- **Network**: Only 1 data fetch per hour
- **Database**: ~100 rows per cycle
- **Duration**: 30 days of continuous operation

## Troubleshooting

### Agent not starting
```
Check:
1. DB_URL is valid in .env
2. PostgreSQL is running
3. Backend is running
4. Check logs for errors
```

### Status shows "NOT RUNNING"
```
Check:
1. Was the start request successful?
2. Check backend logs for errors
3. Verify database connection
```

### No new trades appearing
```
Check:
1. Tickers have sufficient data
2. Signal generation working
3. Portfolio has sufficient cash
4. Check confidence thresholds
```

### Need to view past sessions
```
Use:
python trading_client.py history --limit 50
or
/api/trading/history?limit=50
```

---

**30-Day Mode Version 1.0** | Autonomous Trading System
