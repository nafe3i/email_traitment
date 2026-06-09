import { Fragment, useEffect, useMemo, useState } from 'react'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import {
  StatusBadge,
  UrgencyBadge,
  ConfidenceBadge,
  Tag,
} from '../components/emails/StatusBadge'
import useEmailStore from '../store/useEmailStore'
import { useToast } from '../hooks/useToast'
import { errorMessage } from '../api/client'

const PAGE_SIZE = 20

const STATUS_OPTIONS = ['pending_review', 'sent', 'approved_no_gmail', 'rejected', 'no_reply_needed']
const URGENCY_OPTIONS = ['high', 'normal', 'low']

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

function Select({ label, value, onChange, options }) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="num rounded-lg border border-border bg-bg-secondary px-3 py-2 text-xs text-text outline-none focus:border-accent"
    >
      <option value="">{label}: all</option>
      {options.map((o) => (
        <option key={o} value={o}>
          {o}
        </option>
      ))}
    </select>
  )
}

export default function HistoryPage() {
  const emails = useEmailStore((s) => s.emails)
  const fetchHistory = useEmailStore((s) => s.fetchHistory)
  const loading = useEmailStore((s) => s.loadingHistory)
  const { error } = useToast()

  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [category, setCategory] = useState('')
  const [language, setLanguage] = useState('')
  const [urgency, setUrgency] = useState('')
  const [sortDir, setSortDir] = useState('desc')
  const [page, setPage] = useState(1)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    fetchHistory().catch((e) => error(errorMessage(e, 'Failed to load history')))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const categories = useMemo(
    () => [...new Set(emails.map((e) => e.category).filter(Boolean))].sort(),
    [emails],
  )
  const languages = useMemo(
    () => [...new Set(emails.map((e) => e.language).filter(Boolean))].sort(),
    [emails],
  )

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    let list = emails.filter((e) => {
      if (status && e.status !== status) return false
      if (category && e.category !== category) return false
      if (language && e.language !== language) return false
      if (urgency && e.urgency !== urgency) return false
      if (q) {
        const hay = `${e.sender || ''} ${e.subject || ''}`.toLowerCase()
        if (!hay.includes(q)) return false
      }
      return true
    })
    list = [...list].sort((a, b) => {
      const da = new Date(a.processed_at || 0).getTime()
      const db = new Date(b.processed_at || 0).getTime()
      return sortDir === 'asc' ? da - db : db - da
    })
    return list
  }, [emails, search, status, category, language, urgency, sortDir])

  // Reset to first page whenever filters change.
  useEffect(() => {
    setPage(1)
  }, [search, status, category, language, urgency, sortDir])

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  return (
    <div className="space-y-5">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search sender or subject…"
          className="num min-w-[200px] flex-1 rounded-lg border border-border bg-bg-secondary px-3 py-2 text-sm text-text outline-none focus:border-accent"
        />
        <Select label="Status" value={status} onChange={setStatus} options={STATUS_OPTIONS} />
        <Select label="Category" value={category} onChange={setCategory} options={categories} />
        <Select label="Language" value={language} onChange={setLanguage} options={languages} />
        <Select label="Urgency" value={urgency} onChange={setUrgency} options={URGENCY_OPTIONS} />
        <button
          onClick={() => setSortDir((d) => (d === 'desc' ? 'asc' : 'desc'))}
          className="rounded-lg border border-border bg-bg-secondary px-3 py-2 text-xs font-medium text-muted hover:text-text"
        >
          Date {sortDir === 'desc' ? '↓' : '↑'}
        </button>
      </div>

      {loading && emails.length === 0 ? (
        <div className="flex justify-center py-16">
          <Spinner size={32} />
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState title="No emails found" subtitle="Try adjusting your filters or search." icon="🔍" />
      ) : (
        <>
          <div className="overflow-hidden rounded-xl border border-border bg-bg-card">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border text-xs uppercase tracking-wider text-muted">
                <tr>
                  <th className="px-4 py-3 font-medium">Subject / Sender</th>
                  <th className="hidden px-4 py-3 font-medium md:table-cell">Category</th>
                  <th className="hidden px-4 py-3 font-medium sm:table-cell">Date</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {pageItems.map((e) => (
                  <Fragment key={e.id}>
                    <tr
                      onClick={() => setExpanded(expanded === e.id ? null : e.id)}
                      className="cursor-pointer transition-colors hover:bg-bg-secondary"
                    >
                      <td className="px-4 py-3">
                        <p className="truncate font-medium text-text">{e.subject || '(no subject)'}</p>
                        <p className="num truncate text-xs text-muted">{e.sender}</p>
                      </td>
                      <td className="hidden px-4 py-3 md:table-cell">
                        <div className="flex flex-wrap gap-1">
                          <Tag>{e.category}</Tag>
                          <Tag>{e.language}</Tag>
                        </div>
                      </td>
                      <td className="num hidden px-4 py-3 text-xs text-muted sm:table-cell">
                        {fmtDate(e.processed_at)}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <StatusBadge status={e.status} />
                          <UrgencyBadge urgency={e.urgency} />
                        </div>
                      </td>
                    </tr>
                    {expanded === e.id && (
                      <tr className="bg-bg-secondary/50">
                        <td colSpan={4} className="px-4 py-4">
                          <div className="grid gap-4 lg:grid-cols-2">
                            <div>
                              <p className="mb-1 text-xs uppercase tracking-wider text-muted">Original</p>
                              <div className="mb-2 flex flex-wrap items-center gap-2">
                                <ConfidenceBadge confidence={e.confidence} />
                                <Tag>{e.category}</Tag>
                                <Tag>{e.language}</Tag>
                                <UrgencyBadge urgency={e.urgency} />
                              </div>
                              <div className="max-h-60 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-bg-card p-3 text-sm text-muted">
                                {e.body || '(empty body)'}
                              </div>
                            </div>
                            <div>
                              <p className="mb-1 text-xs uppercase tracking-wider text-muted">Suggested reply</p>
                              <div className="max-h-60 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border bg-bg-card p-3 text-sm text-text">
                                {e.suggested_reply || '(none)'}
                              </div>
                              {e.rejection_reason && (
                                <p className="mt-2 text-xs text-danger">
                                  Rejection reason: {e.rejection_reason}
                                </p>
                              )}
                              {e.reviewed_by && (
                                <p className="num mt-2 text-xs text-muted">
                                  Reviewed by {e.reviewed_by} · {fmtDate(e.reviewed_at)}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between text-sm">
            <p className="text-muted">
              <span className="num text-text">{filtered.length}</span> result(s) · page{' '}
              <span className="num text-text">{page}</span>/<span className="num">{totalPages}</span>
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:text-text disabled:opacity-40"
              >
                ← Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:text-text disabled:opacity-40"
              >
                Next →
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
