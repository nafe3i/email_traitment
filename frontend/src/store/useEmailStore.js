import { create } from 'zustand'
import * as emailsApi from '../api/emails'

const useEmailStore = create((set, get) => ({
  emails: [],
  pending: [],
  loadingHistory: false,
  loadingPending: false,
  error: null,

  async fetchHistory() {
    set({ loadingHistory: true, error: null })
    try {
      const emails = await emailsApi.getHistory()
      set({ emails })
      return emails
    } catch (e) {
      set({ error: e })
      throw e
    } finally {
      set({ loadingHistory: false })
    }
  },

  async fetchPending() {
    set({ loadingPending: true, error: null })
    try {
      const pending = await emailsApi.getPending()
      set({ pending })
      return pending
    } catch (e) {
      set({ error: e })
      throw e
    } finally {
      set({ loadingPending: false })
    }
  },

  async approve(id) {
    const res = await emailsApi.approveEmail(id)
    // Optimistically drop from pending list.
    set({ pending: get().pending.filter((e) => e.id !== id) })
    return res
  },

  async reject(id, reason) {
    const res = await emailsApi.rejectEmail(id, reason)
    set({ pending: get().pending.filter((e) => e.id !== id) })
    return res
  },

  // Update an email's suggested_reply locally (used by the reply editor).
  setReply(id, reply) {
    set({
      pending: get().pending.map((e) =>
        e.id === id ? { ...e, suggested_reply: reply } : e,
      ),
    })
  },

  async run() {
    return emailsApi.runGmail()
  },
}))

export default useEmailStore
