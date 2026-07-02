import api from './index'

export const login = (username, password) => {
  return api.post('/app/auth/admin/login', { username, password })
}
