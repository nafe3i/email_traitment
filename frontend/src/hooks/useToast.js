import { create } from 'zustand'

let idCounter = 0

// Global toast store so any component (or API layer) can raise notifications.
const useToastStore = create((set, get) => ({
  toasts: [],

  push(message, type = 'info', duration = 4000) {
    const id = ++idCounter
    set({ toasts: [...get().toasts, { id, message, type }] })
    if (duration > 0) {
      setTimeout(() => get().dismiss(id), duration)
    }
    return id
  },

  dismiss(id) {
    set({ toasts: get().toasts.filter((t) => t.id !== id) })
  },
}))

// Hook exposing convenient helpers.
export function useToast() {
  const push = useToastStore((s) => s.push)
  return {
    toast: push,
    success: (msg, d) => push(msg, 'success', d),
    error: (msg, d) => push(msg, 'error', d),
    info: (msg, d) => push(msg, 'info', d),
    warning: (msg, d) => push(msg, 'warning', d),
  }
}

export default useToastStore
