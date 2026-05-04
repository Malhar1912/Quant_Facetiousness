import { formatCurrency, formatPercent } from '../../utils/formatters';

export default function PortfolioHero({ portfolio, capital, tickerCount }) {
  const finalValue = portfolio?.equity_curve?.length
    ? portfolio.equity_curve[portfolio.equity_curve.length - 1]?.value
    : capital * tickerCount;
  const totalReturn = portfolio?.metrics?.total_return;
  const cagr = portfolio?.metrics?.cagr;

  return (
    <div className="glass-panel rounded-xl p-6 relative overflow-hidden animate-fade-in">
      {/* Background glow */}
      <div className="absolute inset-0 bg-gradient-to-br from-electric/10 to-transparent pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-full h-1/2 opacity-20 pointer-events-none"
        style={{ background: 'linear-gradient(to top, rgba(132,207,255,0.1), transparent)' }}>
        <svg className="w-full h-full stroke-secondary fill-none" preserveAspectRatio="none" strokeWidth="0.5" viewBox="0 0 100 20">
          <path d="M0 20 Q 25 5, 50 15 T 100 5" />
        </svg>
      </div>

      <div className="relative z-10">
        <h2 className="font-manrope text-xs text-outline uppercase tracking-wider mb-2 font-semibold">
          Live Portfolio Value
        </h2>
        <div className="font-grotesk text-5xl md:text-[64px] font-semibold text-white mb-4 tracking-tighter">
          {formatCurrency(finalValue)}
        </div>
        <div className="flex gap-4 flex-wrap">
          <div className="bg-secondary/5 border border-secondary/20 rounded px-3 py-2 flex flex-col">
            <span className="font-manrope text-xs text-outline font-semibold">Total Return</span>
            <span className={`font-grotesk text-sm tracking-wide ${totalReturn >= 0 ? 'text-secondary' : 'text-coral'}`}>
              {formatPercent(totalReturn)}
            </span>
          </div>
          <div className="bg-secondary/5 border border-secondary/20 rounded px-3 py-2 flex flex-col">
            <span className="font-manrope text-xs text-outline font-semibold">CAGR</span>
            <span className={`font-grotesk text-sm tracking-wide ${cagr >= 0 ? 'text-secondary' : 'text-coral'}`}>
              {formatPercent(cagr)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
