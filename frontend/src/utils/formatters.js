export function formatCurrency(value) {
  if (value == null) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
    minimumFractionDigits: 2, maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value, decimals = 2) {
  if (value == null) return '--';
  const sign = value > 0 ? '+' : '';
  return `${sign}${Number(value).toFixed(decimals)}%`;
}

export function formatNumber(value, decimals = 2) {
  if (value == null) return '--';
  return Number(value).toFixed(decimals);
}

export function formatCompactCurrency(value) {
  if (value == null) return '--';
  if (Math.abs(value) >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  if (Math.abs(value) >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
  return formatCurrency(value);
}
