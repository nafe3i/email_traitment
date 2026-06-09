import client from './client'

export async function login(email, password) {
  const { data } = await client.post('/auth/login', { email, password })
  return data // { access_token, token_type }
}

export async function getMe() {
  const { data } = await client.get('/auth/me')
  return data // { email, role }
}
