import request from './request'
import type { LoginRequest, LoginResponse, UserInfo, ApiResponse } from '@/types'

// 用户登录
export function loginApi(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
  return request.post('/auth/login', data)
}

// 获取当前用户信息
export function getCurrentUserApi(): Promise<ApiResponse<UserInfo>> {
  return request.get('/users/me')
}

// 退出登录（清理本地）
export function logoutApi(): void {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('userInfo')
}
