import { useEffect } from 'react'
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import useAuthStore from './store/useAuthStore'
import { setUnauthorizedHandler } from './api/client'
import { useToast } from './hooks/useToast'
import AppLayout from './components/layout/AppLayout'
import Toast from './components/ui/Toast'
import Spinner from './components/ui/Spinner'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import PendingPage from './pages/PendingPage'
import HistoryPage from './pages/HistoryPage'
import StatsPage from './pages/StatsPage'
import AdminPage from './pages/AdminPage'

function ProtectedRoute({ children }) {
  const token = useAuthStore((s) => s.token)
  const location = useLocation()
  if (!token) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }
  return children
}

// Admin-only guard: redirects non-admins to the dashboard.
function AdminRoute({ children }) {
  const user = useAuthStore((s) => s.user)
  if (user && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />
  }
  return children
}

export default function App() {
  const token = useAuthStore((s) => s.token)
  const initialized = useAuthStore((s) => s.initialized)
  const fetchMe = useAuthStore((s) => s.fetchMe)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()
  const { warning } = useToast()

  // Register a global 401 handler: logout + redirect to login.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (useAuthStore.getState().token) {
        logout()
        warning('Session expired. Please sign in again.')
        navigate('/login', { replace: true })
      }
    })
  }, [logout, navigate, warning])

  // On first load, resolve the current user from an existing token.
  useEffect(() => {
    fetchMe()
  }, [fetchMe])

  if (token && !initialized) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg-primary">
        <Spinner size={36} />
      </div>
    )
  }

  return (
    <>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/pending" element={<PendingPage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route
            path="/admin"
            element={
              <AdminRoute>
                <AdminPage />
              </AdminRoute>
            }
          />
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
      <Toast />
    </>
  )
}
