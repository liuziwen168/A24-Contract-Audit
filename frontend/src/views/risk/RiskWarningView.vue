<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>预警处理</h2>
        <p>处理待风控确认的风险预警，并跟踪用户提交的整改复审与 AI 审核进度。</p>
      </div>
      <el-button :icon="Refresh" @click="loadCurrentTab">刷新</el-button>
    </div>

    <el-alert
      v-if="loadError"
      type="error"
      :title="loadError"
      show-icon
      :closable="false"
      class="load-error"
    >
      <template #default><el-button link type="primary" @click="loadCurrentTab">重新加载</el-button></template>
    </el-alert>

    <el-tabs v-model="activeTab" @tab-change="loadCurrentTab">
      <el-tab-pane name="pending">
        <template #label>待处理预警 <el-badge :value="pendingTotal" :hidden="pendingTotal === 0" /></template>
        <el-table :data="pendingWarnings" stripe empty-text="暂无待处理预警">
          <el-table-column label="预警编号" width="100"><template #default="{ row }">#{{ row.warningId }}</template></el-table-column>
          <el-table-column label="风险事项" min-width="220">
            <template #default="{ row }">
              <div class="risk-name">{{ row.rule?.name || row.risk?.riskName || '-' }}</div>
              <div class="risk-desc">{{ row.risk?.suggestion || '暂无整改建议' }}</div>
            </template>
          </el-table-column>
          <el-table-column label="合同" width="110"><template #default="{ row }">合同 #{{ row.contractId }}</template></el-table-column>
          <el-table-column label="风险等级" width="105"><template #default="{ row }"><el-tag :type="levelTag(row.warningLevel)">{{ levelLabel(row.warningLevel) }}</el-tag></template></el-table-column>
          <el-table-column label="提交时间" width="175"><template #default="{ row }">{{ formatDate(row.createdAt) }}</template></el-table-column>
          <el-table-column label="操作" width="220" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="openActivate(row)">要求整改</el-button>
              <el-button size="small" @click="openWaive(row)">豁免</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <el-tab-pane name="remediation">
        <template #label>整改复审 <el-badge :value="remediationTotal" :hidden="remediationTotal === 0" /></template>
        <el-alert type="info" :closable="false" show-icon class="tab-guide">
          整改文件提交后会依次进入 AI 审核、法务审核和风控复核。到达“待风控复核”后，可直接进入复核工作台完成裁定。
        </el-alert>
        <el-table :data="remediationWarnings" stripe empty-text="暂无整改复审任务">
          <el-table-column label="预警编号" width="100"><template #default="{ row }">#{{ row.warningId }}</template></el-table-column>
          <el-table-column label="风险事项" min-width="190"><template #default="{ row }">{{ row.rule?.name || row.risk?.riskName || '-' }}</template></el-table-column>
          <el-table-column label="合同" width="105"><template #default="{ row }">合同 #{{ row.contractId }}</template></el-table-column>
          <el-table-column label="整改审核进度" min-width="170">
            <template #default="{ row }">
              <el-tag :type="reviewStageTag(row.remediationReview?.reviewStage)" effect="plain">
                {{ reviewStageLabel(row.remediationReview?.reviewStage, row.remediationReview?.reviewStatus) }}
              </el-tag>
              <div v-if="row.remediationReview?.errorMessage" class="review-error">{{ row.remediationReview.errorMessage }}</div>
            </template>
          </el-table-column>
          <el-table-column label="最近更新" width="175"><template #default="{ row }">{{ formatDate(row.remediationReview?.updatedAt || row.updatedAt) }}</template></el-table-column>
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.remediationReview?.reviewStage === 'riskReview'"
                type="primary"
                size="small"
                @click="goToReview(row)"
              >进入风控复核</el-button>
              <span v-else class="waiting">等待 {{ reviewStageLabel(row.remediationReview?.reviewStage, row.remediationReview?.reviewStatus) }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="activateDialog.visible" title="要求合同方整改" width="440px">
      <p class="dialog-tip">激活后，合同方可在预警中心确认并上传修订合同，系统将自动发起 AI 复审。</p>
      <el-form label-width="96px">
        <el-form-item label="整改期限">
          <el-date-picker v-model="activateDialog.dueAt" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" placeholder="可选" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="activateDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="activateWarning">确认要求整改</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="waiveDialog.visible" title="豁免预警" width="440px">
      <el-input v-model="waiveDialog.comment" type="textarea" :rows="4" maxlength="5000" show-word-limit placeholder="请填写豁免原因（必填）" />
      <template #footer>
        <el-button @click="waiveDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="acting" @click="waiveWarning">确认豁免</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { listWarnings, riskActivate, waiveWarning as waiveWarningApi } from '@/api/warnings'
import type { RiskWarning } from '@/types'

const router = useRouter()
const loading = ref(false)
const acting = ref(false)
const loadError = ref('')
const activeTab = ref<'pending' | 'remediation'>('pending')
const pendingWarnings = ref<RiskWarning[]>([])
const remediationWarnings = ref<RiskWarning[]>([])
const pendingTotal = ref(0)
const remediationTotal = ref(0)
const activateDialog = reactive({ visible: false, warning: null as RiskWarning | null, dueAt: '' })
const waiveDialog = reactive({ visible: false, warning: null as RiskWarning | null, comment: '' })

function levelTag(level: string) {
  return ({ low: 'info', medium: 'warning', high: 'danger', critical: 'danger' } as Record<string, string>)[level] || 'info'
}

function levelLabel(level: string) {
  return ({ low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' } as Record<string, string>)[level] || level
}

function reviewStageLabel(stage?: string, status?: string) {
  if (status === 'failed') return 'AI 审核失败'
  return ({ aiReview: 'AI 审核中', legalReview: '待法务审核', riskReview: '待风控复核', completed: '审核已完成' } as Record<string, string>)[stage || ''] || '等待创建审核任务'
}

function reviewStageTag(stage?: string) {
  return ({ aiReview: 'warning', legalReview: 'info', riskReview: 'danger', completed: 'success' } as Record<string, string>)[stage || ''] || 'info'
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}

async function loadCurrentTab() {
  loading.value = true
  loadError.value = ''
  try {
    // 后端最大 pageSize 为 100；旧页面传 200 会直接触发 400。
    const status = activeTab.value === 'pending' ? 'pendingRisk' : 'processing'
    const data = await listWarnings({ warningStatus: status, page: 1, pageSize: 100 })
    if (activeTab.value === 'pending') {
      pendingWarnings.value = data.items
      pendingTotal.value = data.total
    } else {
      remediationWarnings.value = data.items
      remediationTotal.value = data.total
    }
  } catch (error: any) {
    loadError.value = error.response?.data?.message || '预警数据加载失败，请检查后端服务与登录权限。'
  } finally {
    loading.value = false
  }
}

function openActivate(warning: RiskWarning) {
  activateDialog.warning = warning
  activateDialog.dueAt = ''
  activateDialog.visible = true
}

async function activateWarning() {
  if (!activateDialog.warning) return
  acting.value = true
  try {
    await riskActivate(activateDialog.warning.warningId, activateDialog.dueAt || undefined)
    ElMessage.success('预警已激活，等待合同方确认并提交整改文件')
    activateDialog.visible = false
    await loadCurrentTab()
  } finally {
    acting.value = false
  }
}

function openWaive(warning: RiskWarning) {
  waiveDialog.warning = warning
  waiveDialog.comment = ''
  waiveDialog.visible = true
}

async function waiveWarning() {
  if (!waiveDialog.warning) return
  if (!waiveDialog.comment.trim()) {
    ElMessage.warning('请填写豁免原因')
    return
  }
  acting.value = true
  try {
    await waiveWarningApi(waiveDialog.warning.warningId, waiveDialog.comment.trim())
    ElMessage.success('预警已豁免')
    waiveDialog.visible = false
    await loadCurrentTab()
  } finally {
    acting.value = false
  }
}

function goToReview(warning: RiskWarning) {
  const reviewId = warning.remediationReview?.reviewId || warning.remediationReviewId
  if (reviewId) router.push({ path: '/risk/workbench', query: { reviewId } })
}

onMounted(async () => {
  await loadCurrentTab()
  // 预加载另一个页签的计数，避免用户切换时才知道是否有任务。
  try {
    const data = await listWarnings({ warningStatus: 'processing', page: 1, pageSize: 100 })
    remediationTotal.value = data.total
  } catch { /* 当前页错误状态已在上方展示 */ }
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px; color: #303133; }
.page-header p { margin: 0; color: #909399; font-size: 14px; }
.load-error, .tab-guide { margin-bottom: 16px; }
.risk-name { color: #303133; font-weight: 500; margin-bottom: 4px; }
.risk-desc, .review-error { color: #909399; font-size: 12px; line-height: 1.45; }
.review-error { color: #f56c6c; margin-top: 5px; }
.waiting { color: #909399; font-size: 13px; }
.dialog-tip { margin: 0 0 18px; color: #606266; font-size: 14px; line-height: 1.6; }
</style>
