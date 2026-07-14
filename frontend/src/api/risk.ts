 import http from './client'
 import type { ApiResponse, RiskRecord } from '@/types'

 export function getRiskDetail(riskId: number): Promise<ApiResponse<RiskRecord>> {
   return http.get(`/risks/${riskId}`).then((r) => r.data)
 }

 export function patchRisk(
   riskId: number,
   data: { riskLevel?: string; suggestion?: string; riskStatus?: string; comment?: string },
 ): Promise<ApiResponse<RiskRecord>> {
   return http.patch(`/risks/${riskId}`, data).then((r) => r.data)
 }
