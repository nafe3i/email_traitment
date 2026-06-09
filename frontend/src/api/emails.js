import client from './client'

// The backend may return language/urgency nested under `detection` and may
// wrap list responses in an object. Normalize to the flat Email shape the UI
// expects so the dashboard works regardless of which variant the API returns.
export function normalizeEmail(raw) {
  if (!raw || typeof raw !== 'object') return raw
  const detection = raw.detection || {}
  return {
    ...raw,
    language: raw.language ?? detection.language ?? null,
    urgency: raw.urgency ?? detection.urgency ?? null,
    sender: raw.sender ?? detection.sender ?? raw.from ?? '',
  }
}

function toList(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.emails)) return data.emails
  if (Array.isArray(data?.pending)) return data.pending
  return []
}

export async function getHistory() {
  const { data } = await client.get('/emails/history', { params: { limit: 500 } })
  return toList(data).map(normalizeEmail)
}

export async function getPending() {
  const { data } = await client.get('/emails/pending')
  return toList(data).map(normalizeEmail)
}

export async function approveEmail(id) {
  const { data } = await client.post(`/emails/${id}/approve`)
  return data
}

export async function rejectEmail(id, reason) {
  const { data } = await client.post(`/emails/${id}/reject`, null, {
    params: { reason },
  })
  return data
}

export async function runGmail() {
  const { data } = await client.post('/emails/run')
  return data // { processed }
}

export async function processEmail(payload) {
  // payload: { subject, body, sender }
  const { data } = await client.post('/emails/process', payload)
  return normalizeEmail(data)
}
