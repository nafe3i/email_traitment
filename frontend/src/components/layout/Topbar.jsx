import { useNavigate } from 'react-router-dom'
import useAuthStore from '../../store/useAuthStore'

export default function Topbar({ onMenuClick, title }) {
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-border bg-bg-primary/80 px-4 py-3 backdrop-blur lg:px-6">
      <button
        onClick={onMenuClick}
        className="rounded-lg border border-border p-2 text-muted hover:text-text lg:hidden"
        aria-label="Open menu"
      >
        ☰
      </button>

      <h1 className="font-heading text-lg font-bold text-text">{title}</h1>

      <div className="ml-auto flex items-center gap-3">
        {user && (
          <div className="hidden text-right sm:block">
            <p className="num text-xs text-text">{user.email}</p>
            <p className="text-[11px] uppercase tracking-wide text-accent">{user.role}</p>
          </div>
        )}
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-bg-card text-sm font-semibold text-accent">
          {(user?.email || '?').charAt(0).toUpperCase()}
        </div>
        <button
          onClick={handleLogout}
          className="rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-muted transition-colors hover:border-danger/40 hover:text-danger"
        >
          Logout
        </button>
      </div>
    </header>
  )
}
