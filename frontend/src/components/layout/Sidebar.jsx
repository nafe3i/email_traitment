import { NavLink } from 'react-router-dom'
import useAuthStore from '../../store/useAuthStore'

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '▦' },
  { to: '/pending', label: 'Pending', icon: '⏳' },
  { to: '/history', label: 'History', icon: '🗂' },
  { to: '/stats', label: 'Stats', icon: '📊' },
]

export default function Sidebar({ open, onClose }) {
  const user = useAuthStore((s) => s.user)
  const nav =
    user?.role === 'admin'
      ? [...NAV, { to: '/admin', label: 'Admin', icon: '🛡' }]
      : NAV

  return (
    <>
      {/* Mobile backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={onClose}
          aria-hidden
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-border bg-bg-secondary transition-transform duration-200 lg:static lg:translate-x-0 ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent text-bg-primary">
            <span className="font-heading text-lg font-bold">A</span>
          </span>
          <div className="leading-tight">
            <p className="font-heading text-sm font-bold text-text">AUI Support</p>
            <p className="text-[11px] text-muted">Email System</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-accent/10 text-accent'
                    : 'text-muted hover:bg-bg-card hover:text-text'
                }`
              }
            >
              <span className="w-5 text-center text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-border px-5 py-4">
          <p className="text-[11px] text-muted">AUI · Ifrane, Maroc</p>
        </div>
      </aside>
    </>
  )
}
