import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { formatCurrency } from '../../utils/formatters';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="glass-panel rounded-lg px-3 py-2 text-xs font-grotesk shadow-lg">
      <p className="text-outline mb-1">{label}</p>
      <p className="text-white font-semibold">{formatCurrency(payload[0].value)}</p>
    </div>
  );
}

export default function EquityCurve({ data, title = 'Portfolio Equity Curve' }) {
  if (!data?.length) {
    return (
      <div className="glass-panel rounded-xl p-6 flex flex-col min-h-[300px] items-center justify-center">
        <span className="material-symbols-outlined text-4xl text-outline/30 mb-2">show_chart</span>
        <p className="text-outline/50 font-grotesk text-sm">Run a backtest to see the equity curve</p>
      </div>
    );
  }

  return (
    <div className="glass-panel rounded-xl p-6 flex flex-col min-h-[300px] animate-fade-in">
      <h3 className="font-grotesk text-xl text-white mb-4 font-medium">{title}</h3>
      <div className="flex-1" style={{ minHeight: 220 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 5, right: 10, left: 10, bottom: 5 }}>
            <defs>
              <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2F80FF" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#2F80FF" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="date" tick={{ fill: '#8c90a0', fontSize: 10, fontFamily: 'Space Grotesk' }}
              tickLine={false} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              interval="preserveStartEnd" minTickGap={60}
            />
            <YAxis
              tick={{ fill: '#8c90a0', fontSize: 10, fontFamily: 'Space Grotesk' }}
              tickLine={false} axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
              tickFormatter={(v) => `$${(v / 1000).toFixed(0)}K`}
              width={55}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone" dataKey="value" stroke="#2F80FF" strokeWidth={2}
              fill="url(#eqGrad)" animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
