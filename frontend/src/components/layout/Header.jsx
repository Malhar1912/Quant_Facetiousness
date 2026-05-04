export default function Header({ confidence }) {
  return (
    <header className="fixed top-0 w-full z-50 flex items-center justify-between px-6 h-16 bg-navy-light/60 backdrop-blur-xl border-b border-white/10 shadow-[0_0_20px_rgba(47,128,255,0.1)]">
      <div className="flex items-center gap-4">
        <span className="text-xl font-bold bg-gradient-to-r from-electric to-aqua bg-clip-text text-transparent font-grotesk tracking-tight">
          Aether-1 Engine
        </span>
      </div>
      <nav className="hidden md:flex items-center gap-6">
        {['Terminal', 'Portfolio', 'Strategies', 'Intelligence', 'Risk'].map((item) => (
          <a
            key={item}
            href="#"
            className={
              item === 'Portfolio'
                ? 'text-electric border-b-2 border-electric pb-2 font-grotesk tracking-tight px-3'
                : 'text-slate-400 hover:text-white hover:bg-white/5 transition-all duration-300 font-grotesk tracking-tight px-3 py-1 rounded-md'
            }
          >
            {item}
          </a>
        ))}
      </nav>
      <div className="flex items-center gap-4">
        <span className="text-sm font-grotesk text-secondary-fixed-dim tracking-wide">
          LIVE: {confidence ? `${confidence}% Confidence` : 'Connecting...'}
        </span>
        <div className="flex gap-2 text-on-surface">
          <span className="material-symbols-outlined cursor-pointer hover:text-white transition-colors text-xl">notifications_active</span>
          <span className="material-symbols-outlined cursor-pointer hover:text-white transition-colors text-xl">settings</span>
          <span className="material-symbols-outlined cursor-pointer hover:text-white transition-colors text-xl">account_circle</span>
        </div>
      </div>
    </header>
  );
}
