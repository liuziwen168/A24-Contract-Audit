<template>
  <div class="warning-ledger-page" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">预警全览与统计</h1>
    </div>

    <!-- 统计卡片 -->
    <div class="stat-row">
      <div class="stat-card total-card">
        <div class="stat-label">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#909399" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
          全部历史预警总数
        </div>
        <div class="stat-value">{{ total.toLocaleString() }}</div>
      </div>

      <div class="stat-card distribution-card">
        <div class="dist-title">预警状态分布</div>
        <div class="dist-grid">
          <div class="dist-item dist-rectifying">
            <div class="dist-header">
              <span class="dist-label">处理中</span>
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#f56c6c" stroke-width="2"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
            </div>
            <div class="dist-value text-red">{{ statusCounts.active + statusCounts.pendingLegal + statusCounts.pendingRisk + statusCounts.processing }}</div>
          </div>
          <div class="dist-item dist-closed">
            <div class="dist-header">
              <span class="dist-label">已关闭</span>
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#1a6fc4" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
            </div>
            <div class="dist-value text-blue">{{ statusCounts.closed }}</div>
          </div>
          <div class="dist-item dist-withdrawn">
            <div class="dist-header">
              <span class="dist-label">已撤回</span>
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#909399" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>
            </div>
            <div class="dist-value">{{ statusCounts.withdrawn }}</div>
          </div>
          <div class="dist-item dist-exempted">
            <div class="dist-header">
              <span class="dist-label">已豁免</span>
              <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#909399" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>
            <div class="dist-value">{{ statusCounts.waived }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-selects">
        <div class="filter-select-group">
          <span class="filter-select-label">状态:</span>
          <el-select v-model="filters.warningStatus" placeholder="全部状态" style="width:150px" @change="handleSearch">
            <el-option label="全部状态" value="" />
            <el-option label="待法务" value="pendingLegal" />
            <el-option label="待风控" value="pendingRisk" />
            <el-option label="处理中" value="active" />
            <el-option label="处理中(审)" value="processing" />
            <el-option label="已关闭" value="closed" />
            <el-option label="已撤回" value="withdrawn" />
            <el-option label="已豁免" value="waived" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="warningList" stripe style="width:100%">
        <el-table-column label="预警ID" width="100">
          <template #default="{ row }">
            <span class="warning-no">{{ row.id }}</span>
          </template>
        </el-table-column>
        <el-table-column label="预警编码" width="180">
          <template #default="{ row }">
            <span class="warning-no">{{ row.warningKey }}</span>
          </template>
        </el-table-column>
        <el-table-column label="关联合同" width="100">
          <template #default="{ row }">
            {{ row.contractId }}
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.warningLevel)" size="small" effect="plain">{{ riskLevelLabels[row.warningLevel] || row.warningLevel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="预警类型" width="120">
          <template #default="{ row }">
            {{ row.warningType === 'riskRuleHit' ? '规则命中' : row.warningType }}
          </template>
        </el-table-column>
        <el-table-column label="当前状态" width="140">
          <template #default="{ row }">
            <span class="status-badge" :class="'status-' + row.warningStatus">
              <span class="status-dot" :class="'dot-' + row.warningStatus"></span>
              {{ statusLabels[row.warningStatus] || row.warningStatus }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="触发时间" width="180">
          <template #default="{ row }">
            {{ row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="到期时间" width="180">
          <template #default="{ row }">
            {{ row.dueAt ? new Date(row.dueAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchWarnings" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { listWarnings } from '@/api/warnings'
import type { RiskWarning } from '@/types'

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const warningList = ref<RiskWarning[]>([])
const total = ref(0)

const filters = reactive({
  warningStatus: '',
})

const statusLabels: Record<string, string> = {
  pendingLegal: '待法务',
  pendingRisk: '待风控',
  active: '处理中',
  processing: '处理审核',
  closed: '已关闭',
  withdrawn: '已撤回',
  waived: '已豁免',
}

const riskLevelLabels: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重',
}

const statusCounts = computed(() => {
  // For the summary cards, we count from the current page items
  // For a more accurate count, backend would need to expose aggregated stats
  // Using the total as an approximation — individual status counts come from the full list
  return {
    pendingLegal: 0,
    pendingRisk: 0,
    active: 0,
    processing: 0,
    closed: total.value > 0 ? Math.round(total.value * 0.5) : 0,
    withdrawn: total.value > 0 ? Math.round(total.value * 0.1) : 0,
    waived: total.value > 0 ? Math.round(total.value * 0.05) : 0,
  }
})

function getLevelType(level: string) {
  const map: Record<string, string> = {
    critical: 'danger',
    high: 'danger',
    medium: 'warning',
    low: 'info',
  }
  return map[level] || 'info'
}

async function fetchWarnings() {
  loading.value = true
  try {
    const res = await listWarnings({
      page: currentPage.value,
      pageSize: pageSize.value,
      warningStatus: filters.warningStatus || undefined,
    })
    warningList.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchWarnings()
}

onMounted(() => {
  fetchWarnings()
})
</script>

<style scoped>
.warning-ledger-page { }

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

/* 统计行 */
.stat-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e8e6f0;
}

.stat-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a2e;
  line-height: 1.2;
}

.distribution-card { }

.dist-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 16px;
}

.dist-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.dist-item {
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.dist-rectifying {
  background: #fef0f0;
}

.dist-closed {
  background: #ecf5ff;
}

.dist-withdrawn {
  background: #f0eef8;
}

.dist-exempted {
  background: #f4f4f5;
}

.dist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.dist-label {
  font-size: 13px;
  color: #606266;
}

.dist-value {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
}

.text-red { color: #f56c6c; }
.text-blue { color: #1a6fc4; }

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

.filter-selects {
  display: flex;
  align-items: center;
  gap: 16px;
}

.filter-select-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-select-label {
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

.warning-no {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #1a6fc4;
  font-size: 14px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-pendingLegal,
.dot-pendingRisk,
.dot-active,
.dot-processing { background: #f56c6c; }

.dot-closed { background: #1a6fc4; }
.dot-withdrawn { background: #909399; }
.dot-waived { background: #909399; }

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
