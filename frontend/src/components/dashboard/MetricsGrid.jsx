import { formatPercent, formatNumber, formatCurrency } from '../../utils/formatters';

const METRIC_DEFS = [
  { key: 'total_return', label: 'Total Return', fmt: formatPercent, color: 'auto' },
  { key: 'cagr', label: 'CAGR', fmt: formatPercent, color: 'white' },
  { key: 'sharpe', label: 'Sharpe Ratio', fmt: (v) => formatNumber(v), color: 'white' },
  { key: 'max_dd', label: 'Max Drawdown', fmt: formatPercent, color: 'error' },
  { key: 'profit_factor', label: 'Profit Factor', fmt: (v) => formatNumber(v), color: 'white' },
  { key: 'win_rate', label: 'Win Rate', fmt: (v) => formatPercent(v, 1), color: 'white' },
  { key: 'total_trades', label: 'Total Trades', fmt: (v) => v?.toLocaleString() ?? '--', color: 'white' },
  { key: 'expectancy', label: 'Trade Expectancy', fmt: formatPercent, color: 'auto' },
];

export default function MetricsGrid({ metrics }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {METRIC_DEFS.map(({ key, label, fmt, color }, i) => {
        const val = metrics?.[key];
        let textColor = 'text-white';
        if (color === 'error') textColor = 'text-coral';
        else if (color === 'auto' && val != null) textColor = val >= 0 ? 'text-secondary' : 'text-coral';

        return (
          <div key={key} className="metric-card animate-slide-up" style={{ animationDelay: `${i * 50}ms` }}>
            <span className="font-manrope text-xs text-outline font-semibold">{label}</span>
            <span className={`font-grotesk text-lg tracking-wide ${textColor}`}>
              {val != null ? fmt(val) : '--'}
            </span>
          </div>
        );
      })}
    </div>
  );
}
