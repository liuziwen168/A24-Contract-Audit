import request from './request'
import type { PageResult, RiskWarning, WarningAction } from '@/types'

export interface WarningListParams {
  page?: number
  pageSize?: number
  warningStatus?: string
  overdue?: boolean
}

export interface WarningStats {
  activeCount: number
  processingCount: number
  overdueCount: number
  totalCount: number
}

export interface WarningListResult extends PageResult<RiskWarning> {
  overdueSummary?: {
    total: number
    withinSevenDays: number
    overSevenDays: number
  }
}

export async function listWarnings(params?: WarningListParams): Promise<WarningListResult> {
  const res: any = await request.get('/warnings', { params })
  return res.data
}

export async function getWarning(warningId: number): Promise<RiskWarning> {
  const res: any = await request.get(`/warnings/${warningId}`)
  return res.data
}

export async function getWarningStats(): Promise<WarningStats> {
  const res: any = await request.get('/warnings/stats')
  return res.data
}

export async function getRecentActions(limit: number = 5): Promise<{ items: WarningAction[] }> {
  const res: any = await request.get('/warnings/actions/recent', { params: { limit } })
  return res.data
}

export async function legalConfirm(warningId: number): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/legal-confirm`)
  return res.data
}

export async function legalWithdraw(warningId: number, comment: string): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/legal-withdraw`, { comment })
  return res.data
}

export async function riskActivate(warningId: number, dueAt?: string): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/risk-activate`, { dueAt })
  return res.data
}

export async function waiveWarning(warningId: number, comment: string): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/waive`, { comment })
  return res.data
}

export async function acknowledgeWarning(warningId: number): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/acknowledge`)
  return res.data
}

export async function closeWarning(warningId: number, comment?: string): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/close`, { comment })
  return res.data
}

export async function reopenWarning(warningId: number, dueDate?: string): Promise<null> {
  const res: any = await request.post(`/warnings/${warningId}/reopen`, { dueDate })
  return res.data
}

export async function reviseWarning(warningId: number, file: File): Promise<any> {
  const formData = new FormData()
  formData.append('file', file)
  const res: any = await request.post(`/warnings/${warningId}/revise`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
  return res.data
}
