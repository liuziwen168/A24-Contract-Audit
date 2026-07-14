 import http from './client'
 import type {
   ApiResponse,
   ReviewProgress,
   ReviewResult,
   ReviewListParams,
   PaginatedData,
   ReviewRecord,
 } from '@/types'

 export function createReview(
   contractId: number,
   contractFileId: number,
   reviewMode: string,
   idempotencyKey: string,
 ): Promise<ApiResponse<{ reviewId: number; reviewStatus: string; reviewStage: string; requestId: string }>> {
   return http
     .post(
       '/reviews',
       { contractId, contractFileId, reviewMode },
       { headers: { 'Idempotency-Key': idempotencyKey } },
     )
     .then((r) => r.data)
 }

 export function getReviewProgress(reviewId: number): Promise<ApiResponse<ReviewProgress>> {
   return http.get(`/reviews/${reviewId}/progress`).then((r) => r.data)
 }

 export function getReviewResult(reviewId: number): Promise<ApiResponse<ReviewResult>> {
   return http.get(`/reviews/${reviewId}`).then((r) => r.data)
 }

 export function getReviewHistory(params?: ReviewListParams): Promise<ApiResponse<PaginatedData<ReviewRecord>>> {
   return http.get('/reviews', { params }).then((r) => r.data)
 }

 export function patchContractType(reviewId: number, contractType: string, comment?: string): Promise<ApiResponse<any>> {
   return http.patch(`/reviews/${reviewId}/contract-type`, { contractType, comment }).then((r) => r.data)
 }

 export function patchElement(reviewId: number, elementId: number, value: string, comment?: string): Promise<ApiResponse<any>> {
   return http.patch(`/reviews/${reviewId}/elements/${elementId}`, { value, comment }).then((r) => r.data)
 }

 export function patchOverallRisk(reviewId: number, overallRiskLevel: string, overallScore: number, comment?: string): Promise<ApiResponse<any>> {
   return http.patch(`/reviews/${reviewId}/overall-risk`, { overallRiskLevel, overallScore, comment }).then((r) => r.data)
 }

 export function submitFeedback(
   reviewId: number,
   targetType: string,
   judgment: string,
   targetId?: number | null,
   correctedValue?: string,
   comment?: string,
 ): Promise<ApiResponse<{ feedbackId: number }>> {
   return http
     .post(`/reviews/${reviewId}/feedback`, { targetType, targetId, judgment, correctedValue, comment })
     .then((r) => r.data)
 }

 export function legalConfirm(reviewId: number, opinion?: string): Promise<ApiResponse<any>> {
   return http.post(`/reviews/${reviewId}/legal-confirm`, { opinion }).then((r) => r.data)
 }

 export function riskConfirm(reviewId: number, opinion?: string): Promise<ApiResponse<any>> {
   return http.post(`/reviews/${reviewId}/risk-confirm`, { opinion }).then((r) => r.data)
 }
