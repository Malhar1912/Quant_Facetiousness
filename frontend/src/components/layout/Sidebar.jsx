const NAV_ITEMS = [
  { icon: 'dashboard', label: 'Dashboard', active: true },
  { icon: 'query_stats', label: 'Live Feed' },
  { icon: 'security', label: 'Risk Metrics' },
  { icon: 'history', label: 'Backtests' },
  { icon: 'manage_accounts', label: 'Admin' },
];

export default function Sidebar({ onDeploy }) {
  return (
    <aside className="hidden md:flex flex-col h-screen w-64 left-0 top-0 fixed bg-navy border-r border-white/10 z-40 pt-16">
      <div className="p-6 flex flex-col gap-2 border-b border-white/5">
        <h2 className="text-lg font-black text-white font-grotesk">System Core</h2>
        <p className="text-xs text-slate-400 font-grotesk">Autonomous v4.2</p>
      </div>

      <nav className="flex-1 overflow-y-auto py-4 flex flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => (
          <a key={item.label} href="#" className={item.active ? 'nav-link-active' : 'nav-link'}>
            <span className="material-symbols-outlined text-lg">{item.icon}</span>
            {item.label}
          </a>
        ))}
      </nav>

      <div className="p-4 border-t border-white/5">
        <button onClick={onDeploy} className="w-full btn-primary">
          Deploy Capital
        </button>
      </div>

      <div className="p-4 flex flex-col gap-2">
        <a href="#" className="flex items-center gap-3 px-4 py-1 text-slate-500 hover:text-slate-200 font-grotesk text-xs">
          <span className="material-symbols-outlined text-sm">sensors</span> System Status
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-1 text-slate-500 hover:text-slate-200 font-grotesk text-xs">
          <span className="material-symbols-outlined text-sm">menu_book</span> Documentation
        </a>
      </div>
    </aside>
  );
}
