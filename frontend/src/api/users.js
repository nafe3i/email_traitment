import client from './client'

export const getUsers = () => client.get('/users')

// NOTE: the backend reads `role` as a query param on PATCH /users/{email}/role.
export const changeUserRole = (email, role) =>
  client.patch(`/users/${encodeURIComponent(email)}/role`, null, {
    params: { role },
  })

export const deleteUser = (email) =>
  client.delete(`/users/${encodeURIComponent(email)}`)
