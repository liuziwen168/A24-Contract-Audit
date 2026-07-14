 import http from './client'
 import type { ApiResponse, DashboardSummary } from '@/types'

 export function getDashboardSummary(from?: string, to?: string): Promise<ApiResponse<DashboardSummary>> {
   return http.get('/dashboard/summary', { params: { from, to } }).then((r) => r.data)
 }
