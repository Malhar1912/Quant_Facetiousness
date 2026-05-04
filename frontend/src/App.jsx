import { useEffect } from 'react';
import Header from './components/layout/Header';
import PortfolioHero from './components/dashboard/PortfolioHero';
import MetricsGrid from './components/dashboard/MetricsGrid';
import EquityCurve from './components/dashboard/EquityCurve';
import ExecutionFeed from './components/dashboard/ExecutionFeed';
import IntelPanel from './components/dashboard/IntelPanel';
import RiskPanel from './components/dashboard/RiskPanel';
import LoadingOverlay from './components/common/LoadingOverlay';
import BacktestControls from './components/controls/BacktestControls';
import RealtimeControls from './components/controls/RealtimeControls';
import { useBacktest } from './hooks/useBacktest';
import { useRealtime } from './hooks/useRealtime';

export default function App() {
  const { data, loading, error, progress, runBacktest, loadLatest } = useBacktest();
  const { status, loading: rtLoading, error: rtError, start30Days, stop30Days, getStatus } = useRealtime();

  useEffect(() => { 
    loadLatest(); 
    const interval = setInterval(loadLatest, 60000); // Poll for latest backtest run
    return () => clearInterval(interval);
  }, [loadLatest]);

  // Poll 30-day agent status if running
  useEffect(() => {
    if (!status?.running) return;
    
    const interval = setInterval(getStatus, 30000); // Poll every 30 seconds
    getStatus(); // Initial check
    return () => clearInterval(interval);
  }, [status?.running, getStatus]);

  // Aggregate metrics: prefer portfolio-level, fallback to first ticker
  const portfolio = data?.portfolio || {};
  const tickerResults = data?.ticker_results || [];
  const firstTicker = tickerResults[0] || {};

  // For metrics grid: use first ticker's detailed metrics (includes trade stats)
  const displayMetrics = firstTicker?.metrics || {};
  // If multiple tickers, overlay portfolio-level stats
  if (tickerResults.length > 1 && portfolio?.metrics) {
    displayMetrics.total_return = portfolio.metrics.total_return;
    displayMetrics.cagr = portfolio.metrics.cagr;
    displayMetrics.sharpe = portfolio.metrics.sharpe;
    displayMetrics.max_dd = portfolio.metrics.max_dd;
    displayMetrics.volatility = portfolio.metrics.volatility;
  }

  // Aggregate trade counts across all tickers
  if (tickerResults.length > 1) {
    displayMetrics.total_trades = tickerResults.reduce((s, t) => s + (t.metrics?.total_trades || 0), 0);
    const wrs = tickerResults.map(t => t.metrics?.win_rate).filter(Boolean);
    displayMetrics.win_rate = wrs.length ? wrs.reduce((a, b) => a + b, 0) / wrs.length : 0;
    const pfs = tickerResults.map(t => t.metrics?.profit_factor).filter(Boolean);
    displayMetrics.profit_factor = pfs.length ? pfs.reduce((a, b) => a + b, 0) / pfs.length : 0;
    const exps = tickerResults.map(t => t.metrics?.expectancy).filter(Boolean);
    displayMetrics.expectancy = exps.length ? exps.reduce((a, b) => a + b, 0) / exps.length : 0;
  }

  // Equity curve data
  const equityCurveData = portfolio?.equity_curve || firstTicker?.equity_curve || [];

  // Signal confidence for header
  const avgAccuracy = tickerResults.length
    ? Math.round(tickerResults.reduce((s, t) => s + (t.xgb_accuracy || 0), 0) / tickerResults.length * 100 * 10) / 10
    : null;

  const tickerCount = data?.tickers?.length || 3;
  const capital = data?.capital_per_ticker || 10000;

  return (
    <div className="min-h-screen flex flex-col md:flex-row overflow-x-hidden">
      {loading && <LoadingOverlay message={progress} />}

      <Header confidence={avgAccuracy} />

      <main className="flex-1 pt-16 p-6 lg:p-8 bg-navy text-on-surface">
        {/* Hero Section */}
        <div className="mb-6 flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="font-grotesk text-4xl md:text-5xl font-semibold text-white tracking-tight">
                Aether-1 Engine
              </h1>
              <span className="glass-chip px-2 py-1 rounded text-xs font-manrope uppercase tracking-wider flex items-center gap-1 animate-pulse-glow font-semibold">
                <span className="w-2 h-2 rounded-full bg-secondary" /> LIVE 24/7
              </span>
            </div>
            <p className="font-manrope text-lg text-outline">Multi-Regime Mean Reversion</p>
          </div>
          <div className="glass-panel p-3 rounded-lg flex items-center gap-4">
            <div className="flex flex-col">
              <span className="font-manrope text-xs text-outline uppercase tracking-widest font-semibold">Market Mode</span>
              <span className="font-grotesk text-sm text-secondary text-glow tracking-wide">
                {loading ? 'PROCESSING' : data ? 'SCANNING' : 'IDLE'}
              </span>
            </div>
            <div className="h-8 w-px bg-white/10" />
            <div className="flex flex-col max-w-xs">
              <span className="font-manrope text-sm text-outline truncate">
                {loading
                  ? 'Running walk-forward backtest engine...'
                  : error
                    ? `Error: ${error}`
                    : 'Monitoring momentum divergence... Signal confidence rising...'}
              </span>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Column (8 cols) */}
          <div className="lg:col-span-8 flex flex-col gap-5">
            <PortfolioHero portfolio={portfolio} capital={capital} tickerCount={tickerCount} />
            <MetricsGrid metrics={displayMetrics} />
            <EquityCurve data={equityCurveData} />
          </div>

          {/* Right Column (4 cols) */}
          <div className="lg:col-span-4 flex flex-col gap-5">
            <RealtimeControls 
              onStart={start30Days}
              onStop={stop30Days}
              status={status}
              loading={rtLoading}
            />
            <BacktestControls 
              onRun={runBacktest}
              loading={loading}
            />
            <ExecutionFeed tickerResults={tickerResults} />
            <IntelPanel tickerResults={tickerResults} />
            <RiskPanel portfolio={portfolio} />
          </div>
        </div>
      </main>
    </div>
  );
}
