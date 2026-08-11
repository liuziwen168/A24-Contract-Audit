// ========== 基础类型 ==========

// 用户角色
export type Role = 'user' | 'legalReviewer' | 'riskReviewer' | 'admin'

// 用户状态
export type UserStatus = 'active' | 'disabled'

// 合同状态
export type ContractStatus = 'uploaded' | 'reviewing' | 'reviewed' | 'failed' | 'deleted'

// 审查状态
export type ReviewStatus = 'pending' | 'aiReview' | 'legalReview' | 'riskReview' | 'completed' | 'failed'

// 审查阶段（后端与 status 对齐）
export type ReviewStage = 'aiReview' | 'legalReview' | 'riskReview' | 'completed'

// 审查模式
export type ReviewMode = 'full' | 'rulesOnly'

// 风险等级
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical'

// 风险类型
export type RiskType =
  | 'legalValidity'
  | 'financialTerms'
  | 'complianceRisk'
  | 'conflictOfInterest'
  | 'missingClause'
  | 'ambiguousLanguage'
  | 'obligationRisk'
  | 'intellectualProperty'
  | 'other'

// 风险记录状态
export type RiskStatus = 'active' | 'modified' | 'dismissed'

// 合同类型
export type ContractType = 'purchase' | 'sales' | 'nda' | 'outsourcing' | 'labor' | 'other'

// 文件类型
export type FileType = 'pdf' | 'docx' | 'image'

// 报告格式
export type ReportFormat = 'html' | 'pdf'

// 报告状态
export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed'

// 预警状态
export type WarningStatus =
  | 'pendingLegal'
  | 'pendingRisk'
  | 'active'
  | 'processing'
  | 'closed'
  | 'withdrawn'
  | 'waived'

// 预警类型
export type WarningType = 'riskRuleHit'

// 反馈判定
export type Judgment = 'correct' | 'incorrect' | 'modified'

// ========== API 通用结构 ==========

export interface ApiResponse<T = any> {
  code: string
  message: string
  data: T
  requestId: string
}

export interface PageResult<T> {
  items: T[]
  total: number
}

// ========== 认证 ==========

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  accessToken: string
  tokenType: string
  expiresIn: number
  user: UserInfo
}

export interface UserInfo {
  id: number
  username: string
  role: Role
  userStatus: UserStatus
}

// ========== 合同 ==========

export interface Contract {
  contractId: number
  ownerId: number
  name: string
  contractType: ContractType | null
  contractStatus: ContractStatus
  contractFileId?: number
  createdAt: string
  updatedAt?: string
  deletedAt?: string | null
  // 列表接口可能附带
  files?: ContractFile[]
  latestReview?: ReviewRecord | null
}

export interface ContractFile {
  contractFileId: number
  contractId?: number
  fileName: string
  fileType: FileType
  fileSize: number
  sha256: string
  createdAt?: string
}

// ========== 审查 ==========

export interface ReviewRecord {
  id: number          // mapped from backend reviewId
  contractId: number
  contractName?: string
  contractFileId: number
  fileSha256: string
  idempotencyUserId: number
  idempotencyKey: string
  requestId: string
  reviewMode: ReviewMode
  sourceWarningId: number | null
  reviewStatus: ReviewStatus
  reviewStage: ReviewStage
  aiStartedAt: string | null
  aiAttemptCount: number
  aiResultJson: any | null
  aiModelName: string | null
  aiModelVersion: string | null
  promptVersion: string | null
  aiWarnings: any[]
  legalOpinion: string | null
  riskOpinion: string | null
  legalReviewerId: number | null
  riskReviewerId: number | null
  legalReviewedAt: string | null
  riskReviewedAt: string | null
  missingClauses: any[]
  overallRiskLevel: RiskLevel | null
  overallScore: number | null
  processingTimeMs: number | null
  errorCode: string | null
  errorMessage: string | null
  createdAt: string
  updatedAt: string
  // 后端 errors.py 中的中文消息
  errorDisplay?: string
  // 详情接口附带
  elements?: ContractElement[]
  risks?: RiskRecord[]
  reviewRevisions?: ReviewRevision[]
}

export interface ContractElement {
  id: number
  contractId: number
  reviewId: number | null
  elementType: string
  elementName: string
  valueText: string
  page: number | null
  paragraphIndex: number | null
  confidence: number | null
  source: string
  createdAt: string
  updatedAt: string
}

export interface ReviewRevision {
  id: number
  reviewId: number
  targetType: string
  targetId: number | null
  beforeJson: any
  afterJson: any
  comment: string | null
  actorId: number
  actorRole: string
  reviewStage: string
  createdAt: string
}

// ========== 风险 ==========

export interface RiskRecord {
  id: number
  riskId: number
  reviewId: number
  ruleId: number | null
  ruleSnapshot: any | null
  riskType: string
  riskName: string
  riskLevel: RiskLevel
  clauseText: string
  page: number | null
  paragraphIndex: number | null
  basis: string
  suggestion: string
  confidence: number | null
  status: RiskStatus
  createdAt: string
  updatedAt: string
}

// ========== 预警 ==========

export interface RiskWarning {
  warningId: number
  warningKey: string
  reviewId: number
  contractId: number
  ownerId: number
  warningType?: WarningType
  rule: {
    ruleId?: number | null
    ruleCode?: string | null
    name?: string | null
  }
  risk: {
    riskId?: number | null
    riskType?: string | null
    riskName?: string | null
    riskLevel?: string | null
    basis?: string | null
    suggestion?: string | null
  }
  warningLevel: RiskLevel
  warningStatus: WarningStatus
  sourceSnapshot?: any
  dueAt: string | null
  overdue?: boolean
  acknowledgedAt: string | null
  remediationReviewId: number | null
  remediationReview?: {
    reviewId: number
    reviewStatus: string
    reviewStage: string
    overallRiskLevel: RiskLevel | null
    overallScore: number | null
    errorCode: string | null
    errorMessage: string | null
    updatedAt: string
  } | null
  closedAt: string | null
  createdAt: string
  updatedAt: string
  // 详情可能附带
  actions?: WarningAction[]
}

export interface WarningAction {
  warningActionId?: number
  id?: number
  warningId: number
  actionType: string
  fromStatus: string | null
  toStatus: string | null
  actorId: number | null
  actorRole: string | null
  comment: string | null
  remediationReviewId?: number | null
  detailJson?: any | null
  contractId?: number | null
  riskName?: string | null
  createdAt: string
}

// ========== 报告 ==========

export interface Report {
  id: number
  reviewId: number
  format: ReportFormat
  status: ReportStatus
  startedAt: string | null
  attemptCount: number
  errorCode: string | null
  errorMessage: string | null
  fileSize: number | null
  sha256: string | null
  generatedAt: string | null
  createdAt: string
  updatedAt: string
}

// ========== 管理后台 ==========

export interface StandardClause {
  id: number
  name: string
  contractType: string
  clauseType: string
  content: string
  status: string
  version: string
  createdAt: string
  updatedAt: string
}

export interface RiskRule {
  id: number
  ruleCode: string
  riskType: string
  name: string
  riskLevel: string
  ruleContent: string
  standardClauseId: number | null
  status: string
  warningEnabled: boolean
  warningDueHours: number | null
  version: string
  createdAt: string
  updatedAt: string
}

export interface ReviewFeedback {
  id: number
  reviewId: number
  targetType: string
  targetId: number | null
  userId: number
  judgment: Judgment
  correctedValue: string | null
  comment: string | null
  createdAt: string
}

export interface OperationLog {
  id: number
  userId: number | null
  action: string
  resourceType: string
  resourceId: number | null
  detailJson: any | null
  ip: string | null
  createdAt: string
}

export interface DashboardSummary {
  contractsTotal: number
  contractsByStatus: Record<string, number>
  reviewsTotal: number
  reviewsByStatus: Record<string, number>
  reviewsByStage: Record<string, number>
  effectiveRisksByLevel: Record<string, number>
  pendingLegalReview: number
  pendingRiskReview: number
  completedReviews: number
  warningsTotal: number
  warningsByStatus: Record<string, number>
  overdueWarnings: number
  activeUsers: number
  reportsByStatus: Record<string, number>
  contractUploadTrend: { date: string; contractCount: number }[]
}
