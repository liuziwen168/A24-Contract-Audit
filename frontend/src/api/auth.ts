 import http from './client'
import type { ApiResponse, LoginRequest, LoginResponse, User } from '@/types'

export function login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
  return http.post('/auth/login', data).then((r) => r.data)
}

export function getCurrentUser(): Promise<ApiResponse<User>> {
  return http.get('/users/me').then((r) => r.data)
}
