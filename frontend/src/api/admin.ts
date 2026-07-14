 import http from './client'
 import type {
   ApiResponse,
   User,
   PaginatedData,
   StandardClause,
   RiskRule,
   ReviewFeedback,
   OperationLog,
   PaginationParams,
 } from '@/types'

 // ============== User Management ==============
 export function getUserList(params?: PaginationParams & { role?: string }): Promise<ApiResponse<PaginatedData<User>>> {
   return http.get('/users', { params }).then((r) => r.data)
 }

 export function createUser(data: { username: string; password: string; role: string }): Promise<ApiResponse<User>> {
   return http.post('/users', data).then((r) => r.data)
 }

 export function updateUserStatus(userId: number, userStatus: string): Promise<ApiResponse<User>> {
   return http.patch(`/users/${userId}`, { userStatus }).then((r) => r.data)
 }

 // ============== Standard Clauses ==============
 export function getStandardClauseList(params?: PaginationParams & { contractType?: string }): Promise<ApiResponse<PaginatedData<StandardClause>>> {
   return http.get('/standard-clauses', { params }).then((r) => r.data)
 }

 export function createStandardClause(data: Partial<StandardClause>): Promise<ApiResponse<StandardClause>> {
   return http.post('/standard-clauses', data).then((r) => r.data)
 }

 export function updateStandardClause(clauseId: number, data: Partial<StandardClause>): Promise<ApiResponse<StandardClause>> {
   return http.patch(`/standard-clauses/${clauseId}`, data).then((r) => r.data)
 }

 // ============== Risk Rules ==============
 export function getRiskRuleList(params?: PaginationParams & { riskType?: string }): Promise<ApiResponse<PaginatedData<RiskRule>>> {
   return http.get('/risk-rules', { params }).then((r) => r.data)
 }

 export function createRiskRule(data: Partial<RiskRule>): Promise<ApiResponse<RiskRule>> {
   return http.post('/risk-rules', data).then((r) => r.data)
 }

 export function updateRiskRule(ruleId: number, data: Partial<RiskRule>): Promise<ApiResponse<RiskRule>> {
   return http.patch(`/risk-rules/${ruleId}`, data).then((r) => r.data)
 }

 // ============== Feedback ==============
 export function getFeedbackList(params?: PaginationParams & { reviewId?: number; judgment?: string }): Promise<ApiResponse<PaginatedData<ReviewFeedback>>> {
   return http.get('/feedback', { params }).then((r) => r.data)
 }

 // ============== Operation Logs ==============
 export function getOperationLogs(params?: PaginationParams & { userId?: number; action?: string; from?: string; to?: string }): Promise<ApiResponse<PaginatedData<OperationLog>>> {
   return http.get('/operation-logs', { params }).then((r) => r.data)
 }
