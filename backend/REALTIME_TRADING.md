# Aether-1 Real-Time Trading Engine

## Overview

Aether-1 is now a **real-time trading system** that continuously generates trading signals, executes paper trades, and tracks live portfolio performance. The system uses machine learning models to analyze market conditions and generate trading signals with confidence scores.

## Key Features

- **Real-Time Signal Generation**: Continuous ML-based trading signals
- **Position Management**: Automatic open/close based on signals
- **Live Tracking**: Real-time equity, P&L, and position tracking
- **Database Persistence**: All trades and snapshots stored in PostgreSQL
- **Web API**: Full REST API for control and monitoring
- **Paper Trading**: Risk-free testing with simulated capital

## Architecture

```
frontend (React) 
    ↓
API Endpoints (/api/trading/*)
    ↓
Main Backend (FastAPI)
    ↓
Real-Time Engine (realtime_engine.py)
    ├─ Portfolio Management
    ├─ Signal Generation
    └─ Trade Execution
    ↓
Database (PostgreSQL)
    └─ Sessions, Trades, Snapshots
```

## Getting Started

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Environment Variables

Ensure your `.env` file has:
```
DB_URL=postgresql://user:password@host/database
```

### 3. Start the Backend

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Start Trading
**POST** `/api/trading/start`

Request:
```json
{
  "tickers": ["SPY", "QQQ", "IWM"],
  "initial_capital": 100000.0,
  "interval_seconds": 3600
}
```

Response:
```json
{
  "status": "started",
  "session_id": 1,
  "tickers": ["SPY", "QQQ", "IWM"],
  "initial_capital": 100000.0,
  "interval": 3600
}
```

### Stop Trading
**POST** `/api/trading/stop`

Response:
```json
{
  "status": "stopped",
  "session_id": 1
}
```

### Get Current Status
**GET** `/api/trading/status`

Response:
```json
{
  "running": true,
  "session_id": 1,
  "equity": 102500.50,
  "cash": 52500.50,
  "total_return": 2500.50,
  "return_pct": 2.50,
  "positions": [
    {
      "ticker": "SPY",
      "shares": 100,
      "entry_price": 500.0,
      "current_price": 502.50,
      "entry_date": "2026-05-04T10:00:00",
      "unrealized_pnl": 250.0,
      "unrealized_pnl_pct": 0.50
    }
  ],
  "positions_count": 1,
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.0,
  "max_dd": -5.5,
  "profit_factor": 2.3,
  "last_update": "2026-05-04T11:00:00"
}
```

### Get Session Details
**GET** `/api/trading/sessions/{session_id}`

Response:
```json
{
  "session": {
    "id": 1,
    "tickers": "SPY,QQQ,IWM",
    "status": "active",
    "capital": 100000.0,
    "created_at": "2026-05-04T10:00:00",
    "final_equity": null,
    "total_trades": null,
    "total_return": null
  },
  "trades": [...],
  "latest_snapshot": {...}
}
```

### Get Session Trades
**GET** `/api/trading/trades/{session_id}?limit=100`

### Get Session Positions
**GET** `/api/trading/positions/{session_id}`

### Get Trading History
**GET** `/api/trading/history?limit=20`

## Configuration

### Real-Time Engine Parameters

Edit `realtime_engine.py` to customize:

```python
# Position sizing (percent of portfolio)
risk_amount = portfolio_value * 0.02  # 2% risk per trade

# Signal thresholds
confidence_threshold = 0.55  # Buy signals above 55%

# Feature weights in signal calculation
# Customize _calculate_confidence() method
```

### Data Update Interval

Set `interval_seconds` when starting trading (default: 3600 = 1 hour)

## Database Schema

The system automatically creates these tables:

### `realtime_sessions`
- Track each trading session
- Stores initial capital, start/end times
- Records final equity and total returns

### `realtime_trades`
- Event log (OPEN/CLOSE)
- Timestamp, price, shares, confidence
- Links to session_id

### `realtime_snapshots`
- Point-in-time portfolio snapshots
- Positions JSON
- Metrics JSON
- Taken at each update interval

## Signal Generation

The real-time engine generates signals based on:

1. **RSI (Relative Strength Index)**
   - RSI < 30: Oversold (Bullish)
   - RSI > 70: Overbought (Bearish)

2. **Momentum**
   - Positive momentum favors BUY signals
   - Negative momentum favors SELL signals

3. **Moving Average Distance**
   - Price close to MA is healthy indicator

4. **Feature Engineering**
   - Log returns
   - Volatility
   - Amihud illiquidity
   - And more from strategy.py

## Position Sizing

Position size is calculated as:
```
risk_amount = portfolio_value * 0.02 (2% risk)
base_shares = risk_amount / price
final_shares = base_shares * confidence
```

Larger confidence scores → Larger positions

## Performance Metrics

The system tracks:

- **Total Return**: Portfolio value - Initial capital
- **Return %**: Percentage return on capital
- **Win Rate**: (Winning Trades / Total Trades) × 100
- **Profit Factor**: Total Wins / Total Losses
- **Max Drawdown**: Maximum peak-to-trough decline
- **Unrealized P&L**: Open position gains/losses

## Monitoring

### Real-Time Console Output

The backend prints trading activity:
```
[2026-05-04 10:00:00] Fetching live data...
[2026-05-04 10:00:05] Generating signals...
[2026-05-04 10:00:10] Executing trades...
[2026-05-04 10:00:15] Saving snapshot...
Portfolio Equity: $102,500.50 | Return: 2.50% | Trades: 5 | Positions: 1
```

### API Polling

Poll `/api/trading/status` endpoint for live updates

## Troubleshooting

### Database Connection Error
- Verify DB_URL in .env
- Check PostgreSQL is running
- Ensure database exists

### No Signals Generated
- Check data for selected tickers
- Verify data has at least 252 days (1 year)
- Check signal confidence thresholds

### Trades Not Executing
- Verify portfolio has sufficient cash
- Check position sizing calculation
- Review trade event logs

## Frontend Integration

The React frontend can:

1. **Start/Stop Trading**
```javascript
const response = await fetch('/api/trading/start', {
  method: 'POST',
  body: JSON.stringify({
    tickers: ['SPY', 'QQQ'],
    initial_capital: 100000
  })
});
```

2. **Monitor Status**
```javascript
const status = await fetch('/api/trading/status').then(r => r.json());
```

3. **View History**
```javascript
const history = await fetch('/api/trading/history').then(r => r.json());
```

## Performance Tips

1. **Update Interval**: 
   - Shorter intervals = more data but higher costs
   - Recommended: 3600s (1 hour) for daily signals

2. **Tickers**:
   - Limit to 10-20 tickers for best performance
   - Focus on liquid stocks

3. **Database**:
   - Regular backups of realtime_snapshots
   - Archive old sessions periodically

## Future Enhancements

- [ ] Broker API integration (Interactive Brokers, Alpaca)
- [ ] Real money trading support
- [ ] Advanced risk management (stop-loss, take-profit)
- [ ] Portfolio correlation analysis
- [ ] News sentiment integration
- [ ] Multi-timeframe analysis
- [ ] Options trading support

---

**Version 2.0.0** | Real-Time Trading Edition
