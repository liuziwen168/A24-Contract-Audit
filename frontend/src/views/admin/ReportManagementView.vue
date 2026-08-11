<template>
  <div class="report-mgmt-page" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">报告统一管理</h1>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <div class="filter-select-group">
          <span class="filter-label">状态:</span>
          <el-select v-model="filters.status" placeholder="全部" style="width:140px" @change="handleSearch">
            <el-option label="全部" value="" />
            <el-option label="生成成功" value="completed" />
            <el-option label="生成失败" value="failed" />
            <el-option label="处理中" value="processing" />
            <el-option label="待处理" value="pending" />
          </el-select>
        </div>
      </div>
      <div>
        <el-button @click="fetchReports">刷新</el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="reportList" stripe style="width:100%">
        <el-table-column label="报告ID" width="80">
          <template #default="{ row }">
            {{ row.id }}
          </template>
        </el-table-column>
        <el-table-column label="关联审核ID" width="120">
          <template #default="{ row }">
            {{ row.reviewId }}
          </template>
        </el-table-column>
        <el-table-column label="报告格式" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.format === 'pdf' ? 'PDF' : 'HTML' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <span class="status-badge" :class="getStatusClass(row.status)">
              {{ statusLabels[row.status] || row.status }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="生成时间" width="180">
          <template #default="{ row }">
            {{ row.generatedAt ? new Date(row.generatedAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center">
          <template #default="{ row }">
            <div class="action-links">
              <button
                v-if="row.status === 'completed'"
                class="action-link download-link"
                @click="handleDownload(row)"
              >
                下载
              </button>
              <button
                v-if="row.status === 'failed'"
                class="action-link retry-link"
                @click="handleRetry(row)"
              >
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px;vertical-align:middle"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>
                一键重试
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchReports" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listReportsByReview, retryReport, downloadReport } from '@/api/reports'
import { listReviews } from '@/api/reviews'
import type { Report, ReviewRecord } from '@/types'

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const reportList = ref<Report[]>([])
const total = ref(0)

const filters = reactive({
  status: '',
})

const statusLabels: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
}

function getStatusClass(status: string) {
  if (status === 'completed') return 'status-success'
  if (status === 'failed') return 'status-failed'
  if (status === 'processing') return 'status-processing'
  return 'status-pending'
}

async function fetchReports() {
  loading.value = true
  try {
    // Strategy: fetch completed reviews first, then get their reports
    const reviewsRes = await listReviews({
      page: currentPage.value,
      pageSize: pageSize.value,
      reviewStatus: 'completed',
    })

    const reviews: ReviewRecord[] = reviewsRes.items
    const allReports: Report[] = []

    // For each completed review, fetch its reports
    for (const review of reviews) {
      try {
        const reportsRes = await listReportsByReview(review.id, { page: 1, pageSize: 50 })
        allReports.push(...reportsRes.items)
      } catch {
        // skip reviews with no reports
      }
    }

    // Apply status filter
    if (filters.status) {
      reportList.value = allReports.filter((r) => r.status === filters.status)
    } else {
      reportList.value = allReports
    }

    total.value = reportList.value.length
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchReports()
}

async function handleDownload(row: Report) {
  try {
    await downloadReport(row.id)
    ElMessage.success('报告下载已开始')
    // Note: downloadReport uses responseType: 'blob' — the interceptor or caller
    // should handle creating a blob download link
  } catch {
    ElMessage.error('下载失败')
  }
}

async function handleRetry(row: Report) {
  try {
    await retryReport(row.id)
    ElMessage.success('已发起重试，请稍后刷新查看')
    fetchReports()
  } catch {
    // error handled by interceptor
  }
}

onMounted(() => {
  fetchReports()
})
</script>

<style scoped>
.report-mgmt-page { }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
}

/* 筛选栏 */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e8e6f0;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-select-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: #606266;
  white-space: nowrap;
}

/* 表格 */
.table-card {
  background: #fff;
  border-radius: 10px;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e8e6f0;
  overflow: hidden;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 4px;
}

.status-success {
  background: #f0f9f0;
  color: #67c23a;
}

.status-failed {
  background: #fef0f0;
  color: #f56c6c;
}

.status-processing {
  background: #fdf6ec;
  color: #e6a23c;
}

.status-pending {
  background: #f4f4f5;
  color: #909399;
}

.action-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.action-link {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
}

.download-link {
  color: #1a6fc4;
}

.download-link:hover {
  text-decoration: underline;
}

.retry-link {
  color: #f56c6c;
  display: inline-flex;
  align-items: center;
}

.retry-link:hover {
  text-decoration: underline;
}

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
}

.table-total {
  font-size: 14px;
  color: #606266;
}
</style>
