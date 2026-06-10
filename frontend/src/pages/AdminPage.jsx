import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Spinner from '../components/ui/Spinner'
import EmptyState from '../components/ui/EmptyState'
import {
  StatusBadge,
  UrgencyBadge,
  ConfidenceBadge,
  Tag,
} from '../components/emails/StatusBadge'
import useAuthStore from '../store/useAuthStore'
import useAutoRefresh from '../hooks/useAutoRefresh'
import { useToast } from '../hooks/useToast'
import { errorMessage } from '../api/client'
import { getHealth, seedKnowledgeBase, resetAll } from '../api/system'
import { getUsers, changeUserRole, deleteUser } from '../api/users'
import { processEmail } from '../api/emails'

const ROLES = ['admin', 'user', 'viewer']

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString()
}

function Section({ title, danger, right, children }) {
  return (
    <section className="border-t border-border pt-6">
      <div className="mb-4 flex items-center justify-between gap-3">
        <h2 className={`font-heading text-lg font-bold ${danger ? 'text-danger' : 'text-text'}`}>
          {title}
        </h2>
        {right}
      </div>
      {children}
    </section>
  )
}

function StatusCard({ icon, label, value, sub, accent = 'text-text' }) {
  return (
    <div className="rounded-xl border border-border bg-bg-card p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wider text-muted">{label}</p>
        <span className="text-lg opacity-70">{icon}</span>
      </div>
      <p className={`num mt-3 text-2xl font-medium ${accent}`}>{value}</p>
      {sub && <p className="num mt-1 truncate text-xs text-muted">{sub}</p>}
    </div>
  )
}

export default function AdminPage() {
  const currentUser = useAuthStore((s) => s.user)
  const { success, error } = useToast()

  // ── Section 1: System status ──────────────────────────────
  const [health, setHealth] = useState(null)
  const [healthLoading, setHealthLoading] = useState(true)

  const loadHealth = useCallback(async () => {
    try {
      const { data } = await getHealth()
      setHealth(data)
    } catch (e) {
      error(errorMessage(e, 'Failed to load system status'))
    } finally {
      setHealthLoading(false)
    }
  }, [error])

  useAutoRefresh(loadHealth, 30000)

  const docCount = health?.chroma?.documents ?? 0

  // ── Section 2: Knowledge base ─────────────────────────────
  const [seeding, setSeeding] = useState(false)
  const handleSeed = async (force) => {
    setSeeding(true)
    try {
      const { data } = await seedKnowledgeBase(force)
      success(
        force
          ? 'Knowledge base reloaded'
          : `Knowledge base loaded — ${data?.documents_loaded ?? docCount} documents`,
      )
      loadHealth()
    } catch (e) {
      error(errorMessage(e, 'Failed to load knowledge base'))
    } finally {
      setSeeding(false)
    }
  }

  // ── Section 3: Test email ─────────────────────────────────
  const [form, setForm] = useState({ sender: '', subject: '', body: '' })
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState(null)

  const handleProcess = async (e) => {
    e.preventDefault()
    setProcessing(true)
    setResult(null)
    try {
      const email = await processEmail(form.subject, form.body, form.sender)
      setResult(email)
      success(`Email processed — status: ${email.status}`)
    } catch (err) {
      error(errorMessage(err, 'Failed to process email'))
    } finally {
      setProcessing(false)
    }
  }

  // ── Section 4: User management ────────────────────────────
  const [users, setUsers] = useState([])
  const [usersLoading, setUsersLoading] = useState(true)
  const [rowBusy, setRowBusy] = useState(null)

  const loadUsers = useCallback(async () => {
    setUsersLoading(true)
    try {
      const { data } = await getUsers()
      setUsers(Array.isArray(data) ? data : data?.users || [])
    } catch (e) {
      error(errorMessage(e, 'Failed to load users'))
    } finally {
      setUsersLoading(false)
    }
  }, [error])

  useEffect(() => {
    loadUsers()
  }, [loadUsers])

  const handleRoleChange = async (email, role) => {
    setRowBusy(email)
    try {
      await changeUserRole(email, role)
      setUsers((list) => list.map((u) => (u.email === email ? { ...u, role } : u)))
      success('Role updated')
    } catch (e) {
      error(errorMessage(e, 'Failed to update role'))
    } finally {
      setRowBusy(null)
    }
  }

  const handleDelete = async (email) => {
    if (!window.confirm(`Delete user ${email}?`)) return
    setRowBusy(email)
    try {
      await deleteUser(email)
      setUsers((list) => list.filter((u) => u.email !== email))
      success('User deleted')
    } catch (e) {
      error(errorMessage(e, 'Failed to delete user'))
    } finally {
      setRowBusy(null)
    }
  }

  // ── Section 5: Danger zone ────────────────────────────────
  const [resetOpen, setResetOpen] = useState(false)
  const [resetting, setResetting] = useState(false)
  const handleReset = async () => {
    setResetting(true)
    try {
      await resetAll()
      success('System reset complete')
      setResetOpen(false)
      loadHealth()
    } catch (e) {
      error(errorMessage(e, 'Failed to reset system'))
    } finally {
      setResetting(false)
    }
  }

  const inputCls =
    'w-full rounded-lg border border-border bg-bg-secondary px-3 py-2.5 text-sm text-text outline-none focus:border-accent'
  const primaryBtn =
    'inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-bg-primary transition-opacity hover:opacity-90 disabled:opacity-50'
  const ghostBtn =
    'inline-flex items-center justify-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-muted transition-colors hover:text-text disabled:opacity-50'

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-heading text-2xl font-bold text-text">Administration</h1>
        <p className="text-sm text-muted">System management</p>
      </div>

      {/* Section 1 — System status */}
      <Section title="System Status">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatusCard
            icon="🤖"
            label="Ollama"
            value={healthLoading ? '…' : health?.ollama ? 'Online' : 'Offline'}
            accent={health?.ollama ? 'text-success' : 'text-danger'}
          />
          <StatusCard
            icon="🗄"
            label="ChromaDB"
            value={healthLoading ? '…' : docCount}
            sub={health?.chroma?.collection}
            accent={docCount > 0 ? 'text-success' : 'text-warning'}
          />
          <StatusCard
            icon="📄"
            label="Storage"
            value={healthLoading ? '…' : health?.storage?.total ?? 0}
            sub={health?.storage?.path}
            accent="text-info"
          />
        </div>
      </Section>

      {/* Section 2 — Knowledge base */}
      <Section title="Knowledge Base">
        <div className="rounded-xl border border-border bg-bg-card p-5">
          <p className="text-sm text-muted">
            Current documents: <span className="num text-text">{docCount}</span>
          </p>
          <div className="mt-4 flex flex-wrap gap-3">
            <button onClick={() => handleSeed(false)} disabled={seeding} className={primaryBtn}>
              {seeding && <Spinner size={14} className="border-bg-primary/40 border-t-bg-primary" />}
              Load Knowledge Base
            </button>
            <button onClick={() => handleSeed(true)} disabled={seeding} className={ghostBtn}>
              {seeding && <Spinner size={14} />}
              Force Reload
            </button>
          </div>
        </div>
      </Section>

      {/* Section 3 — Test email */}
      <Section title="Test Email Processing">
        <div className="rounded-xl border border-border bg-bg-card p-5">
          <form onSubmit={handleProcess} className="space-y-3">
            <input
              className={inputCls}
              placeholder="etudiant@aui.ma"
              value={form.sender}
              onChange={(e) => setForm({ ...form, sender: e.target.value })}
            />
            <input
              className={inputCls}
              placeholder="Probleme inscription"
              value={form.subject}
              onChange={(e) => setForm({ ...form, subject: e.target.value })}
            />
            <textarea
              className={inputCls}
              rows={4}
              placeholder="Describe the issue..."
              value={form.body}
              onChange={(e) => setForm({ ...form, body: e.target.value })}
            />
            <button type="submit" disabled={processing} className={primaryBtn}>
              {processing && <Spinner size={14} className="border-bg-primary/40 border-t-bg-primary" />}
              Process &amp; Preview
            </button>
          </form>

          {result && (
            <div className="mt-5 rounded-lg border border-border bg-bg-secondary p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <Tag>{result.category}</Tag>
                <Tag>{result.language}</Tag>
                <UrgencyBadge urgency={result.urgency} />
                <ConfidenceBadge confidence={result.confidence} />
                <StatusBadge status={result.status} />
              </div>
              {result.suggested_reply && (
                <textarea
                  readOnly
                  rows={8}
                  value={result.suggested_reply}
                  className="w-full resize-y rounded-lg border border-border bg-bg-card p-3 text-sm text-text outline-none"
                />
              )}
              {result.status === 'pending_review' && (
                <Link to="/pending" className="mt-3 inline-block text-sm font-medium text-info hover:text-accent">
                  View in Pending →
                </Link>
              )}
            </div>
          )}
        </div>
      </Section>

      {/* Section 4 — User management */}
      <Section title="User Management">
        {usersLoading ? (
          <div className="flex justify-center py-10">
            <Spinner size={28} />
          </div>
        ) : users.length === 0 ? (
          <EmptyState title="No users" subtitle="No accounts found." icon="👥" />
        ) : (
          <div className="overflow-hidden rounded-xl border border-border bg-bg-card">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border text-xs uppercase tracking-wider text-muted">
                <tr>
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="hidden px-4 py-3 font-medium sm:table-cell">Joined</th>
                  <th className="px-4 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {users.map((u) => {
                  const isSelf = u.email === currentUser?.email
                  return (
                    <tr key={u.email}>
                      <td className="num px-4 py-3 text-text">{u.email}</td>
                      <td className="px-4 py-3">
                        <select
                          value={u.role}
                          disabled={isSelf || rowBusy === u.email}
                          onChange={(e) => handleRoleChange(u.email, e.target.value)}
                          className="num rounded-lg border border-border bg-bg-secondary px-2 py-1.5 text-xs text-text outline-none focus:border-accent disabled:opacity-50"
                        >
                          {ROLES.map((r) => (
                            <option key={r} value={r}>{r}</option>
                          ))}
                        </select>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`num text-xs font-medium ${u.is_active ? 'text-success' : 'text-danger'}`}>
                          {u.is_active ? 'Active' : 'Disabled'}
                        </span>
                      </td>
                      <td className="num hidden px-4 py-3 text-xs text-muted sm:table-cell">
                        {fmtDate(u.created_at)}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => handleDelete(u.email)}
                          disabled={isSelf || rowBusy === u.email}
                          title={isSelf ? 'You cannot delete your own account' : 'Delete user'}
                          className="rounded-lg border border-border p-1.5 text-muted transition-colors hover:border-danger/40 hover:text-danger disabled:opacity-40"
                        >
                          🗑
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      {/* Section 5 — Danger zone */}
      <Section title="Danger Zone" danger>
        <div className="rounded-xl border border-danger/40 bg-danger/5 p-5">
          <p className="text-sm text-muted">
            Reset all processed emails and system state. Knowledge base and users are preserved.
          </p>
          <button
            onClick={() => setResetOpen(true)}
            className="mt-4 inline-flex items-center gap-2 rounded-lg bg-danger px-4 py-2 text-sm font-semibold text-bg-primary transition-opacity hover:opacity-90"
          >
            Reset All Data
          </button>
        </div>
      </Section>

      {/* Reset confirmation modal */}
      {resetOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div className="w-full max-w-md rounded-2xl border border-border bg-bg-card p-6">
            <h3 className="font-heading text-lg font-bold text-danger">Reset All Data?</h3>
            <p className="mt-2 text-sm text-muted">
              This will delete all processed emails and reset the system. Knowledge base and users
              will be preserved. This action cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setResetOpen(false)} disabled={resetting} className={ghostBtn}>
                Cancel
              </button>
              <button
                onClick={handleReset}
                disabled={resetting}
                className="inline-flex items-center gap-2 rounded-lg bg-danger px-4 py-2 text-sm font-semibold text-bg-primary transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {resetting && <Spinner size={14} className="border-bg-primary/40 border-t-bg-primary" />}
                Yes, Reset
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
