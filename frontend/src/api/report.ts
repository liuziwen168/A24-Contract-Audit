 import http from './client'
 import type { ApiResponse } from '@/types'

 export function generateReport(reviewId: number, reportFormat: string): Promise<ApiResponse<{ reportId: number; reportStatus: string }>> {
   return http.post(`/reviews/${reviewId}/reports`, { reportFormat }).then((r) => r.data)
 }

 export function downloadReport(reportId: number): Promise<Blob> {
   return http.get(`/reports/${reportId}/download`, { responseType: 'blob' }).then((r) => r.data)
 }
