import { useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import StatCard from '../components/ui/StatCard'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import {
  StatusBadge,
  UrgencyBadge,
  ConfidenceBadge,
  Tag,
} from '../components/emails/StatusBadge'
import useEmailStore from '../store/useEmailStore'
import useAutoRefresh from '../hooks/useAutoRefresh'
import { useToast } from '../hooks/useToast'
import { errorMessage } from '../api/client'

export default function DashboardPage() {
  const emails = useEmailStore((s) => s.emails)
  const pending = useEmailStore((s) => s.pending)
  const fetchHistory = useEmailStore((s) => s.fetchHistory)
  const fetchPending = useEmailStore((s) => s.fetchPending)
  const run = useEmailStore((s) => s.run)
  const loading = useEmailStore((s) => s.loadingHistory)
  const { success, error } = useToast()
  const [running, setRunning] = useState(false)

  const refresh = useCallback(() => {
    fetchHistory().catch((e) => error(errorMessage(e, 'Failed to load emails')))
    fetchPending().catch(() => {})
  }, [fetchHistory, fetchPending, error])

  useAutoRefresh(refresh, 30000)

  const counts = {
    pending: emails.filter((e) => e.status === 'pending_review').length || pending.length,
    sent: emails.filter((e) => e.status === 'sent' || e.status === 'approved_no_gmail').length,
    rejected: emails.filter((e) => e.status === 'rejected').length,
    total: emails.length,
  }

  const recentPending = (pending.length ? pending : emails.filter((e) => e.status === 'pending_review')).slice(0, 5)

  const handleRun = async () => {
    setRunning(true)
    try {
      const res = await run()
      success(`Processed ${res?.processed ?? 0} email(s) from Gmail.`)
      refresh()
    } catch (e) {
      error(errorMessage(e, 'Failed to process Gmail'))
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted">Overview of the email support queue.</p>
        <button
          onClick={handleRun}
          disabled={running}
          className="inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg-primary transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {running ? <Spinner size={14} className="border-bg-primary/40 border-t-bg-primary" /> : '⟳'} Process Gmail
        </button>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Pending" value={counts.pending} accent="warning" icon="⏳" loading={loading} />
        <StatCard label="Sent" value={counts.sent} accent="success" icon="✅" loading={loading} />
        <StatCard label="Rejected" value={counts.rejected} accent="danger" icon="❌" loading={loading} />
        <StatCard label="Total" value={counts.total} accent="info" icon="✉️" loading={loading} />
      </div>

      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-heading text-lg font-bold text-text">Recent pending</h2>
          <Link to="/pending" className="text-sm font-medium text-info hover:text-accent">
            View all →
          </Link>
        </div>

        {loading && !recentPending.length ? (
          <div className="flex justify-center py-10">
            <Spinner size={28} />
          </div>
        ) : recentPending.length === 0 ? (
          <EmptyState
            title="No pending emails"
            subtitle="Everything has been reviewed. Process Gmail to fetch new messages."
            icon="🎉"
          />
        ) : (
          <div className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-bg-card">
            {recentPending.map((e) => (
              <Link
                key={e.id}
                to="/pending"
                className="flex items-center gap-3 px-4 py-3 transition-colors hover:bg-bg-secondary"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-text">{e.subject || '(no subject)'}</p>
                  <p className="num truncate text-xs text-muted">{e.sender}</p>
                </div>
                <div className="hidden items-center gap-2 sm:flex">
                  <UrgencyBadge urgency={e.urgency} />
                  <ConfidenceBadge confidence={e.confidence} />
                  <Tag>{e.category}</Tag>
                </div>
                <StatusBadge status={e.status} />
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
