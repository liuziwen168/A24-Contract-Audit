<template>
  <div class="audit-records-page" v-loading="loading">
    <!-- 筛选卡片 -->
    <div class="filter-card">
      <div class="filter-header">
        <div>
          <h2 class="filter-title">全量合同审核记录</h2>
          <p class="filter-desc">全局查询系统内所有合同的流转、审核及定稿历史。只读权限。</p>
        </div>
      </div>

      <div class="filter-row">
        <div class="filter-group">
          <label class="filter-label">审核ID</label>
          <el-input v-model="filters.reviewId" placeholder="输入审核ID" style="width:180px" @keyup.enter="handleSearch" />
        </div>
        <div class="filter-group">
          <label class="filter-label">合同ID</label>
          <el-input v-model="filters.contractId" placeholder="输入合同ID" style="width:180px" @keyup.enter="handleSearch" />
        </div>
        <div class="filter-group">
          <label class="filter-label">审核状态</label>
          <el-select v-model="filters.reviewStatus" placeholder="全部状态" style="width:160px">
            <el-option label="全部状态" value="" />
            <el-option label="待处理" value="pending" />
            <el-option label="AI审核中" value="aiReview" />
            <el-option label="法务审核中" value="legalReview" />
            <el-option label="风控审核中" value="riskReview" />
            <el-option label="已完成" value="completed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">审核阶段</label>
          <el-select v-model="filters.reviewStage" placeholder="全部阶段" style="width:160px">
            <el-option label="全部阶段" value="" />
            <el-option label="AI审核" value="aiReview" />
            <el-option label="法务审核" value="legalReview" />
            <el-option label="风控审核" value="riskReview" />
            <el-option label="已完成" value="completed" />
          </el-select>
        </div>
      </div>

      <div class="filter-actions-row">
        <div></div>
        <div class="filter-btns">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" class="btn-apply" @click="handleSearch">应用筛选</el-button>
        </div>
      </div>
    </div>

    <!-- 表格卡片 -->
    <div class="table-card">
      <div class="table-header-bar">
        <span class="result-count">共检索到 <strong>{{ total }}</strong> 条记录</span>
      </div>

      <el-table :data="recordList" stripe style="width:100%">
        <el-table-column label="审核ID" width="100">
          <template #default="{ row }">
            <span class="contract-no">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="合同ID" width="100">
          <template #default="{ row }">
            <span>{{ row.contractId }}</span>
          </template>
        </el-table-column>
        <el-table-column label="审核模式" width="100">
          <template #default="{ row }">
            {{ row.reviewMode === 'full' ? '全量' : '规则' }}
          </template>
        </el-table-column>
        <el-table-column label="审核阶段" width="120">
          <template #default="{ row }">
            <el-tag :type="getStageType(row.reviewStage)" size="small" effect="plain">
              {{ stageLabels[row.reviewStage] || row.reviewStage }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审核状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small" effect="plain">
              {{ statusLabels[row.status] || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <span v-if="row.overallRiskLevel" class="risk-badge" :class="'risk-' + row.overallRiskLevel">
              {{ riskLevelLabels[row.overallRiskLevel] || row.overallRiskLevel }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="综合评分" width="100" align="center">
          <template #default="{ row }">
            {{ row.overallScore !== null ? row.overallScore : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="更新时间" width="180">
          <template #default="{ row }">
            {{ row.updatedAt ? new Date(row.updatedAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchRecords" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listReviews } from '@/api/reviews'
import type { ReviewRecord } from '@/types'

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const recordList = ref<ReviewRecord[]>([])
const total = ref(0)

const filters = reactive({
  reviewId: '',
  contractId: '',
  reviewStatus: '',
  reviewStage: '',
})

const stageLabels: Record<string, string> = {
  aiReview: 'AI审核',
  legalReview: '法务审核',
  riskReview: '风控审核',
  completed: '已完成',
}

const statusLabels: Record<string, string> = {
  pending: '待处理',
  aiReview: 'AI审核中',
  legalReview: '法务审核中',
  riskReview: '风控审核中',
  completed: '已完成',
  failed: '失败',
}

const riskLevelLabels: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重',
}

function getStageType(stage: string) {
  const map: Record<string, string> = {
    aiReview: '',
    legalReview: 'warning',
    riskReview: 'danger',
    completed: 'success',
  }
  return map[stage] || 'info'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    pending: 'info',
    aiReview: '',
    legalReview: 'warning',
    riskReview: 'danger',
    completed: 'success',
    failed: 'danger',
  }
  return map[status] || 'info'
}

async function fetchRecords() {
  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      pageSize: pageSize.value,
    }
    if (filters.contractId) params.contractId = Number(filters.contractId)
    if (filters.reviewStatus) params.reviewStatus = filters.reviewStatus
    if (filters.reviewStage) params.reviewStage = filters.reviewStage
    // no ownerId = all reviews

    const res = await listReviews(params)
    let items = res.items
    if (filters.reviewId) {
      items = items.filter((r: ReviewRecord) => String(r.id) === filters.reviewId)
    }
    recordList.value = items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchRecords()
}

function resetFilters() {
  filters.reviewId = ''
  filters.contractId = ''
  filters.reviewStatus = ''
  filters.reviewStage = ''
  currentPage.value = 1
  fetchRecords()
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.audit-records-page { }

.filter-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e8e6f0;
  margin-bottom: 20px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.filter-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.filter-desc {
  font-size: 14px;
  color: #909399;
}

.filter-row {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.filter-actions-row {
  display: flex;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid #f0eef8;
}

.filter-btns {
  display: flex;
  gap: 12px;
}

.btn-apply {
  background: #1a6fc4;
  border-color: #1a6fc4;
  border-radius: 6px;
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

.table-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f0eef8;
}

.result-count {
  font-size: 14px;
  color: #606266;
}

.result-count strong {
  color: #1a6fc4;
}

.contract-no {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #1a1a2e;
}

.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 20px;
}

.risk-low {
  background: #f0f9f0;
  color: #67c23a;
}

.risk-medium {
  background: #fdf6ec;
  color: #e6a23c;
}

.risk-high {
  background: #fef0f0;
  color: #f56c6c;
}

.risk-critical {
  background: #fef0f0;
  color: #c0392b;
  font-weight: 600;
}

.text-muted {
  color: #c0c4cc;
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
