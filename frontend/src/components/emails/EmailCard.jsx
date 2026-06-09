import { useState } from 'react'
import ReplyEditor from './ReplyEditor'
import Spinner from '../ui/Spinner'
import {
  StatusBadge,
  UrgencyBadge,
  ConfidenceBadge,
  Tag,
} from './StatusBadge'

function fmtDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

export default function EmailCard({ email, onApprove, onReject }) {
  const [reply, setReply] = useState(email.suggested_reply || '')
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(null) // 'approve' | 'reject' | null

  const handleApprove = async () => {
    setBusy('approve')
    try {
      await onApprove?.(email.id, reply)
    } finally {
      setBusy(null)
    }
  }

  const handleReject = async () => {
    const reason = window.prompt('Reason for rejection?')
    if (reason === null) return // cancelled
    setBusy('reject')
    try {
      await onReject?.(email.id, reason)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div className="rounded-xl border border-border bg-bg-card">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border px-5 py-3">
        <StatusBadge status={email.status} />
        <UrgencyBadge urgency={email.urgency} />
        <ConfidenceBadge confidence={email.confidence} />
        <Tag>{email.category}</Tag>
        <Tag>{email.language}</Tag>
        <span className="num ml-auto text-xs text-muted">{fmtDate(email.processed_at)}</span>
      </div>

      {/* Body: original (left) + reply (right) */}
      <div className="grid grid-cols-1 gap-5 p-5 lg:grid-cols-2">
        <div className="min-w-0">
          <p className="mb-2 text-xs uppercase tracking-wider text-muted">Original email</p>
          <div className="space-y-1 text-sm">
            <p className="truncate">
              <span className="text-muted">From: </span>
              <span className="num text-text">{email.sender}</span>
            </p>
            <p className="font-semibold text-text">{email.subject || '(no subject)'}</p>
          </div>
          <div className="mt-3 max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-bg-secondary p-3 text-sm leading-relaxed text-muted">
            {email.body || '(empty body)'}
          </div>
        </div>

        <div className="min-w-0">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wider text-muted">Suggested reply</p>
            <button
              onClick={() => setEditing((v) => !v)}
              className="text-xs font-medium text-info transition-colors hover:text-accent"
            >
              {editing ? 'Done editing' : '✏️ Edit reply'}
            </button>
          </div>
          <ReplyEditor value={reply} onChange={setReply} editable={editing} />
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-wrap items-center justify-end gap-3 border-t border-border px-5 py-3">
        <button
          onClick={handleReject}
          disabled={!!busy}
          className="inline-flex items-center gap-2 rounded-lg border border-danger/40 px-4 py-2 text-sm font-medium text-danger transition-colors hover:bg-danger/10 disabled:opacity-50"
        >
          {busy === 'reject' ? <Spinner size={14} /> : '❌'} Reject
        </button>
        <button
          onClick={handleApprove}
          disabled={!!busy || !reply}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg-primary transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {busy === 'approve' ? <Spinner size={14} className="border-bg-primary/40 border-t-bg-primary" /> : '✅'} Approve &amp; Send
        </button>
      </div>
    </div>
  )
}
