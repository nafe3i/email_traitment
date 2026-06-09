export default function EmptyState({ title = 'Nothing here', subtitle, icon = '📭', action }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-bg-secondary/40 px-6 py-16 text-center">
      <span className="text-4xl">{icon}</span>
      <h3 className="mt-4 text-lg font-semibold text-text">{title}</h3>
      {subtitle && <p className="mt-1 max-w-sm text-sm text-muted">{subtitle}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
