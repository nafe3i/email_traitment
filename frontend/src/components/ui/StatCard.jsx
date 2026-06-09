const ACCENTS = {
  accent: 'text-accent',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-danger',
  info: 'text-info',
  muted: 'text-text',
}

export default function StatCard({ label, value, accent = 'muted', icon, loading }) {
  return (
    <div className="rounded-xl border border-border bg-bg-card p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wider text-muted">{label}</p>
        {icon && <span className="text-lg opacity-70">{icon}</span>}
      </div>
      <p className={`num mt-3 text-3xl font-medium ${ACCENTS[accent] || ACCENTS.muted}`}>
        {loading ? '—' : value}
      </p>
    </div>
  )
}
