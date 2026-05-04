export default function ExecutionFeed({ trades, tickerResults }) {
  // Build a combined feed from all ticker trades
  const feedItems = [];

  if (tickerResults?.length) {
    tickerResults.forEach((tr) => {
      const lastTrades = (tr.trades || []).slice(-5).reverse();
      lastTrades.forEach((t) => {
        feedItems.push({ ...t, ticker: tr.ticker });
      });
    });
  }

  // Sort by exit_day descending, take top 10
  feedItems.sort((a, b) => (b.exit_day || b.entry_day) - (a.exit_day || a.entry_day));
  const display = feedItems.slice(0, 10);

  return (
    <div className="glass-panel rounded-xl flex flex-col h-80 animate-fade-in">
      <div className="p-4 border-b border-white/10 flex justify-between items-center bg-surface-container-low/50 rounded-t-xl">
        <h3 className="font-grotesk text-lg text-white font-medium">Live Execution Feed</h3>
        <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {display.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-outline/40">
            <span className="material-symbols-outlined text-3xl mb-2">swap_vert</span>
            <p className="font-grotesk text-xs">No trades yet</p>
          </div>
        ) : (
          display.map((t, i) => (
            <div
              key={i}
              className={`p-3 border border-white/5 rounded bg-white/5 flex flex-col gap-1 text-sm
                         hover:bg-white/10 transition-colors ${i > 4 ? 'opacity-60' : ''}`}
            >
              <div className="flex justify-between font-grotesk">
                <span className="text-outline text-xs">Day {t.entry_day}</span>
                <span className="text-white font-bold text-xs">{t.ticker}</span>
                <span className={t.ret >= 0 ? 'text-secondary text-xs' : 'text-coral text-xs'}>
                  {t.ret >= 0 ? 'LONG' : 'SHORT'}
                </span>
              </div>
              <div className="flex justify-between font-grotesk text-xs">
                <span className="text-outline">Entry: {t.entry_price?.toLocaleString()}</span>
                <span className="text-outline">Exit: {t.exit_price?.toLocaleString() || '--'}</span>
                <span className={t.ret >= 0 ? 'text-secondary' : 'text-coral'}>
                  P&L: {t.ret >= 0 ? '+' : ''}{t.ret?.toFixed(2)}%
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
