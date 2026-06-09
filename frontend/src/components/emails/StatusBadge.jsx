const STATUS_MAP = {
  pending_review: { label: 'Pending', cls: 'bg-warning/15 text-warning border-warning/30' },
  sent: { label: 'Sent', cls: 'bg-success/15 text-success border-success/30' },
  approved_no_gmail: { label: 'Approved', cls: 'bg-success/15 text-success border-success/30' },
  rejected: { label: 'Rejected', cls: 'bg-danger/15 text-danger border-danger/30' },
  no_reply_needed: { label: 'No reply', cls: 'bg-muted/15 text-muted border-muted/30' },
}

function Pill({ children, cls }) {
  return (
    <span
      className={`num inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide ${cls}`}
    >
      {children}
    </span>
  )
}

export function StatusBadge({ status }) {
  const s = STATUS_MAP[status] || { label: status || 'unknown', cls: 'bg-muted/15 text-muted border-muted/30' }
  return <Pill cls={s.cls}>{s.label}</Pill>
}

export function UrgencyBadge({ urgency }) {
  const map = {
    high: 'bg-danger/15 text-danger border-danger/30',
    normal: 'bg-warning/15 text-warning border-warning/30',
    low: 'bg-muted/15 text-muted border-muted/30',
  }
  if (!urgency) return null
  return <Pill cls={map[urgency] || map.low}>{urgency}</Pill>
}

export function ConfidenceBadge({ confidence }) {
  if (confidence === null || confidence === undefined) return null
  // Accept either 0..1 or 0..100 ranges.
  const pct = confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence)
  let cls = 'bg-danger/15 text-danger border-danger/30'
  if (pct >= 70) cls = 'bg-success/15 text-success border-success/30'
  else if (pct >= 50) cls = 'bg-warning/15 text-warning border-warning/30'
  return <Pill cls={cls}>{pct}%</Pill>
}

export function Tag({ children }) {
  if (!children) return null
  return (
    <span className="num inline-flex items-center rounded-md border border-border bg-bg-secondary px-2 py-0.5 text-[11px] text-muted">
      {children}
    </span>
  )
}

export default StatusBadge
