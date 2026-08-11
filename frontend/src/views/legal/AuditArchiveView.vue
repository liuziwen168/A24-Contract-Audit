<template>
  <div class="archive-page" v-loading="loading">
    <!-- 顶部操作栏 -->
    <div class="archive-topbar">
      <el-button class="back-btn" @click="$router.back()">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:4px"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
        返回列表
      </el-button>
      <el-button type="primary" class="btn-export-pdf" @click="handleExportPdf">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:4px"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        导出 PDF 案件卷宗
      </el-button>
    </div>

    <h1 class="page-title">审核归档</h1>
    <p class="page-desc">已完成的合同审核记录归档。所有审核结果已锁定为只读状态。</p>

    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-card-title">归档风险分布</div>
        <div class="bar-chart">
          <div class="bar-group">
            <div class="bar high-bar" :style="{ height: archiveStats.high > 0 ? Math.max(15, archiveStats.high * 5) + 'px' : '4px' }"></div>
            <div class="bar medium-bar" :style="{ height: archiveStats.medium > 0 ? Math.max(15, archiveStats.medium * 5) + 'px' : '4px' }"></div>
            <div class="bar low-bar" :style="{ height: archiveStats.low > 0 ? Math.max(15, archiveStats.low * 5) + 'px' : '4px' }"></div>
          </div>
          <div class="bar-labels">
            <span class="bar-label high-label">高: {{ archiveStats.high }}</span>
            <span class="bar-label medium-label">中: {{ archiveStats.medium }}</span>
            <span class="bar-label low-label">低: {{ archiveStats.low }}</span>
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="efficiency-section">
          <div class="efficiency-icon">
            <svg viewBox="0 0 24 24" width="32" height="32" fill="none" stroke="#1a6fc4" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </div>
          <div class="efficiency-info">
            <div class="efficiency-label">归档总数</div>
            <div class="efficiency-value">{{ total }} <span class="efficiency-unit">份</span></div>
          </div>
        </div>
        <p class="efficiency-desc">所有已完成审核的合同档案均在此归档管理</p>
      </div>

      <div class="stat-card">
        <div class="progress-section">
          <div class="progress-row">
            <span class="progress-label">平均综合评分</span>
            <span class="progress-value">{{ avgScore }}</span>
          </div>
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: avgScore + '%', background: avgScore >= 70 ? '#f56c6c' : avgScore >= 40 ? '#e6a23c' : '#67c23a' }"></div>
          </div>
        </div>
        <div class="progress-total" style="margin-top:20px">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="#909399" stroke-width="2" style="vertical-align:middle;margin-right:4px"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
          总计 {{ total }} 条归档记录
        </div>
      </div>
    </div>

    <!-- 归档列表表格 -->
    <div class="table-card">
      <el-table :data="archiveList" stripe style="width:100%">
        <el-table-column label="审核 ID" width="120" align="center">
          <template #default="{ row }">
            <strong style="color:#303133">R-{{ row.id }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="合同 ID" width="130" align="center">
          <template #default="{ row }">
            <span class="contract-link" @click="goToContract(row)">CT-{{ row.contractId }}</span>
          </template>
        </el-table-column>
        <el-table-column label="审核模式" width="120" align="center">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" style="background:#ecf5ff;color:#1a6fc4;border-color:#d9ecff">{{ row.reviewMode === 'full' ? '全量审查' : '规则审查' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="整体风险等级" width="130" align="center">
          <template #default="{ row }">
            <el-tag :type="getRiskType(row.overallRiskLevel)" effect="dark" size="small">{{ riskLevelLabel(row.overallRiskLevel) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="综合评分" width="110" align="center">
          <template #default="{ row }">
            <span :class="getScoreClass(row.overallScore)">{{ row.overallScore ?? '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="完成时间" min-width="190">
          <template #default="{ row }">
            {{ formatDate(row.updatedAt) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button link type="primary" @click="viewDetail(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-footer-note">归档记录为只读状态，所有数据不可修改。</span>
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper"
          @current-change="fetchData"
        />
      </div>
    </div>

    <!-- 页脚 -->
    <div class="page-footer">
      <p>© 2024 A24 Enterprise Contract Management System. Internal Use Only.</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listReviews } from '@/api/reviews'
import type { ReviewRecord } from '@/types'

const router = useRouter()

const loading = ref(false)
const archiveList = ref<ReviewRecord[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(12)

const archiveStats = reactive({ high: 0, medium: 0, low: 0 })
const avgScore = ref(0)

async function fetchData() {
  loading.value = true
  try {
    const res = await listReviews({
      page: currentPage.value,
      pageSize: pageSize.value,
      reviewStage: 'completed',
    })

    archiveList.value = res.items
    total.value = res.total

    // Calculate stats
    let totalScore = 0
    let scoredCount = 0
    archiveStats.high = 0
    archiveStats.medium = 0
    archiveStats.low = 0

    for (const item of res.items) {
      if (item.overallRiskLevel === 'high' || item.overallRiskLevel === 'critical') archiveStats.high++
      else if (item.overallRiskLevel === 'medium') archiveStats.medium++
      else if (item.overallRiskLevel === 'low') archiveStats.low++

      if (item.overallScore !== null) {
        totalScore += item.overallScore
        scoredCount++
      }
    }

    avgScore.value = scoredCount > 0 ? Math.round(totalScore / scoredCount) : 0
  } catch {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

function getRiskType(level: string | null) {
  if (!level) return 'info'
  const map: Record<string, string> = { high: 'danger', critical: 'danger', medium: 'warning', low: 'info' }
  return map[level] || 'info'
}

function riskLevelLabel(level: string | null) {
  if (!level) return '未知'
  const map: Record<string, string> = { high: '高风险', critical: '严重', medium: '中风险', low: '低风险' }
  return map[level] || level
}

function getScoreClass(score: number | null) {
  if (score === null) return ''
  if (score >= 70) return 'text-danger'
  if (score >= 40) return 'text-warning'
  return 'text-success'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleString('zh-CN')
}

function viewDetail(row: ReviewRecord) {
  router.push({ path: '/legal/workbench', query: { reviewId: row.id } })
}

function goToContract(row: ReviewRecord) {
  router.push({ path: '/contracts', query: { contractId: row.contractId } })
}

function handleExportPdf() {
  ElMessage.info('PDF导出功能开发中')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.archive-page {
  max-width: 1100px;
}

.archive-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.back-btn {
  height: 36px;
  font-size: 14px;
  background: #fff;
  border: 1px solid #dcdfe6;
}

.btn-export-pdf {
  height: 36px;
  font-size: 14px;
  background: #1a6fc4;
  border-color: #1a6fc4;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.page-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 20px;
}

/* 统计卡片 */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.stat-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
}

/* 柱状图 */
.bar-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-group {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  height: 100px;
  margin-bottom: 12px;
}

.bar {
  width: 48px;
  border-radius: 4px 4px 0 0;
}

.high-bar { background: #c0392b; }
.medium-bar { background: #d4760a; }
.low-bar { background: #c0c4cc; }

.bar-labels {
  display: flex;
  gap: 20px;
}

.bar-label { font-size: 14px; }
.high-label { color: #c0392b; font-weight: 600; }
.medium-label { color: #d4760a; font-weight: 600; }
.low-label { color: #909399; }

/* 效率 */
.efficiency-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.efficiency-icon {
  width: 56px;
  height: 56px;
  background: #ecf5ff;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.efficiency-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.efficiency-value {
  font-size: 36px;
  font-weight: 700;
  color: #303133;
}

.efficiency-unit {
  font-size: 14px;
  font-weight: 400;
  color: #909399;
}

.efficiency-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
}

/* 进度 */
.progress-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-label { font-size: 13px; color: #606266; }
.progress-value { font-size: 14px; font-weight: 600; color: #1a6fc4; }

.progress-bar-bg {
  height: 8px;
  background: #f0f2f5;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-total {
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
}

/* 表格 */
.table-card {
  background: #fff;
  border-radius: 8px;
  padding: 0 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  margin-bottom: 20px;
}

.contract-link {
  color: #1a6fc4;
  cursor: pointer;
  font-weight: 500;
}

.contract-link:hover { text-decoration: underline; }

.text-danger { color: #f56c6c; font-weight: 700; }
.text-warning { color: #e6a23c; font-weight: 700; }
.text-success { color: #67c23a; font-weight: 700; }

.table-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-top: 1px solid #f0f0f0;
}

.table-footer-note {
  font-size: 13px;
  color: #909399;
}

/* 页脚 */
.page-footer {
  text-align: center;
  padding: 20px 0;
  font-size: 13px;
  color: #c0c4cc;
}
</style>
