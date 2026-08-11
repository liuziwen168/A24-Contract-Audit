import request from './request'
import type { PageResult, Report } from '@/types'

function normalizeReport(raw: any): Report {
  return {
    ...raw,
    id: raw.reportId ?? raw.id,
    reviewId: raw.reviewId,
    format: raw.reportFormat ?? raw.format,
    status: raw.reportStatus ?? raw.status,
    startedAt: raw.startedAt ?? null,
    errorMessage: raw.errorMessage ?? null,
  } as Report
}

export async function listReportsByReview(
  reviewId: number,
  params?: { page?: number; pageSize?: number },
): Promise<PageResult<Report>> {
  const res: any = await request.get(`/reviews/${reviewId}/reports`, { params })
  return { ...res.data, items: (res.data.items || []).map(normalizeReport) }
}

export async function createReport(
  reviewId: number,
  format: 'html' | 'pdf',
): Promise<Report> {
  const res: any = await request.post(`/reviews/${reviewId}/reports`, { reportFormat: format })
  return normalizeReport(res.data)
}

export async function getReport(reportId: number): Promise<Report> {
  const res: any = await request.get(`/reports/${reportId}`)
  return normalizeReport(res.data)
}

export async function retryReport(reportId: number): Promise<Report> {
  const res: any = await request.post(`/reports/${reportId}/retry`)
  return normalizeReport(res.data)
}

export function downloadReport(reportId: number) {
  return request.get(`/reports/${reportId}/download`, { responseType: 'blob' })
}

export function previewReportUrl(reportId: number): string {
  const baseURL = import.meta.env.VITE_API_BASE_URL || '/api/v1'
  const token = localStorage.getItem('accessToken')
  // 返回带 token 的预览 URL，供 iframe 使用
  return `${baseURL}/reports/${reportId}/preview?token=${encodeURIComponent(token || '')}`
}
