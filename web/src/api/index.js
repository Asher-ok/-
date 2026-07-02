import axios from 'axios'
import router from '@/router'

const inferBaseURL = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl) return envUrl
  if (import.meta.env.DEV) return '/api'
  const appBase = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
  return `${appBase}/api`
}

const api = axios.create({
  baseURL: inferBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 重试配置
const MAX_RETRIES = 2
const RETRY_DELAY = 1000 // 1秒

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // 如果是FormData，必须删除Content-Type头，让浏览器自动设置multipart/form-data的boundary
    // 这对于VPN环境特别重要，因为手动设置Content-Type（没有boundary）会导致请求失败
    if (config.data instanceof FormData) {
      // 确保删除所有可能的 Content-Type 设置（包括在 headers 对象中设置的）
      if (config.headers) {
        delete config.headers['Content-Type']
        delete config.headers['content-type']
      }
      // VPN环境下文件上传需要更长的超时时间（增加到180秒）
      // 因为VPN可能导致网络延迟和传输速度变慢
      if (!config.timeout || config.timeout < 180000) {
        config.timeout = 180000
      }
      
      // 添加请求日志（仅在开发环境）
      if (import.meta.env.DEV) {
        console.log('文件上传请求:', {
          url: config.url,
          method: config.method,
          timeout: config.timeout,
          fileSize: config.data instanceof FormData ? 'FormData' : 'unknown'
        })
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    // 对于blob类型，直接返回response，因为response.data已经是blob
    if (response.config.responseType === 'blob') {
      return response.data
    }
    return response.data
  },
  async error => {
    const config = error.config
    if (!config) {
      return Promise.reject(error)
    }

    const trySwitchBaseURL = () => {
      const url = config.url || ''
      if (!url.startsWith('/houtai/') && !url.startsWith('/app/') && !url.startsWith('/guanwang/')) {
        return null
      }
      const base = config.baseURL || api.defaults.baseURL || ''
      const appBase = (import.meta.env.BASE_URL || '/').replace(/\/$/, '')
      if (base.endsWith('/admin/api')) {
        return '/api'
      }
      if (base === '/api' && appBase && appBase !== '/' && !appBase.endsWith('/admin')) {
        return `${appBase}/api`
      }
      if (base === '/api' && appBase && appBase !== '/' && appBase.endsWith('/admin')) {
        return `${appBase}/api`
      }
      if (base.endsWith('/api') && base.includes('/admin/api')) {
        return '/api'
      }
      return null
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (router.currentRoute.value.path !== '/login') {
        router.push('/login')
      }
      return Promise.reject(error)
    }

    if (error.response?.status === 404 && !config.__baseURLSwitched) {
      const altBase = trySwitchBaseURL()
      if (altBase && altBase !== (config.baseURL || api.defaults.baseURL)) {
        config.__baseURLSwitched = true
        config.baseURL = altBase
        return api(config)
      }
    }

    // 对于网络错误或超时，进行重试
    if (!config.retry) {
      config.retry = 0
    }
    
    // 只对网络错误或超时进行重试，且重试次数未超过限制
    // 对于文件上传，在VPN环境下可能需要更多重试
    const isFileUpload = config.data instanceof FormData
    const maxRetries = isFileUpload ? MAX_RETRIES + 1 : MAX_RETRIES // 文件上传多一次重试机会
    
    const shouldRetry = (
      !error.response && // 网络错误
      config.retry < maxRetries &&
      (error.code === 'ECONNABORTED' || error.message.includes('timeout') || error.message.includes('Network Error'))
    )
    
    if (shouldRetry) {
      config.retry += 1
      // 等待后重试，文件上传等待时间稍长
      const delay = isFileUpload ? RETRY_DELAY * config.retry * 2 : RETRY_DELAY * config.retry
      console.log(`请求失败，${delay}ms后进行第${config.retry}次重试...`)
      await new Promise(resolve => setTimeout(resolve, delay))
      return api(config)
    }
    
    // 改进错误消息，特别是VPN相关的问题
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      error.message = '请求超时，请检查网络连接。如果使用VPN，请尝试切换节点或检查VPN连接'
    } else if (error.message.includes('Network Error') || !error.response) {
      error.message = '网络连接失败，请检查网络设置。如果使用VPN，请确保VPN连接正常'
    }
    
    // 对于500错误，如果错误消息是"数据库操作失败"，不在这里显示
    // 让具体的组件来处理错误消息的显示
    return Promise.reject(error)
  }
)

export default api
