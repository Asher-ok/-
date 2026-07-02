import { defineStore } from 'pinia'
import { login } from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: null
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.token
  },
  
  actions: {
    async login(username, password) {
      try {
        const response = await login(username, password)
        this.token = response.access_token
        localStorage.setItem('token', this.token)
        return response
      } catch (error) {
        throw error
      }
    },
    
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    }
  }
})
