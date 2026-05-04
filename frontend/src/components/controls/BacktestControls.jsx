import { useState } from 'react';

const AVAILABLE_TICKERS = ['SPY', 'GME', 'BTC-USD', 'QQQ', 'NVDA', 'TSLA', 'VXX'];
const DEFAULT_TICKERS = ['SPY', 'GME', 'BTC-USD'];

export default function BacktestControls({ onRun, loading }) {
  const [selected, setSelected] = useState(DEFAULT_TICKERS);
  const [start, setStart] = useState('2018-01-01');
  const [end, setEnd] = useState('2024-12-31');
  const [capital, setCapital] = useState(10000);

  const toggle = (ticker) => {
    setSelected((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker]
    );
  };

  const handleRun = () => {
    if (selected.length === 0) return;
    onRun(selected, start, end, capital);
  };

  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col gap-4 animate-fade-in">
      <h3 className="font-grotesk text-lg text-white font-medium border-b border-white/10 pb-2 flex items-center gap-2">
        <span className="material-symbols-outlined text-electric">tune</span>
        Backtest Configuration
      </h3>

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
              className={`px-3 py-1.5 rounded-md text-xs font-grotesk font-medium transition-all duration-200 
                ${selected.includes(t)
                  ? 'bg-electric/20 text-electric border border-electric/40'
                  : 'bg-white/5 text-outline border border-white/10 hover:bg-white/10'}`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Date Range + Capital */}
      <div className="grid grid-cols-3 gap-3">
        <div className="flex flex-col gap-1">
          <label className="font-manrope text-[10px] text-outline uppercase font-semibold">Start</label>
          <input type="date" value={start} onChange={(e) => setStart(e.target.value)} className="input-field text-xs" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-manrope text-[10px] text-outline uppercase font-semibold">End</label>
          <input type="date" value={end} onChange={(e) => setEnd(e.target.value)} className="input-field text-xs" />
        </div>
        <div className="flex flex-col gap-1">
          <label className="font-manrope text-[10px] text-outline uppercase font-semibold">Capital / Ticker</label>
          <input
            type="number" value={capital} min={1000} step={1000}
            onChange={(e) => setCapital(Number(e.target.value))}
            className="input-field text-xs"
          />
        </div>
      </div>

      {/* Run Button */}
      <button onClick={handleRun} disabled={loading || selected.length === 0} className="btn-primary flex items-center justify-center gap-2">
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Running Backtest...
          </>
        ) : (
          <>
            <span className="material-symbols-outlined text-sm">rocket_launch</span>
            Run Backtest ({selected.length} asset{selected.length !== 1 ? 's' : ''})
          </>
        )}
      </button>
    </div>
  );
}
