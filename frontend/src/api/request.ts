import axios from 'axios'
import type { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    // 文件下载直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    if (res.code !== 'OK') {
      ElMessage.error(res.message || '请求失败')
      // Token 失效跳转登录
      if (res.code === 'AUTH_TOKEN_INVALID' || res.code === 'AUTH_TOKEN_MISSING') {
        localStorage.removeItem('accessToken')
        localStorage.removeItem('userInfo')
        router.push('/login')
      }
      return Promise.reject(new Error(res.message))
    }
    return res
  },
  (error) => {
    // 409 REVIEW_RESULT_NOT_READY 由页面自行处理，不弹 toast
    if (error.response?.status === 409 && error.response?.data?.code === 'REVIEW_RESULT_NOT_READY') {
      return Promise.reject(error)
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('accessToken')
      localStorage.removeItem('userInfo')
      router.push('/login')
      ElMessage.error('登录凭证已过期，请重新登录')
    } else if (error.response?.status === 403) {
      ElMessage.error('无权限访问该资源')
    } else {
      // 后端会在 4xx/5xx 响应中返回业务错误码和中文消息；优先展示它，
      // 避免用户只看到 Axios 的“Request failed with status code 400”。
      ElMessage.error(error.response?.data?.message || error.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
