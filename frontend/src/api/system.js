import client from './client'

export const getHealth = () => client.get('/health')

// NOTE: this backend's POST /seed reads `reset_first`. We send both keys so the
// flag works whether the API expects `reset_first` (current) or `force_reload`.
export const seedKnowledgeBase = (force = false) =>
  client.post('/seed', { reset_first: force, force_reload: force })

export const resetAll = () => client.delete('/reset')
