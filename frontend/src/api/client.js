import axios from 'axios'

export const TOKEN_KEY = 'aui_token'

const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({
  baseURL,
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT from localStorage to every request.
client.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Allow the app to register a handler that runs on 401 responses
// (logout + redirect to login). Set from the auth store.
let unauthorizedHandler = null
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler
}

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (unauthorizedHandler) unauthorizedHandler()
    }
    return Promise.reject(error)
  },
)

// Normalize an axios error into a human-readable message.
export function errorMessage(error, fallback = 'Something went wrong') {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join(', ')
  }
  if (error?.message) return error.message
  return fallback
}

export default client
