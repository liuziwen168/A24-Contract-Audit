<template>
  <div class="warnings-page" v-loading="loading">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">风险预警中心</h2>
        <p class="page-desc">监控并处理合同审核中的风险预警，及时整改降低风险。</p>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-num danger">{{ stats.activeCount }}</span>
          <span class="stat-label">活跃预警</span>
        </div>
        <div class="stat-item">
          <span class="stat-num warning">{{ stats.processingCount }}</span>
          <span class="stat-label">处理中</span>
        </div>
        <div class="stat-item">
          <span class="stat-num overdue">{{ stats.overdueCount }}</span>
          <span class="stat-label">已逾期</span>
        </div>
        <el-button :icon="Refresh" circle size="small" @click="refreshAll" :loading="loading" />
      </div>
    </div>

    <!-- 筛选 -->
    <div class="filter-bar">
      <div class="filter-item">
        <span class="filter-label">预警状态:</span>
        <el-select v-model="filters.warningStatus" placeholder="全部有效预警" style="width:160px" @change="doSearch" clearable>
          <el-option label="全部有效预警" value="" />
          <el-option label="活跃" value="active" />
          <el-option label="处理中" value="processing" />
          <el-option label="已关闭" value="closed" />
          <el-option label="已撤回" value="withdrawn" />
          <el-option label="已豁免" value="waived" />
        </el-select>
      </div>
      <el-button @click="doReset" :icon="RefreshLeft">重置</el-button>
    </div>

    <div class="warnings-layout">
      <!-- 左侧：预警列表 -->
      <div class="warnings-main">
        <div class="list-card">
          <div class="list-header">
            <span class="list-title">本人有效预警列表</span>
            <span class="table-total">共 {{ total }} 条</span>
          </div>
          <el-table :data="warningList" stripe style="width:100%" :empty-text="'暂无预警记录'">
            <el-table-column label="风险名称" min-width="180">
              <template #default="{ row }">
                <div class="risk-name-cell">
                  <div class="risk-name">{{ row.rule?.name || row.risk?.riskName || `预警 #${row.warningId}` }}</div>
                  <div class="risk-type-tag">
                    <el-tag size="small" type="info">{{ row.risk?.riskType || '-' }}</el-tag>
                    <span class="risk-contract">合同 #{{ row.contractId }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="风险等级" width="100">
              <template #default="{ row }">
                <el-tag :type="riskLevelType(row.warningLevel)" size="small" effect="dark">
                  {{ riskLevelLabels[row.warningLevel] || row.warningLevel }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="预警状态" width="110">
              <template #default="{ row }">
                <el-tag :type="warningStatusType(row.warningStatus)" size="small">
                  {{ warningStatusLabels[row.warningStatus] || row.warningStatus }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="整改截止时间" width="170">
              <template #default="{ row }">
                <div class="due-cell">
                  <span :class="{ 'text-red': row.overdue }">
                    {{ formatDate(row.dueAt) }}
                  </span>
                  <el-tag v-if="row.overdue" type="danger" size="small" effect="dark">已逾期</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" fixed="right">
              <template #default="{ row }">
                <div class="action-cell">
                  <!-- 活跃且未确认 → 确认知悉 -->
                  <el-button
                    v-if="row.warningStatus === 'active' && !row.acknowledgedAt"
                    type="primary"
                    size="small"
                    @click="handleAcknowledge(row)"
                  >
                    确认知悉
                  </el-button>
                  <!-- 活跃且已确认且未发起整改 → 上传修订 -->
                  <el-button
                    v-else-if="row.warningStatus === 'active' && row.acknowledgedAt && !row.remediationReviewId"
                    type="warning"
                    size="small"
                    @click="openReviseDialog(row)"
                  >
                    上传修订
                  </el-button>
                  <!-- 处理中 → 审核中 -->
                  <el-tooltip
                    v-else-if="row.warningStatus === 'processing'"
                    content="修订文件正在重新审核中，请耐心等待"
                    placement="top"
                  >
                    <el-tag type="warning" size="small">整改审核中</el-tag>
                  </el-tooltip>
                  <!-- 已处理完结 -->
                  <span v-else-if="['closed', 'withdrawn', 'waived'].includes(row.warningStatus)" class="text-done">
                    已完结
                  </span>
                  <!-- 已确认等待中 -->
                  <span v-else-if="row.acknowledgedAt" class="text-done">已确认</span>
                  <span v-else class="text-done">-</span>
                </div>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-bar">
            <el-pagination
              v-model:current-page="currentPage"
              :page-size="pageSize"
              :total="total"
              layout="prev, pager, next"
              @current-change="fetchWarnings"
            />
          </div>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="warnings-side">
        <!-- 历史处置记录 -->
        <div class="side-card history-card">
          <div class="side-card-title">
            <el-icon><Clock /></el-icon> 历史处置记录
          </div>
          <div class="side-card-body">
            <div v-if="recentActions.length === 0" class="empty-history">暂无处置记录</div>
            <div v-else class="history-list">
              <div
                v-for="item in recentActions"
                :key="item.warningActionId || item.id"
                class="history-item"
              >
                <div class="history-dot" :class="actionDotClass(item.actionType)"></div>
                <div class="history-content">
                  <div class="history-title">
                    <span class="history-action">{{ actionTypeLabels[item.actionType] || item.actionType }}</span>
                    <span v-if="item.riskName" class="history-risk">· {{ item.riskName }}</span>
                  </div>
                  <div class="history-meta">
                    <span v-if="item.contractId" class="history-contract">合同 #{{ item.contractId }}</span>
                    <span v-if="item.actorRole" class="history-actor">{{ roleLabels[item.actorRole] || item.actorRole }}</span>
                    <span class="history-time">{{ formatTime(item.createdAt) }}</span>
                  </div>
                  <div v-if="item.comment" class="history-comment">{{ item.comment }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作说明 -->
        <div class="side-card">
          <div class="side-card-title">
            <el-icon><InfoFilled /></el-icon> 操作说明
          </div>
          <div class="side-card-body">
            <div class="guide-box">
              <strong>状态流转：</strong>
              <div class="flow-steps">
                <el-tag size="small" type="info">待法务确认</el-tag>
                <span class="flow-arrow">→</span>
                <el-tag size="small" type="warning">待风控确认</el-tag>
                <span class="flow-arrow">→</span>
                <el-tag size="small" type="danger">活跃</el-tag>
                <span class="flow-arrow">→</span>
                <el-tag size="small" type="warning">处理中</el-tag>
                <span class="flow-arrow">→</span>
                <el-tag size="small" type="success">已关闭</el-tag>
              </div>
            </div>
            <div class="guide-box">
              <strong>您的操作：</strong>
              <ul>
                <li><strong>确认知悉</strong> — 低风险预警确认后自动关闭并移除</li>
                <li><strong>确认知悉</strong> — 中/高风险预警确认后可上传修订</li>
                <li><strong>上传修订</strong> — 提交修订文件进入重新审核流程</li>
                <li>审核完成后预警将返回此处，低风险可确认关闭</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传修订文件对话框 -->
    <el-dialog
      v-model="reviseDialog.visible"
      title="上传修订文件"
      width="480px"
      :close-on-click-modal="false"
    >
      <div class="revise-dialog-body">
        <div class="revise-warning-info">
          <div class="revise-info-row">
            <span class="revise-label">预警编号：</span>
            <span>#{{ reviseDialog.warning?.warningId }}</span>
          </div>
          <div class="revise-info-row">
            <span class="revise-label">风险名称：</span>
            <span>{{ reviseDialog.warning?.rule?.name || reviseDialog.warning?.risk?.riskName || '-' }}</span>
          </div>
          <div class="revise-info-row">
            <span class="revise-label">风险等级：</span>
            <el-tag :type="riskLevelType(reviseDialog.warning?.warningLevel || '')" size="small" effect="dark">
              {{ riskLevelLabels[reviseDialog.warning?.warningLevel || ''] || reviseDialog.warning?.warningLevel }}
            </el-tag>
          </div>
        </div>
        <div class="revise-upload-section">
          <p class="revise-hint">请上传修订后的合同文件（支持 .docx / .pdf，最大 {{ maxUploadMB }}MB）</p>
          <el-upload
            ref="uploadRef"
            v-model:file-list="reviseDialog.fileList"
            :auto-upload="false"
            :limit="1"
            :accept="'.docx,.pdf'"
            :on-exceed="handleExceed"
            :on-change="handleFileChange"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将修订文件拖到此处，或 <em>点击选择</em>
            </div>
          </el-upload>
        </div>
      </div>
      <template #footer>
        <el-button @click="reviseDialog.visible = false" :disabled="reviseDialog.submitting">取消</el-button>
        <el-button
          type="primary"
          :loading="reviseDialog.submitting"
          :disabled="!reviseDialog.selectedFile"
          @click="submitRevision"
        >
          提交修订并重新审核
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, InfoFilled, Refresh, RefreshLeft, UploadFilled } from '@element-plus/icons-vue'
import { listWarnings, acknowledgeWarning, getWarningStats, getRecentActions, reviseWarning } from '@/api/warnings'
import type { RiskWarning, WarningAction } from '@/types'
import type { UploadFile, UploadFiles } from 'element-plus'

const loading = ref(false)
const warningList = ref<RiskWarning[]>([])
const recentActions = ref<WarningAction[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const maxUploadMB = 20
let refreshTimer: ReturnType<typeof setInterval> | null = null

const stats = reactive({
  activeCount: 0,
  processingCount: 0,
  overdueCount: 0,
  totalCount: 0,
})

const filters = reactive({ warningStatus: '' })

// 上传修订对话框
const reviseDialog = reactive({
  visible: false,
  warning: null as RiskWarning | null,
  fileList: [] as UploadFile[],
  selectedFile: null as File | null,
  submitting: false,
})

// 标签映射
const riskLevelLabels: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重风险',
}

const warningStatusLabels: Record<string, string> = {
  pendingLegal: '待法务确认',
  pendingRisk: '待风控确认',
  active: '活跃',
  processing: '处理中',
  closed: '已关闭',
  withdrawn: '已撤回',
  waived: '已豁免',
}

const actionTypeLabels: Record<string, string> = {
  candidateCreated: '预警生成',
  legalConfirmed: '法务确认',
  legalWithdraw: '法务撤回',
  withdrawn: '已撤回',
  waiverRequested: '申请豁免',
  remediationRequired: '要求整改',
  remediationStarted: '整改已发起',
  remediationCompleted: '整改审核完成',
  closed: '已关闭',
  reopened: '已重新激活',
  acknowledged: '用户已确认',
  waived: '已豁免',
}

const roleLabels: Record<string, string> = {
  legalReviewer: '法务',
  riskReviewer: '风控',
  user: '用户',
  admin: '管理员',
}

function riskLevelType(level: string) {
  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[level] || 'info'
}

function warningStatusType(status: string) {
  const map: Record<string, string> = {
    pendingLegal: 'info', pendingRisk: 'warning', active: 'danger',
    processing: 'warning', closed: 'success', withdrawn: 'info', waived: 'info',
  }
  return map[status] || 'info'
}

function actionDotClass(actionType: string) {
  if (['candidateCreated', 'acknowledged', 'remediationStarted', 'remediationCompleted', 'reopened'].includes(actionType)) return 'dot-blue'
  if (['legalConfirmed', 'legalWithdraw', 'remediationRequired'].includes(actionType)) return 'dot-orange'
  if (['closed', 'waived'].includes(actionType)) return 'dot-green'
  return 'dot-gray'
}

function formatDate(s: string | null) {
  if (!s) return '-'
  try { return new Date(s).toLocaleDateString('zh-CN') } catch { return s }
}

function formatTime(s: string | null) {
  if (!s) return '-'
  try {
    const d = new Date(s)
    const now = new Date()
    const diffMs = now.getTime() - d.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return '刚刚'
    if (diffMin < 60) return `${diffMin} 分钟前`
    if (diffMin < 1440) return `${Math.floor(diffMin / 60)} 小时前`
    return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch { return s }
}

async function fetchWarnings() {
  loading.value = true
  try {
    const params: any = { page: currentPage.value, pageSize: pageSize.value }
    if (filters.warningStatus) params.warningStatus = filters.warningStatus
    const res = await listWarnings(params)
    warningList.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const data = await getWarningStats()
    stats.activeCount = data.activeCount
    stats.processingCount = data.processingCount
    stats.overdueCount = data.overdueCount
    stats.totalCount = data.totalCount
  } catch { /* silent */ }
}

async function fetchRecentActions() {
  try {
    const data = await getRecentActions(5)
    recentActions.value = data.items
  } catch { /* silent */ }
}

async function refreshAll() {
  await Promise.all([fetchWarnings(), fetchStats(), fetchRecentActions()])
}

function doSearch() {
  currentPage.value = 1
  fetchWarnings()
}

function doReset() {
  filters.warningStatus = ''
  currentPage.value = 1
  fetchWarnings()
}

async function handleAcknowledge(row: RiskWarning) {
  try {
    await acknowledgeWarning(row.warningId)
    if (row.warningLevel === 'low') {
      ElMessage.success('低风险预警已确认，自动从预警中心移除')
    } else {
      ElMessage.success('已确认知悉，请上传修订文件进行整改')
    }
    await refreshAll()
  } catch { /* handled by interceptor */ }
}

function openReviseDialog(row: RiskWarning) {
  reviseDialog.warning = row
  reviseDialog.fileList = []
  reviseDialog.selectedFile = null
  reviseDialog.visible = true
}

function handleFileChange(file: UploadFile, files: UploadFiles) {
  reviseDialog.selectedFile = file.raw || null
}

function handleExceed() {
  ElMessage.warning('只能上传一个修订文件，请先移除已有文件')
}

async function submitRevision() {
  if (!reviseDialog.selectedFile || !reviseDialog.warning) {
    ElMessage.warning('请选择修订文件')
    return
  }
  const fileSizeMB = reviseDialog.selectedFile.size / (1024 * 1024)
  if (fileSizeMB > maxUploadMB) {
    ElMessage.error(`文件大小超过限制（最大 ${maxUploadMB}MB）`)
    return
  }
  reviseDialog.submitting = true
  try {
    const result = await reviseWarning(reviseDialog.warning.warningId, reviseDialog.selectedFile)
    ElMessage.success('修订文件已提交，正在进入重新审核流程')
    reviseDialog.visible = false
    await refreshAll()
  } catch {
    ElMessage.error('提交修订文件失败，请重试')
  } finally {
    reviseDialog.submitting = false
  }
}

onMounted(() => {
  refreshAll()
  // 每 30 秒刷新一次预警数据和处置记录
  refreshTimer = setInterval(() => {
    fetchStats()
    fetchRecentActions()
  }, 30000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
/* 页头 */
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #909399; }
.header-stats { display: flex; align-items: center; gap: 16px; }
.stat-item { text-align: center; min-width: 64px; }
.stat-num { display: block; font-size: 22px; font-weight: 700; line-height: 1.2; }
.stat-num.danger { color: #f56c6c; }
.stat-num.warning { color: #e6a23c; }
.stat-num.overdue { color: #f56c6c; }
.stat-label { font-size: 12px; color: #909399; }

/* 筛选 */
.filter-bar { display: flex; align-items: center; gap: 16px; background: #fff; border-radius: 8px; padding: 14px 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.filter-item { display: flex; align-items: center; gap: 8px; }
.filter-label { font-size: 14px; color: #606266; white-space: nowrap; }

/* 布局 */
.warnings-layout { display: grid; grid-template-columns: 1fr 340px; gap: 20px; align-items: start; }

/* 列表 */
.list-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.list-title { font-size: 16px; font-weight: 600; color: #303133; }
.table-total { font-size: 13px; color: #909399; }

.risk-name-cell .risk-name { font-size: 14px; color: #303133; font-weight: 500; }
.risk-name-cell .risk-type-tag { display: flex; align-items: center; gap: 8px; margin-top: 4px; }
.risk-contract { font-size: 12px; color: #909399; }

.due-cell { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.text-red { color: #f56c6c; font-weight: 500; }
.text-done { color: #909399; font-size: 13px; }

.action-cell { display: flex; gap: 4px; flex-wrap: wrap; }

.pagination-bar { display: flex; justify-content: center; margin-top: 16px; }

/* 右侧面板 */
.warnings-side { display: flex; flex-direction: column; gap: 20px; }
.side-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.side-card-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.side-card-title .el-icon { color: #1a6fc4; }
.side-card-body { font-size: 14px; color: #606266; line-height: 1.8; }

/* 历史处置记录 */
.history-card { max-height: 420px; display: flex; flex-direction: column; }
.history-card .side-card-body { flex: 1; overflow-y: auto; }
.empty-history { text-align: center; color: #c0c4cc; padding: 24px 0; font-size: 13px; }
.history-list { display: flex; flex-direction: column; gap: 0; }
.history-item { display: flex; gap: 10px; padding: 10px 0; border-bottom: 1px solid #f2f3f5; }
.history-item:last-child { border-bottom: none; }
.history-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
.dot-blue { background: #409eff; }
.dot-orange { background: #e6a23c; }
.dot-green { background: #67c23a; }
.dot-gray { background: #c0c4cc; }
.history-content { flex: 1; min-width: 0; }
.history-title { font-size: 13px; color: #303133; margin-bottom: 2px; }
.history-action { font-weight: 500; }
.history-risk { color: #909399; font-size: 12px; }
.history-meta { display: flex; gap: 8px; font-size: 11px; color: #c0c4cc; flex-wrap: wrap; }
.history-comment { font-size: 12px; color: #606266; margin-top: 4px; background: #f5f7fa; padding: 4px 8px; border-radius: 4px; }

/* 说明 */
.guide-box { background: #f5f7fa; border-radius: 6px; padding: 12px 14px; margin-bottom: 10px; }
.guide-box:last-child { margin-bottom: 0; }
.guide-box strong { display: block; margin-bottom: 6px; color: #303133; font-size: 13px; }
.guide-box ul { padding-left: 20px; font-size: 13px; }
.guide-box li { margin-bottom: 4px; }
.flow-steps { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-top: 6px; }
.flow-arrow { color: #c0c4cc; font-size: 12px; }

/* 上传修订对话框 */
.revise-dialog-body { }
.revise-warning-info { background: #f5f7fa; border-radius: 6px; padding: 14px 16px; margin-bottom: 18px; }
.revise-info-row { display: flex; align-items: center; gap: 8px; font-size: 14px; margin-bottom: 6px; }
.revise-info-row:last-child { margin-bottom: 0; }
.revise-label { color: #909399; min-width: 72px; }
.revise-hint { font-size: 13px; color: #909399; margin-bottom: 10px; }
.revise-upload-section { }

@media (max-width: 1024px) {
  .warnings-layout { grid-template-columns: 1fr; }
}
</style>
