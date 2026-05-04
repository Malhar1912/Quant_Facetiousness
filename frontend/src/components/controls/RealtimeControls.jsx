import { useState, useEffect } from 'react';

const AVAILABLE_TICKERS = ['SPY', 'QQQ', 'IWM', 'AAPL', 'MSFT', 'GOOGL', 'NVDA'];
const DEFAULT_TICKERS = ['SPY', 'QQQ', 'IWM'];

export default function RealtimeControls({ onStart, onStop, status, loading }) {
  const [selected, setSelected] = useState(DEFAULT_TICKERS);
  const [capital, setCapital] = useState(100000);
  const [isAgent30Day, setIsAgent30Day] = useState(false);
  const [statusRefresh, setStatusRefresh] = useState(null);

  // Poll status if agent is running
  useEffect(() => {
    if (!isAgent30Day) return;
    
    const interval = setInterval(() => {
      setStatusRefresh(Date.now());
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, [isAgent30Day]);

  useEffect(() => {
    if (status?.running) {
      setIsAgent30Day(true);
    } else {
      setIsAgent30Day(false);
    }
  }, [status]);

  const toggle = (ticker) => {
    setSelected((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker]
    );
  };

  const handleStart30Days = async () => {
    if (selected.length === 0) return;
    try {
      await onStart(selected, capital);
      setIsAgent30Day(true);
    } catch (err) {
      console.error('Failed to start 30-day agent:', err);
    }
  };

  const handleStop = async () => {
    try {
      await onStop();
      setIsAgent30Day(false);
    } catch (err) {
      console.error('Failed to stop agent:', err);
    }
  };

  const returnPct = status?.metrics?.return_pct || 0;
  const isProfit = returnPct > 0;

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col gap-4 animate-fade-in">
      <h3 className="font-grotesk text-lg text-white font-medium border-b border-white/10 pb-2 flex items-center gap-2">
        <span className="material-symbols-outlined text-secondary">auto_awesome</span>
        Real-Time Trading
      </h3>

      {!isAgent30Day ? (
        <>
          {/* Ticker Selection */}
          <div>
            <label className="font-manrope text-xs text-outline uppercase tracking-wider font-semibold block mb-2">
              Asset Selection
            </label>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_TICKERS.map((t) => (
                <button
                  key={t}
                  onClick={() => toggle(t)}
                  disabled={loading}
                  className={`px-3 py-1.5 rounded-md text-xs font-grotesk font-medium transition-all duration-200 
                    ${selected.includes(t)
                      ? 'bg-secondary/20 text-secondary border border-secondary/40'
                      : 'bg-white/5 text-outline border border-white/10 hover:bg-white/10'} 
                    ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Capital Input */}
          <div className="flex flex-col gap-1">
            <label className="font-manrope text-[10px] text-outline uppercase font-semibold">Initial Capital</label>
            <div className="flex items-center gap-2">
              <span className="text-outline text-sm">$</span>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                min={10000}
                step={10000}
                disabled={loading}
                className="input-field text-sm flex-1"
              />
            </div>
          </div>

          {/* 30-Day Button */}
          <button
            onClick={handleStart30Days}
            disabled={loading || selected.length === 0}
            className="btn-primary flex items-center justify-center gap-2 bg-gradient-to-r from-secondary to-secondary/80 hover:from-secondary/90 hover:to-secondary/70 disabled:opacity-50"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Starting...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-base">rocket_launch</span>
                Start 30-Day Agent
              </>
            )}
          </button>
          <p className="font-manrope text-xs text-outline text-center">
            🔄 Trades for 30 days • Continues even if browser closes • Updates hourly
          </p>
        </>
      ) : (
        <>
          {/* Agent Running Status */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-secondary/10 border border-secondary/30 rounded-lg p-3">
              <p className="font-manrope text-xs text-outline uppercase mb-1">Equity</p>
              <p className="font-grotesk text-lg text-secondary font-semibold">
                ${(status?.equity || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </p>
            </div>
            <div 
              className="rounded-lg p-3 border"
              style={{
                backgroundColor: isProfit ? 'rgba(74, 222, 128, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                borderColor: isProfit ? 'rgba(74, 222, 128, 0.3)' : 'rgba(239, 68, 68, 0.3)'
              }}
            >
              <p className="font-manrope text-xs text-outline uppercase mb-1">Return</p>
              <p className="font-grotesk text-lg font-semibold" style={{ color: isProfit ? '#4ade80' : '#ef4444' }}>
                {returnPct > 0 ? '+' : ''}{returnPct.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* Live Stats */}
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <p className="text-outline uppercase font-semibold mb-1">Positions</p>
              <p className="font-grotesk text-base text-white">{status?.positions_count || 0}</p>
            </div>
            <div>
              <p className="text-outline uppercase font-semibold mb-1">Trades</p>
              <p className="font-grotesk text-base text-white">{status?.metrics?.total_trades || 0}</p>
            </div>
            <div>
              <p className="text-outline uppercase font-semibold mb-1">Win Rate</p>
              <p className="font-grotesk text-base text-white">{(status?.metrics?.win_rate || 0).toFixed(1)}%</p>
            </div>
          </div>

          {/* Tickers Info */}
          <div className="bg-white/5 rounded-lg p-3 border border-white/10">
            <p className="font-manrope text-xs text-outline uppercase font-semibold mb-2">Trading</p>
            <p className="font-grotesk text-sm text-secondary">{status?.tickers?.join(' • ') || 'N/A'}</p>
          </div>

          {/* Last Update */}
          <p className="font-manrope text-xs text-outline text-center">
            Last Update: {status?.last_update ? new Date(status.last_update).toLocaleTimeString() : 'N/A'}
          </p>

          {/* Stop Button */}
          <button
            onClick={handleStop}
            disabled={loading}
            className="btn-secondary flex items-center justify-center gap-2 bg-danger/20 hover:bg-danger/30 text-danger border border-danger/40"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Stopping...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-base">stop_circle</span>
                Stop Agent
              </>
            )}
          </button>
        </>
      )}
    </div>
  );
}
