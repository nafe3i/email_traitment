import { create } from 'zustand'
import { TOKEN_KEY } from '../api/client'
import * as authApi from '../api/auth'

const useAuthStore = create((set, get) => ({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: null,
  loading: false,
  initialized: false,

  isAuthenticated: () => !!get().token,

  async login(email, password) {
    const { access_token } = await authApi.login(email, password)
    localStorage.setItem(TOKEN_KEY, access_token)
    set({ token: access_token })
    const user = await authApi.getMe()
    set({ user })
    return user
  },

  // Load the current user when a token already exists (e.g. on refresh).
  async fetchMe() {
    if (!get().token) {
      set({ initialized: true })
      return null
    }
    set({ loading: true })
    try {
      const user = await authApi.getMe()
      set({ user })
      return user
    } catch {
      // token invalid/expired — clear it
      localStorage.removeItem(TOKEN_KEY)
      set({ token: null, user: null })
      return null
    } finally {
      set({ loading: false, initialized: true })
    }
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY)
    set({ token: null, user: null })
  },
}))

export default useAuthStore
