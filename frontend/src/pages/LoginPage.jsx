import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import useAuthStore from '../store/useAuthStore'
import { errorMessage } from '../api/client'
import Spinner from '../components/ui/Spinner'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const login = useAuthStore((s) => s.login)
  const token = useAuthStore((s) => s.token)
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from?.pathname || '/dashboard'

  if (token) return <Navigate to={from} replace />

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(errorMessage(err, 'Login failed. Check your credentials.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-primary px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-accent text-bg-primary">
            <span className="font-heading text-2xl font-bold">A</span>
          </span>
          <h1 className="font-heading text-2xl font-bold text-text">AUI Email Support</h1>
          <p className="mt-1 text-sm text-muted">Al Akhawayn University · Ifrane</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="space-y-4 rounded-2xl border border-border bg-bg-card p-6"
        >
          {error && (
            <div className="rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}

          <div>
            <label className="mb-1 block text-xs uppercase tracking-wider text-muted">
              Email
            </label>
            <input
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@aui.ma"
              className="num w-full rounded-lg border border-border bg-bg-secondary px-3 py-2.5 text-sm text-text outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs uppercase tracking-wider text-muted">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-lg border border-border bg-bg-secondary px-3 py-2.5 text-sm text-text outline-none focus:border-accent"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-2.5 text-sm font-semibold text-bg-primary transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading && <Spinner size={16} className="border-bg-primary/40 border-t-bg-primary" />}
            Sign in
          </button>
        </form>
      </div>
    </div>
  )
}
