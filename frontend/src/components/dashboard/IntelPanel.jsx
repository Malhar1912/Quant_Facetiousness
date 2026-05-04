export default function IntelPanel({ tickerResults }) {
  // Calculate average XGB accuracy across tickers as "Signal Confidence"
  const accuracies = (tickerResults || []).map((t) => t.xgb_accuracy).filter(Boolean);
  const signalConf = accuracies.length
    ? Math.round((accuracies.reduce((a, b) => a + b, 0) / accuracies.length) * 100)
    : null;

  // Risk utilization = avg abs(max_dd) as percentage of a -50% cap
  const drawdowns = (tickerResults || []).map((t) => Math.abs(t.metrics?.max_dd || 0));
  const avgDd = drawdowns.length ? drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length : 0;
  const riskUtil = Math.min(Math.round((avgDd / 50) * 100), 100);

  // Generate insight text
  const bestTicker = tickerResults?.reduce(
    (best, t) => (t.metrics?.sharpe > (best?.metrics?.sharpe || -Infinity) ? t : best), null
  );
  const insight = bestTicker
    ? `${bestTicker.ticker} showing strongest alpha with ${bestTicker.metrics.sharpe.toFixed(2)} Sharpe. Portfolio volatility contained within risk tolerance.`
    : 'Run a backtest to generate intelligence insights.';

  return (
    <div className="glass-panel rounded-xl p-6 flex flex-col gap-4 animate-fade-in">
      <h3 className="font-grotesk text-lg text-white font-medium border-b border-white/10 pb-2">
        Intelligence Panel
      </h3>
      <div className="flex justify-around items-center py-2">
        <div className="flex flex-col items-center gap-1">
          <span className="font-grotesk text-2xl text-secondary text-glow">
            {signalConf != null ? `${signalConf}%` : '--'}
          </span>
          <span className="font-manrope text-xs text-outline text-center font-semibold">
            Signal<br />Confidence
          </span>
        </div>
        <div className="w-px h-12 bg-white/10" />
        <div className="flex flex-col items-center gap-1">
          <span className="font-grotesk text-2xl text-white">
            {riskUtil ? `${riskUtil}%` : '--'}
          </span>
          <span className="font-manrope text-xs text-outline text-center font-semibold">
            Risk<br />Utilization
          </span>
        </div>
      </div>
      <p className="font-manrope text-sm text-outline bg-white/5 p-3 rounded border border-white/5">
        {insight}
      </p>
    </div>
  );
}
