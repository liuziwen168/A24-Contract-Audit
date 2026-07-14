 // ============== Enums & Dictionaries ==============
 export type Role = 'user' | 'legalReviewer' | 'riskReviewer' | 'admin'
 export type ContractType = 'purchase' | 'sales' | 'nda' | 'outsourcing' | 'labor' | 'other'
 export type RiskLevel = 'high' | 'medium' | 'low'
 export type ReviewStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
 export type ContractStatus = 'uploaded' | 'reviewing' | 'reviewed' | 'failed' | 'deleted'
 export type ReviewStage = 'aiReview' | 'legalReview' | 'riskReview' | 'completed'
 export type FileType = 'docx' | 'pdf' | 'image'
 export type Judgment = 'correct' | 'incorrect' | 'modified'
 export type ReportFormat = 'html' | 'pdf'
 export type RiskStatus = 'active' | 'modified' | 'dismissed'
 export type ConfigStatus = 'active' | 'disabled'
 export type UserStatus = 'active' | 'disabled'
 export type RevisionTargetType = 'contractType' | 'element' | 'risk' | 'overallRisk'
 export type FeedbackTargetType = 'contractType' | 'element' | 'risk' | 'overallRisk'

 // ============== API Response ==============
 export interface ApiResponse<T = any> {
   code: string
   message: string
   data: T
   requestId: string
 }

 export interface PaginatedData<T> {
   items: T[]
   total: number
 }

 // ============== User ==============
 export interface User {
   id: number
   username: string
   role: Role
   userStatus: UserStatus
 }

 export interface LoginRequest {
   username: string
   password: string
 }

 export interface LoginResponse {
   accessToken: string
   tokenType: string
   expiresIn: number
   user: User
 }

 // ============== Contract ==============
 export interface Contract {
   id: number
   ownerId: number
   name: string
   contractType: ContractType | null
   status: ContractStatus
   createdAt: string
   updatedAt: string
 }

 export interface ContractFile {
   id: number
   contractId: number
   fileName: string
   fileType: FileType
   fileSize: number
   sha256: string
 }

 export interface ContractDetail {
   contract: Contract
   files: ContractFile[]
   latestReview: ReviewRecord | null
 }

 // ============== Review ==============
 export interface ReviewRecord {
   id: number
   contractId: number
   contractFileId: number
   fileSha256: string
   requestId: string
   status: ReviewStatus
   reviewStage: ReviewStage
   aiResultJson: any
   aiModelName: string | null
   aiModelVersion: string | null
   promptVersion: string | null
   aiWarnings: string[]
   legalOpinion: string | null
   riskOpinion: string | null
   legalReviewerId: number | null
   riskReviewerId: number | null
   legalReviewedAt: string | null
   riskReviewedAt: string | null
   missingClauses: string[]
   overallRiskLevel: RiskLevel | null
   overallScore: number | null
   processingTimeMs: number | null
   errorCode: string | null
   errorMessage: string | null
   createdAt: string
   updatedAt: string
 }

 export interface ReviewProgress {
   reviewId: number
   reviewStatus: ReviewStatus
   reviewStage: ReviewStage
   progress: number
   aiResultAvailable: boolean
   errorCode: string | null
 }

 export interface ReviewResult {
   reviewId: number
   reviewStatus: ReviewStatus
   reviewStage: ReviewStage
   aiResult: AiResult | null
   legalReview: LegalReview | null
   riskReview: RiskReview | null
   effectiveResult: EffectiveResult
 }

 export interface AiResult {
   requestId: string
   contractId: number
   contractType: ContractType
   typeConfidence: number
   elements: ContractElement[]
   risks: RiskRecord[]
   missingClauses: string[]
   overallRiskLevel: RiskLevel
   overallScore: number
   modelName: string
   modelVersion: string
   promptVersion: string
   processingTimeMs: number
   warnings: string[]
 }

 export interface LegalReview {
   reviewerId: number | null
   reviewedAt: string | null
   opinion: string | null
   revisions: ReviewRevision[]
 }

 export interface RiskReview {
   reviewerId: number | null
   reviewedAt: string | null
   opinion: string | null
   revisions: ReviewRevision[]
   overallRiskLevel: RiskLevel | null
   overallScore: number | null
 }

 export interface EffectiveResult {
   contractType: ContractType | null
   elements: ContractElement[]
   risks: RiskRecord[]
   missingClauses: string[]
   overallRiskLevel: RiskLevel | null
   overallScore: number | null
 }

 // ============== Element ==============
 export interface ContractElement {
   id?: number
   contractId?: number
   reviewId?: number | null
   elementType: string
   elementName: string
   value: string
   page: number | null
   paragraphIndex: number | null
   confidence: number | null
   source: string
 }

 // ============== Risk ==============
 export interface RiskRecord {
   id: number
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
 }

 // ============== Standard Clause ==============
 export interface StandardClause {
   id: number
   name: string
   contractType: ContractType
   clauseType: string
   content: string
   configStatus: ConfigStatus
   version: string
 }

 // ============== Risk Rule ==============
 export interface RiskRule {
   id: number
   ruleCode: string
   riskType: string
   name: string
   riskLevel: RiskLevel
   ruleContent: string
   standardClauseId: number | null
   configStatus: ConfigStatus
   version: string
 }

 // ============== Feedback ==============
 export interface ReviewFeedback {
   id: number
   reviewId: number
   targetType: FeedbackTargetType
   targetId: number | null
   userId: number
   judgment: Judgment
   correctedValue: string | null
   comment: string | null
 }

 // ============== Revision ==============
 export interface ReviewRevision {
   id: number
   reviewId: number
   targetType: RevisionTargetType
   targetId: number | null
   beforeJson: any
   afterJson: any
   comment: string | null
   actorId: number
   actorRole: Role
   reviewStage: ReviewStage
 }

 // ============== Report ==============
 export interface Report {
   id: number
   reviewId: number
   format: ReportFormat
   status: string
   storagePath: string | null
   generatedAt: string | null
 }

 // ============== Operation Log ==============
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

 // ============== Dashboard ==============
 export interface DashboardSummary {
   totalReviews: number
   completedReviews: number
   failedReviews: number
   pendingReviews: number
   riskDistribution: { riskType: string; count: number }[]
   reviewTrend: { date: string; count: number }[]
   contractTypeDistribution: { contractType: string; count: number }[]
 }

 // ============== Pagination Params ==============
 export interface PaginationParams {
   page?: number
   pageSize?: number
 }

 // ============== Contract List Params ==============
 export interface ContractListParams extends PaginationParams {
   contractStatus?: ContractStatus
   contractType?: ContractType
   ownerId?: number
 }

 // ============== Review List Params ==============
 export interface ReviewListParams extends PaginationParams {
   contractId?: number
   reviewStatus?: ReviewStatus
   reviewStage?: ReviewStage
   ownerId?: number
 }

 // ============== Constant maps ==============
 export const CONTRACT_TYPE_LABELS: Record<string, string> = {
   purchase: '采购合同',
   sales: '销售合同',
   nda: '保密协议',
   outsourcing: '服务外包合同',
   labor: '劳动合同',
   other: '其他',
 }

 export const RISK_LEVEL_LABELS: Record<string, string> = {
   high: '高风险',
   medium: '中风险',
   low: '低风险',
 }

 export const RISK_LEVEL_COLORS: Record<string, string> = {
   high: '#F56C6C',
   medium: '#E6A23C',
   low: '#909399',
 }

 export const REVIEW_STATUS_LABELS: Record<string, string> = {
   pending: '待处理',
   processing: '处理中',
   completed: '已完成',
   failed: '失败',
   cancelled: '已取消',
 }

 export const REVIEW_STAGE_LABELS: Record<string, string> = {
   aiReview: 'AI初审',
   legalReview: '法务复核',
   riskReview: '风控复核',
   completed: '已完成',
 }

 export const CONTRACT_STATUS_LABELS: Record<string, string> = {
   uploaded: '已上传',
   reviewing: '审核中',
   reviewed: '已审核',
   failed: '审核失败',
   deleted: '已删除',
 }

 export const JUDGMENT_LABELS: Record<string, string> = {
   correct: '正确',
   incorrect: '错误',
   modified: '已修订',
 }

 export const USER_ROLE_LABELS: Record<string, string> = {
   user: '普通用户',
   legalReviewer: '法务审核员',
   riskReviewer: '风控审核员',
   admin: '管理员',
 }

 export const RISK_STATUS_LABELS: Record<string, string> = {
   active: '有效',
   modified: '已修订',
   dismissed: '已忽略',
 }
