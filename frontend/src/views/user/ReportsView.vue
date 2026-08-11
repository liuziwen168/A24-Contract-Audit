<template>
  <div class="reports-page" v-loading="loading">
    <!-- 页头 -->
    <div class="page-header">
      <div>
        <h2 class="page-title">AI & 法务联合修改意见报告列表</h2>
        <p class="page-desc">
          审核通过的合同将自动生成修改意见报告。支持 HTML 在线预览和 PDF 下载。
        </p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="fetchReviews" :loading="loading">
        刷新列表
      </el-button>
    </div>

    <!-- 报告列表 -->
    <div class="table-card">
      <el-table :data="reviewsWithReports" stripe style="width:100%" :empty-text="'暂无已完成审核的合同'">
        <el-table-column label="审查ID" width="90">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column label="合同名称" min-width="160">
          <template #default="{ row }">
            <span class="contract-name">{{ row.contractName || `合同 #${row.contractId}` }}</span>
          </template>
        </el-table-column>
        <el-table-column label="合同类型" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.contractType || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag
              v-if="row.overallRiskLevel"
              :type="riskLevelType(row.overallRiskLevel)"
              size="small"
              effect="dark"
            >
              {{ riskLevelLabels[row.overallRiskLevel] || row.overallRiskLevel }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="HTML报告" width="130" align="center">
          <template #default="{ row }">
            <template v-if="getReport(row, 'html')">
              <el-tag
                v-if="getReport(row, 'html')?.status === 'completed'"
                type="success" size="small" effect="plain"
              >
                已生成
              </el-tag>
              <el-tag
                v-else-if="getReport(row, 'html')?.status === 'generating' || getReport(row, 'html')?.status === 'pending'"
                type="warning" size="small" effect="plain"
              >
                <el-icon class="is-loading"><Loading /></el-icon> 生成中
              </el-tag>
              <el-tag v-else type="danger" size="small" effect="plain">
                {{ getReport(row, 'html')?.status }}
              </el-tag>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="PDF报告" width="130" align="center">
          <template #default="{ row }">
            <template v-if="getReport(row, 'pdf')">
              <el-tag
                v-if="getReport(row, 'pdf')?.status === 'completed'"
                type="success" size="small" effect="plain"
              >
                已生成
              </el-tag>
              <el-tag
                v-else-if="getReport(row, 'pdf')?.status === 'generating' || getReport(row, 'pdf')?.status === 'pending'"
                type="warning" size="small" effect="plain"
              >
                <el-icon class="is-loading"><Loading /></el-icon> 生成中
              </el-tag>
              <el-tag v-else type="danger" size="small" effect="plain">
                {{ getReport(row, 'pdf')?.status }}
              </el-tag>
            </template>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <div class="action-cell">
              <!-- HTML 预览 -->
              <el-button
                v-if="getReport(row, 'html')?.status === 'completed'"
                type="primary"
                size="small"
                :icon="View"
                @click="openPreview(row, 'html')"
              >
                HTML 在线预览
              </el-button>
              <!-- PDF 下载 -->
              <el-button
                v-if="getReport(row, 'pdf')?.status === 'completed'"
                type="success"
                size="small"
                :icon="Download"
                @click="handleDownloadPdf(getReport(row, 'pdf')!.id)"
              >
                PDF 下载
              </el-button>
              <!-- 未生成 → 一键生成 -->
              <template v-if="!getReport(row, 'html') || !getReport(row, 'pdf')">
                <el-button
                  v-if="!hasGenerating(row)"
                  type="warning"
                  size="small"
                  :icon="DocumentChecked"
                  @click="generateBothReports(row.id)"
                >
                  生成报告
                </el-button>
                <el-tag v-else type="warning" size="small">
                  <el-icon class="is-loading"><Loading /></el-icon> 生成中...
                </el-tag>
              </template>
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
          @current-change="fetchReviews"
        />
      </div>

      <!-- 使用须知 -->
      <div class="report-notice">
        <strong>报告使用须知：</strong>
        <ul>
          <li>仅已完成审查的合同可生成报告；</li>
          <li><strong>HTML 报告</strong>：在线预览，含 AI 初审 + 法务风控联合修改意见；</li>
          <li><strong>PDF 报告</strong>：完整下载，带格式排版，可用于打印存档；</li>
          <li>报告由 AI 自动生成并整合人工复核结果，生成过程约需数秒。</li>
        </ul>
      </div>
    </div>

    <!-- HTML 在线预览对话框 -->
    <el-dialog
      v-model="previewDialog.visible"
      title="HTML 在线预览意见书"
      width="90%"
      top="3vh"
      :close-on-click-modal="false"
      :destroy-on-close="true"
    >
      <div class="preview-frame-wrapper">
        <iframe
          v-if="previewDialog.url"
          :src="previewDialog.url"
          class="preview-iframe"
          frameborder="0"
          sandbox="allow-same-origin allow-scripts"
        ></iframe>
        <div v-else class="preview-loading">
          <el-icon class="is-loading" :size="32"><Loading /></el-icon>
          <p>正在加载报告...</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="previewDialog.visible = false">关闭</el-button>
        <el-button
          v-if="previewDialog.reportId"
          type="primary"
          :icon="Download"
          @click="handleDownloadPdf(previewDialog.reportId)"
        >
          下载此报告
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, View, Download, Loading, DocumentChecked } from '@element-plus/icons-vue'
import { listReviews } from '@/api/reviews'
import { listReportsByReview, createReport, downloadReport, previewReportUrl } from '@/api/reports'
import type { ReviewRecord, Report } from '@/types'

interface ReviewWithInfo extends ReviewRecord {
  contractName?: string
  contractType?: string
  reports?: Report[]
}

const loading = ref(false)
const reviewsWithReports = ref<ReviewWithInfo[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
let pollTimer: ReturnType<typeof setInterval> | null = null

const previewDialog = ref({
  visible: false,
  url: '',
  reportId: null as number | null,
})

const riskLevelLabels: Record<string, string> = {
  low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险',
}

function riskLevelType(level: string) {
  const map: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return map[level] || 'info'
}

function getReport(row: ReviewWithInfo, format: string): Report | undefined {
  return (row.reports || []).find(r => r.format === format)
}

function hasGenerating(row: ReviewWithInfo): boolean {
  return (row.reports || []).some(r => r.status === 'pending' || r.status === 'generating')
}

function hasAnyGenerating(): boolean {
  return reviewsWithReports.value.some(r => hasGenerating(r))
}

async function fetchReviews() {
  loading.value = true
  try {
    const reviewRes = await listReviews({
      page: currentPage.value,
      pageSize: pageSize.value,
    })
    const completedItems = reviewRes.items.filter(
      (r: ReviewWithInfo) => r.reviewStage === 'completed' || r.reviewStatus === 'completed'
    )
    total.value = completedItems.length > 0 ? reviewRes.total : 0

    // 并行获取每个已完成审查的报告
    await Promise.all(
      completedItems.map(async (review: ReviewWithInfo) => {
        try {
          const r = await listReportsByReview(review.id)
          review.reports = r.items
        } catch {
          review.reports = []
        }
      }),
    )
    reviewsWithReports.value = completedItems
  } finally {
    loading.value = false
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(async () => {
    if (!hasAnyGenerating()) return
    // 静默刷新：只更新报告状态
    await Promise.all(
      reviewsWithReports.value.map(async (review) => {
        try {
          const r = await listReportsByReview(review.id)
          review.reports = r.items
        } catch { /* silent */ }
      }),
    )
  }, 3000) // 每 3 秒轮询
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function generateBothReports(reviewId: number) {
  try {
    await Promise.all([
      createReport(reviewId, 'html'),
      createReport(reviewId, 'pdf'),
    ])
    ElMessage.success('报告生成请求已提交，请稍候...')
    startPolling()
    // 刷新以显示"生成中"状态
    setTimeout(() => fetchReviews(), 1000)
  } catch {
    ElMessage.error('报告生成请求失败')
  }
}

async function handleDownloadPdf(reportId: number) {
  try {
    const res: any = await downloadReport(reportId)
    const blob = res.data || res
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    // 尝试从 content-disposition 获取文件名
    const disposition = res.headers?.['content-disposition']
    if (disposition) {
      const match = disposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (match) a.download = match[1].replace(/['"]/g, '')
    }
    if (!a.download) a.download = `审核报告.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('PDF 下载已开始')
  } catch {
    ElMessage.error('下载失败')
  }
}

function openPreview(row: ReviewWithInfo, format: string) {
  const report = getReport(row, format)
  if (!report) return
  previewDialog.value = {
    visible: true,
    url: previewReportUrl(report.id),
    reportId: report.id,
  }
}

onMounted(() => {
  fetchReviews()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #909399; max-width: 600px; }
.table-card { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.contract-name { font-size: 14px; color: #303133; font-weight: 500; }
.text-muted { color: #c0c4cc; font-size: 13px; }
.action-cell { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.pagination-bar { display: flex; justify-content: center; margin-top: 16px; }

.report-notice { background: #fafafa; border: 1px dashed #dcdfe6; border-radius: 6px; padding: 14px 18px; font-size: 13px; color: #606266; line-height: 1.8; margin-top: 16px; }
.report-notice strong { display: block; margin-bottom: 4px; color: #303133; }

.preview-frame-wrapper { position: relative; min-height: 70vh; }
.preview-iframe { width: 100%; height: 75vh; border: 1px solid #ebeef5; border-radius: 6px; }
.preview-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh; color: #909399; gap: 12px; }
</style>
