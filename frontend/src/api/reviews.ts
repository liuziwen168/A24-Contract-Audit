import request from './request'
import type { PageResult, ReviewRecord, RiskRecord } from '@/types'

function _toArray(v: any): any[] | null {
  if (!v) return null
  if (Array.isArray(v)) return v
  // 对象 {1: {...}, 2: {...}} → 数组 [...]
  if (typeof v === 'object') return Object.values(v)
  return null
}

export interface ReviewListParams {
  page?: number
  pageSize?: number
  contractId?: number
  reviewStatus?: string
  reviewStage?: string
  ownerId?: number
}

export interface ReviewCreateParams {
  contractId: number
  contractFileId: number
  reviewMode: 'full' | 'rulesOnly'
  sourceWarningId?: number
}

export async function createReview(
  params: ReviewCreateParams,
  idempotencyKey: string,
): Promise<ReviewRecord> {
  const res: any = await request.post('/reviews', params, {
    headers: { 'Idempotency-Key': idempotencyKey },
  })
  return res.data
}

export async function listReviews(params?: ReviewListParams): Promise<PageResult<ReviewRecord>> {
  const res: any = await request.get('/reviews', { params })
  // 后端返回 reviewId 映射为前端 id
  const data: any = res.data
  if (data?.items) {
    data.items = data.items.map((item: any) => ({ ...item, id: item.reviewId }))
  }
  return data
}

export async function getReview(reviewId: number): Promise<ReviewRecord> {
  const res: any = await request.get(`/reviews/${reviewId}`)
  const raw: any = res.data
  if (!raw) return raw
  // 后端详情接口返回 { reviewId, reviewStatus, reviewStage, aiResult, legalReview, riskReview, effectiveResult }
  // 扁平化为视图可直接使用的结构
  const eff = raw.effectiveResult || {}
  const ai = raw.aiResult || {}
  return {
    id: raw.reviewId,
    reviewId: raw.reviewId,
    contractId: ai.contract_id || eff.contract_id || 0,
    contractFileId: 0,
    fileSha256: '',
    idempotencyUserId: 0,
    idempotencyKey: '',
    requestId: '',
    reviewMode: (ai.review_mode || 'full') as any,
    sourceWarningId: null,
    reviewStatus: raw.reviewStatus || '',
    reviewStage: raw.reviewStage || '',
    aiStartedAt: null,
    aiAttemptCount: 0,
    aiResultJson: ai,
    aiModelName: null,
    aiModelVersion: null,
    promptVersion: null,
    aiWarnings: [],
    legalOpinion: raw.legalReview?.opinion || null,
    riskOpinion: raw.riskReview?.opinion || null,
    legalReviewerId: raw.legalReview?.reviewerId || null,
    riskReviewerId: raw.riskReview?.reviewerId || null,
    legalReviewedAt: raw.legalReview?.reviewedAt || null,
    riskReviewedAt: raw.riskReview?.reviewedAt || null,
    missingClauses: eff.missing_clauses || [],
    overallRiskLevel: raw.riskReview?.overallRiskLevel || eff.overall_risk_level || null,
    overallScore: raw.riskReview?.overallScore ?? eff.overall_score ?? null,
    processingTimeMs: null,
    errorCode: null,
    errorMessage: null,
    createdAt: '',
    updatedAt: '',
    // effective 返回的 elements 和 risks 可能是对象（keyed by ID），统一转数组
    // 确保每个 item 同时有 id（统一前端引用）
    elements: (_toArray(eff.elements) || _toArray(ai.elements) || []).map((el: any) => ({ id: el.elementId || el.id, ...el })),
    risks: (_toArray(eff.risks) || _toArray(ai.risks) || []).map((r: any) => ({ id: r.riskId || r.id, ...r })),
    reviewRevisions: raw.legalReview?.revisions || [],
    feedback: raw.feedback || [],
  } as ReviewRecord
}

export async function getReviewProgress(reviewId: number): Promise<{ progress: number; reviewStage: string; reviewStatus: string }> {
  const res: any = await request.get(`/reviews/${reviewId}/progress`)
  return res.data
}

export async function updateContractType(
  reviewId: number,
  contractType: string,
): Promise<null> {
  const res: any = await request.patch(`/reviews/${reviewId}/contract-type`, { contractType })
  return res.data
}

export async function updateElement(
  reviewId: number,
  elementId: number,
  valueText: string,
): Promise<null> {
  const res: any = await request.patch(`/reviews/${reviewId}/elements/${elementId}`, {
    valueText,
  })
  return res.data
}

export async function updateOverallRisk(
  reviewId: number,
  data: { overallRiskLevel?: string; overallScore?: number },
): Promise<null> {
  const res: any = await request.patch(`/reviews/${reviewId}/overall-risk`, data)
  return res.data
}

export async function submitFeedback(
  reviewId: number,
  data: {
    targetType: string
    targetId?: number
    judgment: string
    correctedValue?: string
    comment?: string
  },
): Promise<null> {
  const res: any = await request.post(`/reviews/${reviewId}/feedback`, data)
  return res.data
}

export async function confirmLegal(reviewId: number, opinion?: string): Promise<null> {
  const res: any = await request.post(`/reviews/${reviewId}/legal-confirm`, { opinion })
  return res.data
}

export async function confirmRisk(reviewId: number, opinion?: string): Promise<null> {
  const res: any = await request.post(`/reviews/${reviewId}/risk-confirm`, { opinion })
  return res.data
}

export async function getRisk(riskId: number): Promise<RiskRecord> {
  const res: any = await request.get(`/risks/${riskId}`)
  return res.data
}

export async function updateRisk(
  riskId: number,
  data: { riskLevel?: string; suggestion?: string; riskStatus?: string },
): Promise<null> {
  const res: any = await request.patch(`/risks/${riskId}`, data)
  return res.data
}
