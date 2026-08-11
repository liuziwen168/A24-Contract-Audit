<template>
  <div class="workbench-page" v-loading="loading">
    <div class="workbench-layout">
      <!-- 左栏：待复核任务列表 -->
      <div class="panel panel-left">
        <div class="panel-header">
          <span class="panel-title">待复核任务</span>
          <el-tag type="primary" size="small" effect="plain">{{ totalReviews }}</el-tag>
        </div>
        <el-input v-model="taskSearch" placeholder="搜索合同名称或编号..." style="margin-bottom:16px">
          <template #prefix>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#909399" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </template>
        </el-input>
        <div class="task-list" v-if="reviewList.length > 0">
          <div
            v-for="(task, index) in filteredReviewList"
            :key="task.id"
            class="task-card"
            :class="{ active: selectedTaskId === task.id }"
            @click="selectTask(task)"
          >
            <div class="task-name">{{ task.contractId ? '合同 #' + task.contractId : '审查 #' + task.id }}</div>
            <div class="task-meta">
              <div class="task-status">
                <span :class="getStageClass(task.reviewStage)">{{ getStageLabel(task.reviewStage) }}</span>
              </div>
              <div class="task-score">
                <span class="score-label">综合评分：</span>
                <el-tag :type="getScoreTagType(task.overallScore)" size="small" effect="dark">{{ task.overallScore ?? '-' }}</el-tag>
              </div>
            </div>
            <div v-if="task.overallRiskLevel === 'critical' || task.overallRiskLevel === 'high'" class="task-urgent">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#f56c6c" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              <span class="text-red">重点关注</span>
            </div>
            <div class="task-id">ID: {{ task.id }} | {{ new Date(task.createdAt).toLocaleString('zh-CN') }}</div>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无待复核任务</p>
        </div>
      </div>

      <!-- 中栏：审查记录 -->
      <div class="panel panel-center" v-if="currentReview">
        <div class="contract-header">
          <div>
            <h2 class="contract-title">审查 #{{ currentReview.id }}</h2>
            <div class="contract-meta">
              <span>合同 ID：{{ currentReview.contractId }}</span>
              <span>审查模式：{{ currentReview.reviewMode === 'full' ? '全量审查' : '规则审查' }}</span>
              <span>创建时间：{{ new Date(currentReview.createdAt).toLocaleString('zh-CN') }}</span>
            </div>
          </div>
          <div class="system-score">
            <div class="system-score-label">系统建议等级</div>
            <el-tag :type="getRiskTagType(currentReview.overallRiskLevel)" size="large" effect="dark" style="font-size:16px;padding:8px 16px">
              {{ getRiskLevelLabel(currentReview.overallRiskLevel) }} ({{ currentReview.overallScore ?? '-' }})
            </el-tag>
          </div>
        </div>

        <div class="review-section">
          <div class="section-title">审查记录</div>
          <div class="timeline" v-if="currentReview.risks && currentReview.risks.length > 0">
            <!-- AI 初审意见 -->
            <div class="timeline-item">
              <div class="timeline-dot timeline-dot-blue"></div>
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="timeline-title">AI 初审意见</span>
                  <span class="timeline-time">{{ currentReview.aiStartedAt ? new Date(currentReview.aiStartedAt).toLocaleString('zh-CN') : '已完成' }}</span>
                </div>
                <div class="ai-risk-list">
                  <div
                    v-for="risk in currentReview.risks"
                    :key="risk.riskId"
                    class="ai-risk-item"
                    :class="getRiskItemClass(risk.riskLevel)"
                  >
                    <el-tag :type="getRiskTagType(risk.riskLevel)" size="small" effect="dark">{{ getRiskLevelLabel(risk.riskLevel) }}</el-tag>
                    <div class="ai-risk-text">{{ risk.riskName }}：{{ risk.clauseText }}</div>
                  </div>
                </div>
                <div class="risk-summary">
                  <div class="risk-summary-title">风险依据</div>
                  <div v-for="risk in currentReview.risks" :key="'basis-' + risk.riskId" class="risk-summary-item">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#f56c6c" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                    {{ risk.basis }}
                  </div>
                </div>
                <div v-if="currentReview.risks.length > 0" class="risk-summary" style="margin-top:10px">
                  <div class="risk-summary-title">修改建议</div>
                  <div v-for="risk in currentReview.risks" :key="'sug-' + risk.riskId" class="risk-summary-item">
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#1a6fc4" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                    {{ risk.suggestion }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 法务修订记录 -->
            <div v-if="currentReview.reviewRevisions && currentReview.reviewRevisions.length > 0" class="timeline-item">
              <div class="timeline-dot timeline-dot-gray"></div>
              <div class="timeline-content">
                <div class="timeline-header">
                  <span class="timeline-title">法务修订记录</span>
                </div>
                <div v-for="rev in currentReview.reviewRevisions" :key="rev.id" class="legal-revision-card">
                  <p>{{ rev.comment || '无备注' }}</p>
                  <div class="revision-meta">
                    <span>{{ rev.actorRole }} | {{ new Date(rev.createdAt).toLocaleString('zh-CN') }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>暂未识别到风险项</p>
          </div>
        </div>
      </div>
      <div class="panel panel-center" v-else>
        <div class="empty-state" style="height:100%;display:flex;align-items:center;justify-content:center">
          <p style="color:#909399">请从左侧选择一个审查任务</p>
        </div>
      </div>

      <!-- 右栏：风控最终裁断 -->
      <div class="panel panel-right" v-if="currentReview">
        <div class="section-title">风控最终裁断</div>

        <div class="judge-section" v-if="currentReview.risks && currentReview.risks.length > 0">
          <div class="judge-label">AI 识别点处理状态</div>
          <div v-for="risk in currentReview.risks" :key="'judge-' + risk.riskId" class="judge-item">
            <div class="judge-item-header">
              <span>{{ risk.riskId }}. {{ risk.riskName }}</span>
              <el-tag size="small" effect="plain">{{ getRiskLevelLabel(risk.riskLevel) }}</el-tag>
            </div>
            <div class="judge-item-body">
              <div class="judge-item-text">{{ risk.clauseText }}</div>
              <div class="judge-item-actions">
                <el-select
                  :model-value="editingRisks[risk.riskId]?.riskLevel || risk.riskLevel"
                  @change="(val: string) => handleRiskLevelChange(risk, val)"
                  size="small"
                  style="width:110px"
                >
                  <el-option label="低风险" value="low" />
                  <el-option label="中风险" value="medium" />
                  <el-option label="高风险" value="high" />
                  <el-option label="严重" value="critical" />
                </el-select>
                <el-button size="small" :type="riskJudgments[risk.riskId] === 'confirmed' ? 'primary' : ''" :plain="riskJudgments[risk.riskId] !== 'confirmed'" @click="handleConfirmRisk(risk)">确认有效</el-button>
                <el-button size="small" :type="riskJudgments[risk.riskId] === 'dismissed' ? 'danger' : ''" :plain="riskJudgments[risk.riskId] !== 'dismissed'" @click="handleDismissRisk(risk)">判定忽略</el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="judge-section">
          <div class="judge-label">最终定级</div>
          <el-select v-model="overallRiskLevel" placeholder="请选择" style="width:100%">
            <el-option label="低风险 - 建议通过" value="low" />
            <el-option label="中风险 - 建议关注执行" value="medium" />
            <el-option label="高风险 - 建议驳回" value="high" />
            <el-option label="严重风险 - 必须驳回" value="critical" />
          </el-select>
        </div>

        <div class="judge-section">
          <div class="judge-label">综合评分</div>
          <el-input-number v-model="overallScore" :min="0" :max="100" style="width:100%" />
        </div>

        <div class="judge-section">
          <div class="judge-label">风控复核意见</div>
          <el-input
            v-model="reviewOpinion"
            type="textarea"
            :rows="6"
            placeholder="请输入风控最终意见，此意见将同步至业务端及法务端..."
          />
        </div>

        <div class="judge-actions">
          <el-button @click="saveDraft" :loading="savingDraft">保存更新</el-button>
          <el-button type="primary" @click="confirmReview" :loading="confirming">确认复核完成</el-button>
        </div>
      </div>
      <div class="panel panel-right" v-else>
        <div class="empty-state" style="height:100%;display:flex;align-items:center;justify-content:center">
          <p style="color:#909399">请选择审查任务</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listReviews, getReview, updateOverallRisk, updateRisk, submitFeedback, confirmRisk } from '@/api/reviews'
import type { ReviewRecord, RiskRecord } from '@/types'

const route = useRoute()

const loading = ref(false)
const savingDraft = ref(false)
const confirming = ref(false)
const taskSearch = ref('')
const reviewOpinion = ref('')
const overallRiskLevel = ref('medium')
const overallScore = ref<number>(0)

const reviewList = ref<ReviewRecord[]>([])
const totalReviews = ref(0)
const currentReview = ref<ReviewRecord | null>(null)
const selectedTaskId = ref<number | null>(null)
const editingRisks = ref<Record<number, { riskLevel?: string; riskStatus?: string; suggestion?: string }>>({})
const riskJudgments = ref<Record<number, 'confirmed' | 'dismissed'>>({})

const filteredReviewList = computed(() => {
  if (!taskSearch.value) return reviewList.value
  const kw = taskSearch.value.toLowerCase()
  return reviewList.value.filter(r =>
    String(r.id).includes(kw) ||
    String(r.contractId).includes(kw)
  )
})

function getStageLabel(stage: string): string {
  const map: Record<string, string> = {
    aiReview: 'AI审查中',
    legalReview: '法务审核中',
    riskReview: '风控复核中',
    completed: '已完成',
  }
  return map[stage] || stage
}

function getStageClass(stage: string): string {
  const map: Record<string, string> = {
    aiReview: 'text-blue',
    legalReview: 'text-blue',
    riskReview: 'text-orange',
    completed: 'text-green',
  }
  return map[stage] || 'text-gray'
}

function getRiskLevelLabel(level: string | null): string {
  const map: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' }
  return level ? map[level] || level : '-'
}

function getRiskTagType(level: string | null): string {
  const map: Record<string, string> = { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }
  return level ? map[level] || 'info' : 'info'
}

function getScoreTagType(score: number | null): string {
  if (score === null) return 'info'
  if (score < 40) return 'danger'
  if (score < 70) return 'warning'
  return 'success'
}

function getRiskItemClass(level: string): string {
  if (level === 'critical' || level === 'high') return 'ai-risk-high'
  if (level === 'medium') return 'ai-risk-medium'
  return 'ai-risk-low'
}

async function loadReviewList() {
  try {
    const res = await listReviews({ page: 1, pageSize: 50, reviewStage: 'riskReview' })
    reviewList.value = res.items
    totalReviews.value = res.total
  } catch {
    ElMessage.error('加载审查列表失败')
  }
}

async function selectTask(task: ReviewRecord) {
  selectedTaskId.value = task.id
  loading.value = true
  try {
    const res = await getReview(task.id)
    currentReview.value = res
    if (res.overallRiskLevel) {
      overallRiskLevel.value = res.overallRiskLevel
    }
    if (res.overallScore !== null && res.overallScore !== undefined) {
      overallScore.value = res.overallScore
    }
    if (res.riskOpinion) {
      reviewOpinion.value = res.riskOpinion
    }
    // 恢复已保存的风险判定状态
    const fb = (res as any).feedback || []
    riskJudgments.value = {}
    ;(res.risks || []).forEach((r: any) => {
      const match = fb.find((f: any) => f.targetType === 'risk' && f.targetId === (r.riskId || r.id))
      if (match) {
        riskJudgments.value[r.riskId || r.id] = match.judgment === 'correct' ? 'confirmed' : 'dismissed'
      }
    })
  } catch {
    ElMessage.error('加载审查详情失败')
  } finally {
    loading.value = false
  }
}

function handleRiskLevelChange(risk: RiskRecord, val: string) {
  editingRisks.value[risk.riskId] = {
    ...editingRisks.value[risk.riskId],
    riskLevel: val,
  }
}

async function handleConfirmRisk(risk: RiskRecord) {
  const edit = editingRisks.value[risk.riskId] || {}
  try {
    await updateRisk(risk.riskId, {
      riskLevel: edit.riskLevel || risk.riskLevel,
      suggestion: edit.suggestion,
      riskStatus: 'active',
    })
    await submitFeedback(currentReview.value!.id, {
      targetType: 'risk',
      targetId: risk.riskId,
      judgment: 'correct',
      comment: '风控确认有效',
    })
    ElMessage.success('风险点已确认')
    riskJudgments.value[risk.riskId] = 'confirmed'
    delete editingRisks.value[risk.riskId]
  } catch {
    ElMessage.error('操作失败')
  }
}

async function handleDismissRisk(risk: RiskRecord) {
  try {
    await updateRisk(risk.riskId, { riskStatus: 'dismissed' })
    await submitFeedback(currentReview.value!.id, {
      targetType: 'risk',
      targetId: risk.riskId,
      judgment: 'incorrect',
      comment: '风控判定忽略',
    })
    ElMessage.success('风险点已标记为忽略')
    riskJudgments.value[risk.riskId] = 'dismissed'
  } catch {
    ElMessage.error('操作失败')
  }
}

async function saveDraft() {
  if (!currentReview.value) return
  savingDraft.value = true
  try {
    await updateOverallRisk(currentReview.value.id, {
      overallRiskLevel: overallRiskLevel.value,
      overallScore: overallScore.value,
    })
    ElMessage.success('已保存更新')
  } catch {
    ElMessage.error('保存失败')
  } finally {
    savingDraft.value = false
  }
}

async function confirmReview() {
  if (!currentReview.value) return
  confirming.value = true
  try {
    await updateOverallRisk(currentReview.value.id, {
      overallRiskLevel: overallRiskLevel.value,
      overallScore: overallScore.value,
    })
    await confirmRisk(currentReview.value.id, reviewOpinion.value || undefined)
    ElMessage.success('风控复核已完成')
    currentReview.value = null
    selectedTaskId.value = null
    loadReviewList()
  } catch {
    ElMessage.error('确认失败')
  } finally {
    confirming.value = false
  }
}

onMounted(() => {
  loadReviewList()
  const reviewId = route.query.reviewId
  if (reviewId) {
    const id = Number(reviewId)
    if (!isNaN(id)) {
      getReview(id).then(res => {
        reviewList.value = [res]
        selectTask(res)
      }).catch(() => {
        ElMessage.error('加载指定审查失败')
      })
    }
  }
})
</script>

<style scoped>
.workbench-page {
  height: calc(100vh - 104px);
}

.workbench-layout {
  display: grid;
  grid-template-columns: 320px 1fr 380px;
  gap: 20px;
  height: 100%;
}

.panel {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

/* 左栏 */
.panel-left {
  padding: 16px 20px;
}

.task-list {
  flex: 1;
  overflow-y: auto;
}

.task-card {
  padding: 14px 16px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
  border-left: 3px solid transparent;
}

.task-card:hover {
  border-color: #1a6fc4;
  box-shadow: 0 2px 8px rgba(26,111,196,0.1);
}

.task-card.active {
  border-left-color: #1a6fc4;
  background: #f5f8ff;
}

.task-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.task-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.text-blue { color: #1a6fc4; }
.text-gray { color: #909399; }
.text-red { color: #f56c6c; }
.text-orange { color: #e6a23c; }
.text-green { color: #67c23a; }

.task-score {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #606266;
}

.score-label {
  color: #909399;
}

.task-urgent {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 13px;
}

.task-id {
  font-size: 12px;
  color: #909399;
  margin-top: 6px;
}

/* 中栏 */
.panel-center {
  padding: 20px 24px;
  overflow-y: auto;
}

.contract-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.contract-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.contract-meta {
  display: flex;
  gap: 20px;
  font-size: 13px;
  color: #909399;
  flex-wrap: wrap;
}

.system-score {
  text-align: right;
}

.system-score-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

/* 时间线 */
.timeline {
  position: relative;
  padding-left: 24px;
}

.timeline-item {
  position: relative;
  padding-bottom: 24px;
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-dot {
  position: absolute;
  left: -24px;
  top: 4px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 0 2px #e8e8e8;
}

.timeline-dot-blue {
  background: #1a6fc4;
  box-shadow: 0 0 0 2px #1a6fc4;
}

.timeline-dot-gray {
  background: #c0c4cc;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.timeline-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.timeline-time {
  font-size: 12px;
  color: #909399;
}

.ai-risk-list {
  margin-bottom: 16px;
}

.ai-risk-item {
  display: flex;
  gap: 10px;
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 10px;
}

.ai-risk-high {
  background: #fef0f0;
  border-left: 3px solid #f56c6c;
}

.ai-risk-medium {
  background: #fdf6ec;
  border-left: 3px solid #e6a23c;
}

.ai-risk-low {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
}

.ai-risk-text {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  flex: 1;
}

.risk-summary {
  background: #fafafa;
  border-radius: 6px;
  padding: 12px 16px;
}

.risk-summary-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.risk-summary-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.risk-summary-item:last-child {
  margin-bottom: 0;
}

.legal-revision-card {
  background: #fafafa;
  border: 1px dashed #dcdfe6;
  border-radius: 6px;
  padding: 14px 16px;
  margin-bottom: 10px;
}

.legal-revision-card p {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  margin-bottom: 10px;
}

.revision-meta {
  font-size: 12px;
  color: #909399;
}

.revision-attachment {
  display: flex;
  align-items: center;
  gap: 6px;
}

.attachment-link {
  font-size: 13px;
  color: #1a6fc4;
  cursor: pointer;
}

.attachment-link:hover {
  text-decoration: underline;
}

/* 右栏 */
.panel-right {
  padding: 20px 24px;
  overflow-y: auto;
}

.judge-section {
  margin-bottom: 20px;
}

.judge-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
  margin-bottom: 10px;
}

.judge-item {
  background: #fafafa;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 12px 16px;
  margin-bottom: 10px;
}

.judge-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: #303133;
}

.judge-item-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.judge-item-text {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.judge-item-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.judge-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.judge-actions .el-button {
  flex: 1;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
  font-size: 14px;
}
</style>
