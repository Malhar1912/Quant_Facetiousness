export default function LoadingOverlay({ message }) {
  return (
    <div className="fixed inset-0 z-[100] bg-navy/80 backdrop-blur-md flex flex-col items-center justify-center gap-6">
      {/* Animated rings */}
      <div className="relative w-24 h-24">
        <div className="absolute inset-0 border-2 border-electric/30 rounded-full animate-ping" />
        <div className="absolute inset-2 border-2 border-electric/50 rounded-full animate-pulse" />
        <div className="absolute inset-4 border-2 border-electric rounded-full animate-spin" style={{ animationDuration: '3s' }} />
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="material-symbols-outlined text-electric text-3xl">neurology</span>
        </div>
      </div>
      <div className="text-center">
        <p className="font-grotesk text-lg text-white mb-1">Processing</p>
        <p className="font-manrope text-sm text-outline">{message || 'Running walk-forward backtest...'}</p>
        <p className="font-manrope text-xs text-outline/50 mt-2">This may take 1-3 minutes per ticker</p>
      </div>
    </div>
  );
}
