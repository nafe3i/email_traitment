import client from './client'

export async function getStats() {
  const { data } = await client.get('/stats')
  return {
    by_category: data?.by_category || {},
    by_language: data?.by_language || {},
    by_urgency: data?.by_urgency || {},
    total: data?.total ?? 0,
    sent: data?.sent ?? 0,
  }
}

export async function getHealth() {
  const { data } = await client.get('/health')
  return data
}
