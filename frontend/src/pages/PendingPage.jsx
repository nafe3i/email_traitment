import { useCallback } from 'react'
import EmailList from '../components/emails/EmailList'
import EmptyState from '../components/ui/EmptyState'
import Spinner from '../components/ui/Spinner'
import useEmailStore from '../store/useEmailStore'
import useAutoRefresh from '../hooks/useAutoRefresh'
import { useToast } from '../hooks/useToast'
import { errorMessage } from '../api/client'

export default function PendingPage() {
  const pending = useEmailStore((s) => s.pending)
  const fetchPending = useEmailStore((s) => s.fetchPending)
  const approve = useEmailStore((s) => s.approve)
  const reject = useEmailStore((s) => s.reject)
  const loading = useEmailStore((s) => s.loadingPending)
  const { success, error } = useToast()

  const refresh = useCallback(() => {
    fetchPending().catch((e) => error(errorMessage(e, 'Failed to load pending emails')))
  }, [fetchPending, error])

  useAutoRefresh(refresh, 30000)

  const handleApprove = async (id) => {
    try {
      const res = await approve(id)
      success(`Email approved — ${res?.status || 'sent'}.`)
    } catch (e) {
      error(errorMessage(e, 'Failed to approve email'))
      refresh()
    }
  }

  const handleReject = async (id, reason) => {
    try {
      await reject(id, reason)
      success('Email rejected.')
    } catch (e) {
      error(errorMessage(e, 'Failed to reject email'))
      refresh()
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">
          <span className="num text-text">{pending.length}</span> email(s) awaiting validation. Auto-refreshes every 30s.
        </p>
        <button
          onClick={refresh}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted hover:text-text"
        >
          ⟳ Refresh
        </button>
      </div>

      {loading && pending.length === 0 ? (
        <div className="flex justify-center py-16">
          <Spinner size={32} />
        </div>
      ) : pending.length === 0 ? (
        <EmptyState
          title="No pending emails"
          subtitle="All caught up! New emails will appear here once processed."
          icon="📭"
        />
      ) : (
        <EmailList emails={pending} onApprove={handleApprove} onReject={handleReject} />
      )}
    </div>
  )
}
