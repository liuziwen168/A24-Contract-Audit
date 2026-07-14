 import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
 import { ElMessage } from 'element-plus'
 import { useAuthStore } from '@/stores/auth'
 import type { ApiResponse } from '@/types'

 const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

 const http: AxiosInstance = axios.create({
   baseURL: BASE_URL,
   timeout: 30000,
   headers: {
     'Content-Type': 'application/json',
   },
 })

 http.interceptors.request.use(
   (config: InternalAxiosRequestConfig) => {
     const token = localStorage.getItem('accessToken')
     if (token && config.headers) {
       config.headers['Authorization'] = `Bearer ${token}`
     }
     return config
   },
   (error) => Promise.reject(error),
 )

 http.interceptors.response.use(
   (response: AxiosResponse<ApiResponse>) => {
     const res = response.data
     if (res.code !== 'OK') {
       ElMessage.error(res.message || '请求失败')
       return Promise.reject(new Error(res.message || '请求失败'))
     }
     return response
   },
   (error) => {
     if (error.response) {
       const { status, data } = error.response
       if (status === 401) {
         localStorage.removeItem('accessToken')
         const authStore = useAuthStore()
         authStore.clearUser()
         window.location.href = '/login'
       } else if (status === 403) {
         ElMessage.error('权限不足，无法执行此操作')
       } else if (status === 409) {
         ElMessage.warning(data?.message || '操作冲突，请刷新后重试')
       } else if (status >= 500) {
         ElMessage.error('服务器错误，请联系管理员')
       }
     } else {
       ElMessage.error('网络错误，请检查连接')
     }
     return Promise.reject(error)
   },
 )

 export default http
