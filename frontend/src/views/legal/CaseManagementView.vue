<template>
  <div class="page" v-loading="loading">
    <h2>案件管理</h2>
    <p class="desc">法务已处理及进行中的审核案件</p>

    <div class="filter-row">
      <el-select v-model="filterStage" placeholder="审核阶段" @change="fetchData" style="width:160px">
        <el-option label="全部" value="" />
        <el-option label="法务复核" value="legalReview" />
        <el-option label="风控复核" value="riskReview" />
        <el-option label="已完成" value="completed" />
      </el-select>
    </div>

    <el-table :data="caseList" stripe empty-text="暂无案件">
      <el-table-column label="审查ID" width="80"><template #default="{ row }">#{{ row.id }}</template></el-table-column>
      <el-table-column label="合同" min-width="200">
        <template #default="{ row }">{{ row.contractName || '合同 #' + row.contractId }}</template>
      </el-table-column>
      <el-table-column label="阶段" width="110">
        <template #default="{ row }">
          <el-tag :type="stageTag(row.reviewStage)" size="small">{{ stageLabel(row.reviewStage) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="风险等级" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.overallRiskLevel" :type="levelTag(row.overallRiskLevel)" size="small">{{ row.overallRiskLevel }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="评分" width="80">
        <template #default="{ row }">{{ row.overallScore ?? '-' }}</template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="$router.push({ path: '/legal/workbench', query: { reviewId: row.id } })">
            进入复核
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="fetchData"
      style="margin-top:16px;justify-content:flex-end"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listReviews } from '@/api/reviews'

const loading = ref(false)
const caseList = ref<any[]>([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const filterStage = ref('')

function stageTag(s: string) {
  const m: Record<string, string> = { legalReview: 'warning', riskReview: 'danger', completed: 'success' }
  return m[s] || 'info'
}
function stageLabel(s: string) {
  const m: Record<string, string> = { legalReview: '法务复核', riskReview: '风控复核', completed: '已完成' }
  return m[s] || s
}
function levelTag(l: string) {
  const m: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return m[l] || 'info'
}
function fmt(s: string) {
  if (!s) return '-'
  try { return new Date(s).toLocaleString('zh-CN') } catch { return s }
}

async function fetchData() {
  loading.value = true
  try {
    const params: any = { page: page.value, pageSize: pageSize.value }
    if (filterStage.value) params.reviewStage = filterStage.value
    const res = await listReviews(params)
    caseList.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.page { }
.desc { color: #909399; font-size: 14px; margin-bottom: 16px; }
.filter-row { margin-bottom: 16px; }
</style>
