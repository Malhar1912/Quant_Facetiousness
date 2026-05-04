# Aether-1 Real-Time Trading - Quick Reference

## 🚀 START 30-DAY AUTONOMOUS TRADING

**Simplest Way - Start & Forget:**

```bash
python backend/trading_client.py start-30days --tickers SPY QQQ IWM --capital 100000
```

Agent will trade for 30 days **even if you close the browser!**

---

## Start Trading

**Option 1: CLI (Easiest)**
```bash
cd backend
python trading_client.py start --tickers SPY QQQ IWM --capital 100000
```

**Option 2: API**
```bash
curl -X POST http://localhost:8000/api/trading/start \
  -H "Content-Type: application/json" \
  -d '{"tickers":["SPY","QQQ"],"initial_capital":100000,"interval_seconds":3600}'
```

**Option 3: Python**
```python
import asyncio
from realtime_engine import RealtimeTradingEngine

engine = RealtimeTradingEngine(db_url, ["SPY", "QQQ"], 100000)
await engine.run(interval_seconds=3600)
```

## Monitor Trading

**CLI (Real-time)**
```bash
python trading_client.py monitor --interval 30  # Refresh every 30s
```

**API (Single Check)**
```bash
curl http://localhost:8000/api/trading/status
```

**Response:**
```json
{
  "running": true,
  "session_id": 1,
  "equity": 102500.50,
  "total_return": 2500.50,
  "return_pct": 2.50,
  "positions": [
    {
      "ticker": "SPY",
      "shares": 100,
      "entry_price": 500.0,
      "current_price": 502.50,
      "unrealized_pnl": 250.0,
      "unrealized_pnl_pct": 0.50
    }
  ],
  "total_trades": 5,
  "win_rate": 60.0,
  "max_dd": -5.5,
  "profit_factor": 2.3
}
```

## Stop Trading

```bash
python trading_client.py stop
```

## View Session History

```bash
python trading_client.py history --limit 20
```

## System Files

| File | Purpose |
|------|---------|
| `realtime_engine.py` | Core trading engine |
| `main.py` | FastAPI backend + endpoints |
| `trading_client.py` | CLI management tool |
| `example_trading.py` | Example usage |
| `REALTIME_TRADING.md` | Full documentation |
| `MIGRATION_GUIDE.md` | Migration details |
| `30_DAY_MODE.md` | 30-day autonomous trading guide |

## 🔴 30-Day Autonomous Trading Mode

### Start 30-Day Agent (Runs in Background!)

```bash
# Start: trades for 30 days even if you close the browser
python trading_client.py start-30days --tickers SPY QQQ IWM --capital 100000
```

**Output:**
```
✓ 30-Day Trading Agent started!
  Tickers: SPY, QQQ, IWM
  Initial Capital: $100,000.00
  Duration: 30 days (720 hours)
  Trading will continue for 30 days even if browser closes
```

### Monitor 30-Day Agent

```bash
# Check status (even if agent is still running)
python trading_client.py 30days-status

# View trade log
python trading_client.py 30days-log --limit 50
```

### Stop 30-Day Agent

```bash
# Stop anytime
python trading_client.py stop-30days
```

See [30_DAY_MODE.md](30_DAY_MODE.md) for complete guide.

## Key Concepts

### Update Interval
How often the system fetches data and generates signals
- Default: 3600s (1 hour)
- Smaller = more trading (more data)
- Larger = less trading (lower costs)

### Confidence Score
0-1 scale probability of signal correctness
- Affects position size
- Higher confidence = larger positions
- BUY when > 0.55, SELL when < 0.45

### Position Sizing
Risk-based position calculation:
- 2% of portfolio risked per trade
- Multiplied by confidence score
- Ensures consistent risk management

### Unrealized P&L
Open position profit/loss:
- Calculated at each update cycle
- Displayed in real-time
- Realized when position closes

## Metrics Explained

| Metric | Formula | Interpretation |
|--------|---------|-----------------|
| **Total Return** | Equity - Initial Capital | Absolute gain/loss |
| **Return %** | (Total Return / Initial) × 100 | Percentage gain/loss |
| **Win Rate** | (Winning Trades / Total) × 100 | % of profitable trades |
| **Profit Factor** | Total Wins / Total Losses | Win size vs loss size |
| **Max DD** | (Peak - Trough) / Peak × 100 | Largest drawdown % |
| **Equity** | Cash + Position Value | Current portfolio value |

## Troubleshooting

### Engine won't start
```
✗ Failed to start trading engine
→ Check DB_URL in .env
→ Verify PostgreSQL is running
→ Check API logs for errors
```

### No trades executing
```
→ Check tickers have >252 days of data
→ Verify signal confidence >= 0.55
→ Check portfolio has sufficient cash
→ Review console logs for errors
```

### Wrong profits showing
```
→ Ensure prices updated correctly
→ Check for database connection issues
→ Verify trade event recording
→ Check equity calculation logic
```

## Environment Setup

**Required .env variables:**
```
DB_URL=postgresql://user:password@host:5432/database
```

**Start Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Frontend should connect to:**
```
http://localhost:8000
```

## API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Check API status |
| `/api/trading/start` | POST | Start session |
| `/api/trading/stop` | POST | Stop session |
| `/api/trading/status` | GET | Current status |
| `/api/trading/sessions/{id}` | GET | Session details |
| `/api/trading/trades/{id}` | GET | Trade history |
| `/api/trading/positions/{id}` | GET | Open positions |
| `/api/trading/history` | GET | Recent sessions |

## Performance Tips

1. **Optimize Update Interval**
   - 5-15 min: Very active trading
   - 1 hour: Standard/recommended
   - 4+ hours: Less frequent signals

2. **Choose Liquid Stocks**
   - SPY, QQQ, IWM (recommended)
   - Avoid low-volume stocks
   - Reduces slippage impact

3. **Monitor Resource Usage**
   - CPU: Should be low between updates
   - Memory: Steady ~50-100MB
   - Database: Check query performance

4. **Risk Management**
   - Start with small capital
   - Monitor max drawdown
   - Use stop-loss logic (coming soon)

## Common Commands

```bash
# Check if running
curl http://localhost:8000/api/health

# Start with default settings
python trading_client.py start

# Start with custom tickers
python trading_client.py start --tickers AAPL MSFT GOOGL

# Monitor with short interval
python trading_client.py monitor --interval 10

# View last 50 sessions
python trading_client.py history --limit 50

# Get specific session details
python trading_client.py session 123

# Stop current session
python trading_client.py stop

# ─── 30-DAY MODE ─────────────────────────────────

# START 30-DAY AGENT (runs for 30 days, even if browser closes)
python trading_client.py start-30days --tickers SPY QQQ IWM --capital 100000

# Check 30-day agent status
python trading_client.py 30days-status

# Get 30-day trade log
python trading_client.py 30days-log --limit 50

# Stop 30-day agent (anytime)
python trading_client.py stop-30days
```

## Database Queries

```sql
-- Current session equity over time
SELECT timestamp, equity FROM realtime_snapshots 
WHERE session_id = 1 
ORDER BY timestamp;

-- All trades from session
SELECT * FROM realtime_trades 
WHERE session_id = 1 
ORDER BY timestamp DESC;

-- Session performance
SELECT 
  total_trades,
  final_equity - capital as total_return,
  (final_equity - capital) / capital * 100 as return_pct
FROM realtime_sessions 
WHERE id = 1;

-- Best performing session
SELECT * FROM realtime_sessions 
WHERE status = 'closed'
ORDER BY (final_equity - capital) DESC 
LIMIT 1;
```

---

**Need help?** See `REALTIME_TRADING.md` for detailed documentation
