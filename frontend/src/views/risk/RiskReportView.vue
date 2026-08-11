<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>审核报告</h2>
        <p>查看本人已完成风控复核的合同报告；支持在线预览、生成和下载。</p>
      </div>
      <div class="header-actions">
        <span v-if="lastUpdated" class="updated-at">更新于 {{ formatDate(lastUpdated) }}</span>
        <el-button :icon="Refresh" @click="fetchData">立即刷新</el-button>
      </div>
    </div>

    <el-alert v-if="loadError" type="error" :title="loadError" show-icon :closable="false" class="load-error">
      <template #default><el-button link type="primary" @click="fetchData">重新加载</el-button></template>
    </el-alert>

    <section class="table-card">
      <div class="table-head"><h3>已完成审核</h3><span>共 {{ total }} 条</span></div>
      <el-table :data="reviews" stripe empty-text="暂无已完成的风控审核">
        <el-table-column label="审核编号" width="100"><template #default="{ row }">#{{ row.id }}</template></el-table-column>
        <el-table-column label="合同" min-width="190"><template #default="{ row }">{{ row.contractName || `合同 #${row.contractId}` }}</template></el-table-column>
        <el-table-column label="风险等级" width="115"><template #default="{ row }"><el-tag v-if="row.overallRiskLevel" :type="levelTag(row.overallRiskLevel)" size="small">{{ levelLabel(row.overallRiskLevel) }}</el-tag><span v-else>-</span></template></el-table-column>
        <el-table-column label="HTML 报告" width="155"><template #default="{ row }"><report-status :report="reportOf(row, 'html')" /></template></el-table-column>
        <el-table-column label="PDF 报告" width="155"><template #default="{ row }"><report-status :report="reportOf(row, 'pdf')" /></template></el-table-column>
        <el-table-column label="操作" width="350" fixed="right">
          <template #default="{ row }">
            <div class="actions">
              <el-button v-if="reportOf(row, 'html')?.status === 'completed'" type="primary" size="small" @click="openPreview(reportOf(row, 'html')!)">在线预览</el-button>
              <el-button v-if="reportOf(row, 'pdf')?.status === 'completed'" type="success" size="small" @click="download(reportOf(row, 'pdf')!)">下载 PDF</el-button>
              <el-button v-if="!reportOf(row, 'html')" size="small" @click="generate(row, 'html')">生成 HTML</el-button>
              <el-button v-if="!reportOf(row, 'pdf')" size="small" @click="generate(row, 'pdf')">生成 PDF</el-button>
              <el-button v-for="report in failedReports(row)" :key="report.id" type="warning" size="small" @click="retry(report)">重试 {{ report.format.toUpperCase() }}</el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchData" /></div>
    </section>

    <el-dialog v-model="preview.visible" title="HTML 审核报告预览" width="90%" top="3vh" destroy-on-close>
      <iframe v-if="preview.url" :src="preview.url" class="preview-frame" sandbox="allow-same-origin allow-scripts" />
      <template #footer><el-button @click="preview.visible = false">关闭</el-button><el-button type="primary" @click="download(preview.report!)">下载 HTML</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, onUnmounted, ref } from 'vue'
import { ElTag, ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { listReviews } from '@/api/reviews'
import { createReport, downloadReport, listReportsByReview, previewReportUrl, retryReport } from '@/api/reports'
import type { Report, ReviewRecord } from '@/types'

interface ReviewWithReports extends ReviewRecord { reports: Report[] }

const ReportStatus = defineComponent({
  props: { report: { type: Object as () => Report | undefined, default: undefined } },
  setup(props) {
    return () => {
      if (!props.report) return h('span', { class: 'muted' }, '未生成')
      const labels: Record<string, string> = { pending: '等待生成', generating: '生成中', completed: '已生成', failed: '生成失败' }
      const types: Record<string, string> = { pending: 'info', generating: 'warning', completed: 'success', failed: 'danger' }
      return h(ElTag, { size: 'small', type: types[props.report.status] || 'info' }, () => `${props.report.format.toUpperCase()} · ${labels[props.report.status] || props.report.status}`)
    }
  },
})

const loading = ref(false)
const loadError = ref('')
const reviews = ref<ReviewWithReports[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const lastUpdated = ref('')
const preview = ref<{ visible: boolean; url: string; report: Report | null }>({ visible: false, url: '', report: null })
let pollTimer: ReturnType<typeof setInterval> | null = null

const hasGenerating = computed(() => reviews.value.some(row => row.reports.some(report => ['pending', 'generating'].includes(report.status))))

function levelTag(level: string) { return ({ low: 'info', medium: 'warning', high: 'danger', critical: 'danger' } as Record<string, string>)[level] || 'info' }
function levelLabel(level: string) { return ({ low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' } as Record<string, string>)[level] || level }
function formatDate(value?: string | null) { if (!value) return '-'; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN') }
function reportOf(row: ReviewWithReports, format: Report['format']) { return row.reports.find(report => report.format === format) }
function failedReports(row: ReviewWithReports) { return row.reports.filter(report => report.status === 'failed') }

async function loadReports(row: ReviewWithReports) {
  const result = await listReportsByReview(row.id, { page: 1, pageSize: 100 })
  row.reports = result.items
}

async function fetchData(silent = false) {
  if (!silent) loading.value = true
  loadError.value = ''
  try {
    const result = await listReviews({ page: page.value, pageSize: pageSize.value, reviewStage: 'completed' })
    const next = result.items.map(item => ({ ...item, reports: [] } as ReviewWithReports))
    await Promise.all(next.map(async row => {
      try { await loadReports(row) } catch { row.reports = [] }
    }))
    reviews.value = next
    total.value = result.total
    lastUpdated.value = new Date().toISOString()
  } catch (error: any) {
    if (!silent) loadError.value = error.response?.data?.message || '审核报告加载失败，请检查服务与登录权限。'
  } finally {
    if (!silent) loading.value = false
  }
}

async function generate(row: ReviewWithReports, format: Report['format']) {
  try {
    await createReport(row.id, format)
    ElMessage.success(`${format.toUpperCase()} 报告已进入生成队列`)
    await loadReports(row)
  } catch { /* 通用请求拦截器会展示后端原因 */ }
}

async function retry(report: Report) {
  try {
    await retryReport(report.id)
    ElMessage.success('报告已重新进入生成队列')
    await fetchData(true)
  } catch { /* 通用请求拦截器会展示后端原因 */ }
}

async function download(report: Report) {
  try {
    const response: any = await downloadReport(report.id)
    const blob = response.data as Blob
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `审核报告.${report.format}`
    link.click()
    URL.revokeObjectURL(url)
  } catch { /* 通用请求拦截器会展示后端原因 */ }
}

function openPreview(report: Report) {
  preview.value = { visible: true, url: previewReportUrl(report.id), report }
}

onMounted(() => {
  fetchData()
  // 有报告在队列中时快速同步状态；没有任务时仍周期刷新，新的完成审核也会出现。
  pollTimer = setInterval(() => fetchData(true), 5000)
})
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }.page-header h2 { margin: 0 0 8px; color: #303133; }.page-header p { margin: 0; color: #909399; font-size: 14px; }.header-actions { display: flex; align-items: center; gap: 12px; }.updated-at, .muted { color: #909399; font-size: 12px; }.load-error { margin-bottom: 16px; }.table-card { background: #fff; border-radius: 10px; box-shadow: 0 1px 4px rgba(0, 0, 0, .06); overflow: hidden; }.table-head { display: flex; justify-content: space-between; align-items: center; padding: 17px 20px; border-bottom: 1px solid #ebeef5; }.table-head h3 { margin: 0; font-size: 16px; color: #303133; }.table-head span { color: #909399; font-size: 13px; }.actions { display: flex; gap: 6px; flex-wrap: wrap; }.pagination { display: flex; justify-content: flex-end; padding: 16px 20px; }.preview-frame { width: 100%; height: 75vh; border: 1px solid #ebeef5; border-radius: 6px; } @media (max-width: 760px) { .header-actions { flex-direction: column; align-items: flex-end; } }
</style>
