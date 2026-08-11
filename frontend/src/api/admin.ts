import request from './request'
import type {
  PageResult,
  UserInfo,
  StandardClause,
  RiskRule,
  ReviewFeedback,
  OperationLog,
  DashboardSummary,
} from '@/types'

// ========== 用户管理 ==========

export interface UserListParams {
  page?: number
  pageSize?: number
  username?: string
  role?: string
  userStatus?: string
}

export async function listUsers(params?: UserListParams): Promise<PageResult<UserInfo>> {
  const res: any = await request.get('/users', { params })
  return res.data
}

export async function createUser(data: {
  username: string
  password: string
  role: string
}): Promise<UserInfo> {
  const res: any = await request.post('/users', data)
  return res.data
}

export async function getUser(userId: number): Promise<UserInfo> {
  const res: any = await request.get(`/users/${userId}`)
  return res.data
}

export async function updateUser(
  userId: number,
  data: { username?: string; role?: string; status?: string },
): Promise<UserInfo> {
  const res: any = await request.patch(`/users/${userId}`, data)
  return res.data
}

// ========== 标准条款 ==========

export interface ClauseListParams {
  page?: number
  pageSize?: number
  name?: string
  contractType?: string
  clauseType?: string
  configStatus?: string
}

export async function listClauses(
  params?: ClauseListParams,
): Promise<PageResult<StandardClause>> {
  const res: any = await request.get('/standard-clauses', { params })
  return res.data
}

export async function createClause(data: {
  name: string
  contractType: string
  clauseType: string
  content: string
}): Promise<StandardClause> {
  const res: any = await request.post('/standard-clauses', data)
  return res.data
}

export async function getClause(clauseId: number): Promise<StandardClause> {
  const res: any = await request.get(`/standard-clauses/${clauseId}`)
  return res.data
}

export async function updateClause(
  clauseId: number,
  data: {
    name?: string
    contractType?: string
    clauseType?: string
    content?: string
  },
): Promise<StandardClause> {
  const res: any = await request.patch(`/standard-clauses/${clauseId}`, data)
  return res.data
}

export async function deleteClause(clauseId: number): Promise<null> {
  const res: any = await request.delete(`/standard-clauses/${clauseId}`)
  return res.data
}

// ========== 风险规则 ==========

export interface RuleListParams {
  page?: number
  pageSize?: number
  ruleCode?: string
  name?: string
  riskType?: string
  riskLevel?: string
  configStatus?: string
}

export async function listRiskRules(params?: RuleListParams): Promise<PageResult<RiskRule>> {
  const res: any = await request.get('/risk-rules', { params })
  return res.data
}

export async function createRiskRule(data: {
  ruleCode: string
  riskType: string
  name: string
  riskLevel: string
  ruleContent: string
  standardClauseId?: number
  warningEnabled?: boolean
  warningDueHours?: number
}): Promise<RiskRule> {
  const res: any = await request.post('/risk-rules', data)
  return res.data
}

export async function getRiskRule(ruleId: number): Promise<RiskRule> {
  const res: any = await request.get(`/risk-rules/${ruleId}`)
  return res.data
}

export async function updateRiskRule(
  ruleId: number,
  data: {
    ruleCode?: string
    riskType?: string
    name?: string
    riskLevel?: string
    ruleContent?: string
    standardClauseId?: number
    warningEnabled?: boolean
    warningDueHours?: number
  },
): Promise<RiskRule> {
  const res: any = await request.patch(`/risk-rules/${ruleId}`, data)
  return res.data
}

export async function deleteRiskRule(ruleId: number): Promise<null> {
  const res: any = await request.delete(`/risk-rules/${ruleId}`)
  return res.data
}

// ========== 反馈 & 日志 & 仪表盘 ==========

export interface FeedbackListParams {
  page?: number
  pageSize?: number
  reviewId?: number
  contractId?: number
  submitterId?: number
  submitterRole?: string
  feedbackType?: string
  judgment?: string
  startDate?: string
  endDate?: string
}

export async function listFeedback(
  params?: FeedbackListParams,
): Promise<PageResult<ReviewFeedback>> {
  const res: any = await request.get('/feedback', { params })
  return res.data
}

export interface LogListParams {
  page?: number
  pageSize?: number
  operatorId?: number
  operatorRole?: string
  action?: string
  targetType?: string
  targetId?: number
  reviewId?: number
  startDate?: string
  endDate?: string
}

export async function listOperationLogs(
  params?: LogListParams,
): Promise<PageResult<OperationLog>> {
  const res: any = await request.get('/operation-logs', { params })
  return res.data
}

export async function getDashboardSummary(params?: { from?: string; to?: string }): Promise<DashboardSummary> {
  const res: any = await request.get('/dashboard/summary', { params })
  return res.data
}
