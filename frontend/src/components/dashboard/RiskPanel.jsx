export default function RiskPanel({ portfolio }) {
  const maxDd = Math.abs(portfolio?.metrics?.max_dd || 0);
  const riskCapPercent = Math.min(Math.round((maxDd / 30) * 100), 100);
  const volatility = portfolio?.metrics?.volatility;
  const calmar = portfolio?.metrics?.calmar;

  return (
    <div className="glass-panel rounded-xl p-6 flex flex-col gap-4 animate-fade-in">
      <h3 className="font-grotesk text-lg text-white font-medium border-b border-white/10 pb-2 flex items-center gap-2">
        <span className="material-symbols-outlined text-outline">shield</span> Risk Panel
      </h3>

      {/* Daily Risk Cap Bar */}
      <div className="flex flex-col gap-2">
        <div className="flex justify-between font-manrope text-xs font-semibold">
          <span className="text-outline">Daily Risk Cap</span>
          <span className="text-white">{riskCapPercent}%</span>
        </div>
        <div className="h-1.5 w-full bg-surface-container-highest rounded-full overflow-hidden">
          <div
            className="h-full bg-secondary rounded-full transition-all duration-1000"
            style={{ width: `${riskCapPercent}%` }}
          />
        </div>
      </div>

      {/* Volatility & Calmar */}
      <div className="flex justify-between text-xs font-grotesk">
        <div className="flex flex-col gap-0.5">
          <span className="text-outline font-manrope font-semibold">Volatility</span>
          <span className="text-white">{volatility != null ? `${volatility.toFixed(1)}%` : '--'}</span>
        </div>
        <div className="flex flex-col gap-0.5 text-right">
          <span className="text-outline font-manrope font-semibold">Calmar Ratio</span>
          <span className="text-white">{calmar != null ? calmar.toFixed(2) : '--'}</span>
        </div>
      </div>

      {/* Status Indicators */}
      <div className="grid grid-cols-2 gap-2 mt-1">
        <div className="bg-surface-container-high/30 p-2 rounded border border-secondary/20 flex flex-col items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-secondary animate-pulse" />
          <span className="font-manrope text-[10px] text-outline text-center uppercase font-semibold">
            Stop-Loss Triggers
          </span>
          <span className="font-grotesk text-xs text-white">ACTIVE</span>
        </div>
        <div className="bg-surface-container-high/30 p-2 rounded border border-white/5 flex flex-col items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-outline" />
          <span className="font-manrope text-[10px] text-outline text-center uppercase font-semibold">
            Safeguard Interventions
          </span>
          <span className="font-grotesk text-xs text-outline">STANDBY</span>
        </div>
      </div>
    </div>
  );
}
