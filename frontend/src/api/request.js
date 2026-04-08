import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { getToken, getRefreshToken, setToken, setRefreshToken, clearTokens } from '@/utils/auth'

const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

request.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

let isRefreshing = false
let pendingRequests = []

request.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(request(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const refreshToken = getRefreshToken()
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post('/api/auth/refresh', {
          refresh_token: refreshToken,
        })

        setToken(data.access_token)
        setRefreshToken(data.refresh_token)

        pendingRequests.forEach((cb) => cb(data.access_token))
        pendingRequests = []

        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        return request(originalRequest)
      } catch {
        clearTokens()
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    const message = error.response?.data?.detail || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default request
