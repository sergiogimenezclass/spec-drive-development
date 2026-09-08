import { defineStore } from 'pinia'
import { api } from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('access_token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null'),
  }),
  getters: {
    isAuthenticated: (s) => !!s.token,
  },
  actions: {
    _persist(token, user, refresh) {
      this.token = token
      this.user = user
      if (token) localStorage.setItem('access_token', token)
      if (user) localStorage.setItem('user', JSON.stringify(user))
      if (refresh) localStorage.setItem('refresh_token', refresh)
    },
    async register(payload) {
      const data = await api.post('/auth/register', payload)
      this._persist(data.access_token, data.user, data.refresh_token)
      return data
    },
    async login(email, password) {
      const data = await api.post('/auth/login', { email, password })
      this._persist(data.access_token, data.user, data.refresh_token)
      return data
    },
    async fetchProfile() {
      const user = await api.get('/professional', { auth: true })
      this._persist(this.token, user)
      return user
    },
    logout() {
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        api.post('/auth/logout', { refresh_token: refresh }, { auth: true }).catch(() => {})
      }
      this.token = null
      this.user = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },
  },
})
