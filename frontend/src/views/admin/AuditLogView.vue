<template>
  <div class="audit-log-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h1 class="page-title">操作审计日志</h1>
        <p class="page-desc">系统所有不可逆或关键配置变更的操作记录，仅供查询审计，不可篡改。</p>
      </div>
      <div class="audit-status">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#67c23a" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        <span>审计功能已激活</span>
      </div>
    </div>

    <!-- 筛选卡片 -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-group">
          <label class="filter-label">操作人ID</label>
          <el-input v-model="filters.operatorId" placeholder="输入用户ID" style="width:180px" @keyup.enter="handleSearch" />
        </div>
        <div class="filter-group">
          <label class="filter-label">操作动作</label>
          <el-select v-model="filters.action" placeholder="全部动作" style="width:200px">
            <el-option label="全部动作" value="" />
            <el-option label="创建用户" value="create_user" />
            <el-option label="更新用户" value="update_user" />
            <el-option label="创建条款" value="create_clause" />
            <el-option label="更新条款" value="update_clause" />
            <el-option label="删除条款" value="delete_clause" />
            <el-option label="创建规则" value="create_rule" />
            <el-option label="更新规则" value="update_rule" />
            <el-option label="删除规则" value="delete_rule" />
            <el-option label="创建审查" value="create_review" />
            <el-option label="确认审查" value="confirm_review" />
            <el-option label="关闭预警" value="close_warning" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">资源类型</label>
          <el-select v-model="filters.targetType" placeholder="全部类型" style="width:180px">
            <el-option label="全部类型" value="" />
            <el-option label="用户" value="user" />
            <el-option label="标准条款" value="standard_clause" />
            <el-option label="风险规则" value="risk_rule" />
            <el-option label="审查记录" value="review" />
            <el-option label="预警" value="warning" />
            <el-option label="报告" value="report" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">操作时间范围</label>
          <div class="date-range">
            <el-date-picker v-model="filters.startDate" type="date" placeholder="开始日期" style="width:160px" value-format="YYYY-MM-DD" />
            <span class="date-sep">-</span>
            <el-date-picker v-model="filters.endDate" type="date" placeholder="结束日期" style="width:160px" value-format="YYYY-MM-DD" />
          </div>
        </div>
      </div>
      <div class="filter-actions-row">
        <div></div>
        <div class="filter-btns">
          <el-button @click="resetFilters">重置条件</el-button>
          <el-button type="primary" class="btn-search" @click="handleSearch">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;vertical-align:middle"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            查询日志
          </el-button>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="logList" stripe style="width:100%">
        <el-table-column label="操作时间" width="180">
          <template #default="{ row }">
            {{ row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作人ID" width="120">
          <template #default="{ row }">
            {{ row.userId ?? 'SYSTEM' }}
          </template>
        </el-table-column>
        <el-table-column label="操作动作" min-width="180">
          <template #default="{ row }">
            <span class="action-text">{{ row.action }}</span>
          </template>
        </el-table-column>
        <el-table-column label="资源类型" width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ resourceTypeLabels[row.resourceType] || row.resourceType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="资源ID" width="100">
          <template #default="{ row }">
            {{ row.resourceId ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column label="IP地址" width="160">
          <template #default="{ row }">
            <span class="ip-text">{{ row.ip || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作详情" min-width="200">
          <template #default="{ row }">
            <span class="detail-text">{{ row.detailJson ? JSON.stringify(row.detailJson) : '-' }}</span>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchLogs" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listOperationLogs } from '@/api/admin'
import type { OperationLog } from '@/types'

const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const logList = ref<OperationLog[]>([])
const total = ref(0)

const filters = reactive({
  operatorId: '',
  action: '',
  targetType: '',
  startDate: null as string | null,
  endDate: null as string | null,
})

const resourceTypeLabels: Record<string, string> = {
  user: '用户',
  standard_clause: '标准条款',
  risk_rule: '风险规则',
  review: '审查记录',
  warning: '预警',
  report: '报告',
  contract: '合同',
}

async function fetchLogs() {
  loading.value = true
  try {
    const res = await listOperationLogs({
      page: currentPage.value,
      pageSize: pageSize.value,
      operatorId: filters.operatorId ? Number(filters.operatorId) : undefined,
      action: filters.action || undefined,
      targetType: filters.targetType || undefined,
      startDate: filters.startDate || undefined,
      endDate: filters.endDate || undefined,
    })
    logList.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchLogs()
}

function resetFilters() {
  filters.operatorId = ''
  filters.action = ''
  filters.targetType = ''
  filters.startDate = null
  filters.endDate = null
  currentPage.value = 1
  fetchLogs()
}

onMounted(() => {
  fetchLogs()
})
</script>

<style scoped>
.audit-log-page { }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.page-title {
  font-size: 26px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.page-desc {
  font-size: 14px;
  color: #909399;
}

.audit-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #67c23a;
  background: #f0f9f0;
  padding: 8px 16px;
  border-radius: 20px;
}

/* 筛选卡片 */
.filter-card {
  background: #fff;
  border-radius: 10px;
  padding: 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e8e6f0;
  margin-bottom: 20px;
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

.date-range {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date-sep {
  color: #909399;
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

.btn-search {
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

.action-text {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.detail-text {
  font-size: 12px;
  color: #909399;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

.ip-text {
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: #606266;
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
