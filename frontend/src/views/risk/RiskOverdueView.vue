<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>逾期清单</h2>
        <p>实时跟踪已超过整改期限的风险预警。</p>
      </div>
      <div class="header-actions">
        <span v-if="lastUpdated" class="updated-at">更新于 {{ formatDate(lastUpdated) }}</span>
        <el-button :icon="Refresh" @click="fetchData">立即刷新</el-button>
      </div>
    </div>

    <el-alert
      v-if="loadError"
      type="error"
      :title="loadError"
      show-icon
      :closable="false"
      class="load-error"
    >
      <template #default><el-button link type="primary" @click="fetchData">重新加载</el-button></template>
    </el-alert>

    <div class="stat-row">
      <div class="stat-card">
        <span class="stat-label">逾期总数</span>
        <span class="num red">{{ totalOverdue }}</span>
        <span class="stat-hint">当前需要跟进的预警</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">超期 1–7 天</span>
        <span class="num orange">{{ overdue1to7 }}</span>
        <span class="stat-hint">请优先安排跟进</span>
      </div>
      <div class="stat-card">
        <span class="stat-label">超期 7 天以上</span>
        <span class="num red">{{ overdueOver7 }}</span>
        <span class="stat-hint">建议重点升级处置</span>
      </div>
    </div>

    <section class="detail-card">
      <div class="detail-header">
        <h3>当前逾期明细</h3>
        <span>共 {{ totalOverdue }} 条</span>
      </div>
      <el-table :data="overdueList" stripe empty-text="当前没有逾期预警">
        <el-table-column label="预警编号" width="100"><template #default="{ row }">#{{ row.warningId }}</template></el-table-column>
        <el-table-column label="审核编号" width="100"><template #default="{ row }">#{{ row.reviewId }}</template></el-table-column>
        <el-table-column label="合同编号" width="100"><template #default="{ row }">#{{ row.contractId }}</template></el-table-column>
        <el-table-column label="风险事项" min-width="220">
          <template #default="{ row }">
            <div class="risk-name">{{ row.rule?.name || row.risk?.riskName || '-' }}</div>
            <div class="risk-suggestion">{{ row.risk?.suggestion || '暂无整改建议' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="110"><template #default="{ row }"><el-tag :type="levelTag(row.warningLevel)" size="small">{{ levelLabel(row.warningLevel) }}</el-tag></template></el-table-column>
        <el-table-column label="整改期限" width="180"><template #default="{ row }">{{ formatDate(row.dueAt) }}</template></el-table-column>
        <el-table-column label="逾期时长" width="120"><template #default="{ row }"><el-tag type="danger" size="small">{{ overdueText(row.overdueMs) }}</el-tag></template></el-table-column>
        <el-table-column label="当前状态" width="115"><template #default="{ row }"><el-tag :type="row.warningStatus === 'processing' ? 'warning' : 'danger'" size="small">{{ row.warningStatus === 'processing' ? '整改复审中' : '等待整改' }}</el-tag></template></el-table-column>
      </el-table>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { listWarnings } from '@/api/warnings'
import type { RiskWarning } from '@/types'

type OverdueWarning = RiskWarning & { overdueMs: number }

const loading = ref(false)
const loadError = ref('')
const overdueList = ref<OverdueWarning[]>([])
const total = ref(0)
const withinSevenDays = ref(0)
const overSevenDays = ref(0)
const lastUpdated = ref('')
let refreshTimer: ReturnType<typeof setInterval> | null = null

const totalOverdue = computed(() => total.value)
const overdue1to7 = computed(() => withinSevenDays.value)
const overdueOver7 = computed(() => overSevenDays.value)

function levelTag(level: string) {
  return ({ low: 'info', medium: 'warning', high: 'danger', critical: 'danger' } as Record<string, string>)[level] || 'info'
}

function levelLabel(level: string) {
  return ({ low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' } as Record<string, string>)[level] || level
}

function formatDate(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}

function overdueText(milliseconds: number) {
  const hours = Math.max(1, Math.floor(milliseconds / 3600000))
  return hours < 24 ? `${hours} 小时` : `${Math.floor(hours / 24)} 天 ${hours % 24} 小时`
}

async function fetchData() {
  loading.value = true
  loadError.value = ''
  try {
    // 后端按 dueAt 与当前时间筛选 active/processing 状态，pageSize 不超过其 100 的校验上限。
    const result = await listWarnings({ page: 1, pageSize: 100, overdue: true })
    const now = Date.now()
    overdueList.value = result.items
      .filter(item => item.dueAt)
      .map(item => ({ ...item, overdueMs: Math.max(0, now - new Date(item.dueAt!).getTime()) }))
      .sort((left, right) => right.overdueMs - left.overdueMs)
    total.value = result.total
    withinSevenDays.value = result.overdueSummary?.withinSevenDays
      ?? overdueList.value.filter(item => item.overdueMs <= 7 * 86400000).length
    overSevenDays.value = result.overdueSummary?.overSevenDays
      ?? overdueList.value.filter(item => item.overdueMs > 7 * 86400000).length
    lastUpdated.value = new Date().toISOString()
  } catch (error: any) {
    loadError.value = error.response?.data?.message || '逾期明细加载失败，请检查后端服务与登录权限。'
    ElMessage.error(loadError.value)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  // 数据库逾期筛选与页面时长均每 30 秒更新一次，新的逾期预警无需手动刷新即可出现。
  refreshTimer = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; }
.page-header h2 { margin: 0 0 8px; color: #303133; }
.page-header p { margin: 0; color: #909399; font-size: 14px; }
.header-actions { display: flex; align-items: center; gap: 12px; }
.updated-at { color: #909399; font-size: 12px; }
.load-error { margin-bottom: 16px; }
.stat-row { display: grid; grid-template-columns: repeat(3, minmax(180px, 260px)); justify-content: center; gap: 24px; margin: 12px auto 24px; }
.stat-card { display: flex; min-height: 124px; flex-direction: column; justify-content: center; align-items: center; background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0, 0, 0, .08); }
.stat-label { color: #606266; font-size: 14px; }
.num { margin: 8px 0 5px; font-size: 32px; font-weight: 700; line-height: 1; }
.red { color: #f56c6c; }.orange { color: #e6a23c; }
.stat-hint { color: #a8abb2; font-size: 12px; }
.detail-card { overflow: hidden; background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0, 0, 0, .06); }
.detail-header { display: flex; align-items: center; justify-content: space-between; padding: 17px 20px; border-bottom: 1px solid #ebeef5; }
.detail-header h3 { margin: 0; color: #303133; font-size: 16px; }.detail-header span { color: #909399; font-size: 13px; }
.risk-name { margin-bottom: 4px; color: #303133; font-weight: 500; }.risk-suggestion { color: #909399; font-size: 12px; line-height: 1.45; }
@media (max-width: 760px) { .stat-row { grid-template-columns: 1fr; }.header-actions { align-items: flex-end; flex-direction: column; } }
</style>
