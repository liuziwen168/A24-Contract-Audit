<template>
  <div class="risk-rules-page" v-loading="loading">
    <!-- 面包屑 -->
    <div class="breadcrumb">
      <span class="breadcrumb-item">系统管理</span>
      <span class="breadcrumb-sep">&gt;</span>
      <span class="breadcrumb-item active">风险规则管理</span>
    </div>

    <div class="page-header">
      <h1 class="page-title">风险规则配置</h1>
      <el-button type="primary" class="btn-add" @click="openCreateDialog">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;vertical-align:middle"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新增规则
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-card">
      <div class="filter-row">
        <div class="filter-group filter-search">
          <label class="filter-label">规则编码/名称</label>
          <div class="search-input-wrap">
            <svg class="search-icon" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#909399" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <el-input v-model="filters.keyword" placeholder="搜索规则..." class="search-input" @keyup.enter="handleSearch" />
          </div>
        </div>
        <div class="filter-group">
          <label class="filter-label">风险类型</label>
          <el-select v-model="filters.riskType" placeholder="全部类型" style="width:160px">
            <el-option label="全部类型" value="" />
            <el-option label="法律效力" value="legalValidity" />
            <el-option label="财务条款" value="financialTerms" />
            <el-option label="合规风险" value="complianceRisk" />
            <el-option label="利益冲突" value="conflictOfInterest" />
            <el-option label="条款缺失" value="missingClause" />
            <el-option label="模糊语言" value="ambiguousLanguage" />
            <el-option label="义务风险" value="obligationRisk" />
            <el-option label="知识产权" value="intellectualProperty" />
            <el-option label="其他" value="other" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">风险等级</label>
          <el-select v-model="filters.riskLevel" placeholder="全部等级" style="width:140px">
            <el-option label="全部等级" value="" />
            <el-option label="低风险" value="low" />
            <el-option label="中风险" value="medium" />
            <el-option label="高风险" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </div>
        <div class="filter-group">
          <label class="filter-label">状态</label>
          <el-select v-model="filters.configStatus" placeholder="全部状态" style="width:140px">
            <el-option label="全部状态" value="" />
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
        </div>
        <div class="filter-actions">
          <el-button @click="resetFilters">重置</el-button>
          <el-button type="primary" @click="handleSearch">查询</el-button>
        </div>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="ruleList" stripe style="width:100%">
        <el-table-column label="规则编码" width="140">
          <template #default="{ row }">
            <span class="rule-code">{{ row.ruleCode }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="规则名称" min-width="200" />
        <el-table-column label="风险类型" width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" class="type-tag">{{ riskTypeLabels[row.riskType] || row.riskType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.riskLevel)" size="small" effect="plain">{{ riskLevelLabels[row.riskLevel] || row.riskLevel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="预警开关" width="100" align="center">
          <template #default="{ row }">
            <span :style="{ color: row.warningEnabled ? '#67c23a' : '#909399' }">{{ row.warningEnabled ? '已开启' : '已关闭' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" size="small" effect="plain">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="版本" width="80" align="center">
          <template #default="{ row }">
            v{{ row.version }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <div class="action-links">
              <button class="action-link edit-link" @click="openEditDialog(row)">编辑</button>
              <button class="action-link delete-link" @click="handleDelete(row)">删除</button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchRules" />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px" destroy-on-close>
      <el-form :model="formData" label-width="110px">
        <el-form-item label="规则编码">
          <el-input v-model="formData.ruleCode" placeholder="如：FIN-001" />
        </el-form-item>
        <el-form-item label="规则名称">
          <el-input v-model="formData.name" placeholder="请输入规则名称" />
        </el-form-item>
        <el-form-item label="风险类型">
          <el-select v-model="formData.riskType" style="width:100%">
            <el-option v-for="item in riskTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="formData.riskLevel" style="width:100%">
            <el-option label="低风险" value="low" />
            <el-option label="中风险" value="medium" />
            <el-option label="高风险" value="high" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险规则内容">
          <el-input v-model="formData.ruleContent" type="textarea" :rows="4" placeholder="请输入具体的判定规则内容" />
        </el-form-item>
        <el-form-item label="启用预警">
          <el-switch v-model="formData.warningEnabled" />
        </el-form-item>
        <el-form-item v-if="formData.warningEnabled" label="预警时限(小时)">
          <el-input-number v-model="formData.warningDueHours" :min="1" :max="720" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ dialogMode === 'create' ? '创建' : '保存' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listRiskRules, createRiskRule, updateRiskRule, deleteRiskRule } from '@/api/admin'
import type { RiskRule } from '@/types'

const loading = ref(false)
const submitting = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const ruleList = ref<RiskRule[]>([])
const total = ref(0)

const filters = reactive({
  keyword: '',
  riskType: '',
  riskLevel: '',
  configStatus: '',
})

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingRuleId = ref<number | null>(null)

interface FormData {
  ruleCode: string
  riskType: string
  name: string
  riskLevel: string
  ruleContent: string
  warningEnabled: boolean
  warningDueHours: number | undefined
}

const formData = ref<FormData>({
  ruleCode: '',
  riskType: 'legalValidity',
  name: '',
  riskLevel: 'medium',
  ruleContent: '',
  warningEnabled: false,
  warningDueHours: undefined,
})

const dialogTitle = ref('')

const riskLevelLabels: Record<string, string> = {
  low: '低风险',
  medium: '中风险',
  high: '高风险',
  critical: '严重',
}

const riskTypeLabels: Record<string, string> = {
  legalValidity: '法律效力',
  financialTerms: '财务条款',
  complianceRisk: '合规风险',
  conflictOfInterest: '利益冲突',
  missingClause: '条款缺失',
  ambiguousLanguage: '模糊语言',
  obligationRisk: '义务风险',
  intellectualProperty: '知识产权',
  other: '其他',
}

const riskTypeOptions = [
  { label: '法律效力', value: 'legalValidity' },
  { label: '财务条款', value: 'financialTerms' },
  { label: '合规风险', value: 'complianceRisk' },
  { label: '利益冲突', value: 'conflictOfInterest' },
  { label: '条款缺失', value: 'missingClause' },
  { label: '模糊语言', value: 'ambiguousLanguage' },
  { label: '义务风险', value: 'obligationRisk' },
  { label: '知识产权', value: 'intellectualProperty' },
  { label: '其他', value: 'other' },
]

function getLevelType(level: string) {
  const map: Record<string, string> = {
    critical: 'danger',
    high: 'danger',
    medium: 'warning',
    low: 'info',
  }
  return map[level] || 'info'
}

async function fetchRules() {
  loading.value = true
  try {
    const res = await listRiskRules({
      page: currentPage.value,
      pageSize: pageSize.value,
      name: filters.keyword || undefined,
      ruleCode: filters.keyword || undefined,
      riskType: filters.riskType || undefined,
      riskLevel: filters.riskLevel || undefined,
      configStatus: filters.configStatus || undefined,
    })
    ruleList.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchRules()
}

function resetFilters() {
  filters.keyword = ''
  filters.riskType = ''
  filters.riskLevel = ''
  filters.configStatus = ''
  currentPage.value = 1
  fetchRules()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  dialogTitle.value = '新增规则'
  editingRuleId.value = null
  formData.value = {
    ruleCode: '',
    riskType: 'legalValidity',
    name: '',
    riskLevel: 'medium',
    ruleContent: '',
    warningEnabled: false,
    warningDueHours: undefined,
  }
  dialogVisible.value = true
}

function openEditDialog(row: RiskRule) {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑规则'
  editingRuleId.value = row.id
  formData.value = {
    ruleCode: row.ruleCode,
    riskType: row.riskType,
    name: row.name,
    riskLevel: row.riskLevel,
    ruleContent: row.ruleContent,
    warningEnabled: row.warningEnabled,
    warningDueHours: row.warningDueHours ?? undefined,
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formData.value.ruleCode || !formData.value.name || !formData.value.ruleContent) {
    ElMessage.warning('请填写规则编码、名称和内容')
    return
  }
  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await createRiskRule({
        ruleCode: formData.value.ruleCode,
        riskType: formData.value.riskType,
        name: formData.value.name,
        riskLevel: formData.value.riskLevel,
        ruleContent: formData.value.ruleContent,
        warningEnabled: formData.value.warningEnabled,
        warningDueHours: formData.value.warningDueHours,
      })
      ElMessage.success('规则创建成功')
    } else {
      if (editingRuleId.value === null) return
      await updateRiskRule(editingRuleId.value, {
        ruleCode: formData.value.ruleCode,
        riskType: formData.value.riskType,
        name: formData.value.name,
        riskLevel: formData.value.riskLevel,
        ruleContent: formData.value.ruleContent,
        warningEnabled: formData.value.warningEnabled,
        warningDueHours: formData.value.warningDueHours,
      })
      ElMessage.success('规则已更新')
    }
    dialogVisible.value = false
    fetchRules()
  } catch {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: RiskRule) {
  try {
    await ElMessageBox.confirm(`确定删除规则「${row.ruleCode} ${row.name}」吗？此操作不可撤销。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteRiskRule(row.id)
    ElMessage.success('规则已删除')
    fetchRules()
  } catch {
    // cancelled or error
  }
}

onMounted(() => {
  fetchRules()
})
</script>

<style scoped>
.risk-rules-page { }

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.breadcrumb-item { cursor: pointer; }
.breadcrumb-item.active { color: #1a6fc4; }
.breadcrumb-sep { color: #c0c4cc; }

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

.btn-add {
  background: #1a6fc4;
  border-color: #1a6fc4;
  height: 38px;
  padding: 0 20px;
  font-size: 14px;
  border-radius: 6px;
}

/* 筛选栏 */
.filter-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  border: 1px solid #e8e6f0;
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: flex-end;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-search {
  flex: 1;
  min-width: 280px;
}

.filter-label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.search-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5f3ff;
  border: 1px solid #e8e6f0;
  border-radius: 8px;
  padding: 8px 14px;
}

.search-icon {
  flex-shrink: 0;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: none;
  background: transparent;
}

.filter-actions {
  margin-left: auto;
  display: flex;
  gap: 12px;
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

.rule-code {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #1a6fc4;
  font-size: 14px;
}

.type-tag {
  background: #f0eef8;
  color: #6c63a0;
  border-color: #e0ddf0;
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
  padding: 2px 4px;
}

.edit-link {
  color: #1a6fc4;
}

.edit-link:hover {
  text-decoration: underline;
}

.delete-link {
  color: #f56c6c;
}

.delete-link:hover {
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
