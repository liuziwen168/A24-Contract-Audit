<template>
  <div class="todo-page" v-loading="loading">
    <h2 class="page-title">法务待办列表</h2>

    <div class="table-card">
      <el-table :data="taskList" stripe style="width:100%" empty-text="暂无待审核合同">
        <el-table-column label="审查编号" width="100">
          <template #default="{ row }">#{{ row.id }}</template>
        </el-table-column>
        <el-table-column label="合同名称" min-width="280">
          <template #default="{ row }">{{ row.contractName || '合同 #' + row.contractId }}</template>
        </el-table-column>
        <el-table-column label="审核模式" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ row.reviewMode === 'full' ? '全量审查' : '规则审查' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.overallRiskLevel" :type="riskType(row.overallRiskLevel)" size="small">
              {{ row.overallRiskLevel }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="AI评分" width="100">
          <template #default="{ row }">{{ row.overallScore ?? '-' }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">{{ formatDate(row.createdAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="$router.push({ path: '/legal/workbench', query: { reviewId: row.id } })">
              进入复核
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div style="display:flex;justify-content:flex-end;margin-top:16px">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchData"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listReviews } from '@/api/reviews'

const loading = ref(false)
const taskList = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

function riskType(level: string) {
  const m: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return m[level] || 'info'
}

function formatDate(s: string) {
  if (!s) return '-'
  try { return new Date(s).toLocaleString('zh-CN') } catch { return s }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listReviews({
      page: currentPage.value,
      pageSize: pageSize.value,
      reviewStage: 'legalReview',
    })
    taskList.value = res.items
    total.value = res.total
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.todo-page { }
.page-title { font-size: 22px; font-weight: 600; color: #303133; margin-bottom: 20px; }
.table-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
</style>
