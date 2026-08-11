<template>
  <div class="clauses-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h1 class="page-title">标准条款库</h1>
        <p class="page-desc">管理和维护用于合同审核及风险识别的标准条款模板。</p>
      </div>
      <div class="header-actions">
        <div class="search-wrap">
          <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#909399" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <el-input v-model="searchKeyword" placeholder="搜索条款名称..." class="search-input" @keyup.enter="handleSearch" />
        </div>
        <el-button type="primary" class="btn-add" @click="openCreateDialog">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;vertical-align:middle"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          新增条款
        </el-button>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="clauseList" stripe style="width:100%">
        <el-table-column label="条款名称" min-width="220">
          <template #default="{ row }">
            <div class="clause-name-cell">
              <div class="clause-name">{{ row.name }}</div>
              <div class="clause-code">v{{ row.version }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="适用合同类型" min-width="160">
          <template #default="{ row }">
            <el-tag size="small" effect="plain" class="type-tag">{{ row.contractType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="条款类别" width="140">
          <template #default="{ row }">
            {{ row.clauseType }}
          </template>
        </el-table-column>
        <el-table-column label="启用状态" width="120">
          <template #default="{ row }">
            <span class="status-badge" :class="row.status === 'active' ? 'status-enabled' : 'status-disabled'">
              <span class="status-dot" :class="row.status === 'active' ? 'dot-green' : 'dot-red'"></span>
              {{ row.status === 'active' ? '已启用' : '已停用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="最后更新" width="180">
          <template #default="{ row }">
            {{ row.updatedAt ? new Date(row.updatedAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <div class="action-icons">
              <button class="icon-btn edit-icon" @click="openEditDialog(row)" title="编辑">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#1a6fc4" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
              </button>
              <button class="icon-btn delete-icon" @click="handleDelete(row)" title="删除">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#f56c6c" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchClauses" />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="560px" destroy-on-close>
      <el-form :model="formData" label-width="100px">
        <el-form-item label="条款名称">
          <el-input v-model="formData.name" placeholder="请输入条款名称" />
        </el-form-item>
        <el-form-item label="适用合同类型">
          <el-select v-model="formData.contractType" style="width:100%">
            <el-option v-for="item in contractTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="条款类别">
          <el-input v-model="formData.clauseType" placeholder="如：核心条款、补充条款等" />
        </el-form-item>
        <el-form-item label="条款内容">
          <el-input v-model="formData.content" type="textarea" :rows="5" placeholder="请输入条款内容" />
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
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listClauses, createClause, updateClause, deleteClause } from '@/api/admin'
import type { StandardClause } from '@/types'

const loading = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const clauseList = ref<StandardClause[]>([])
const total = ref(0)

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingClauseId = ref<number | null>(null)

interface FormData {
  name: string
  contractType: string
  clauseType: string
  content: string
}

const formData = ref<FormData>({
  name: '',
  contractType: 'purchase',
  clauseType: '',
  content: '',
})

const dialogTitle = computed(() => (dialogMode.value === 'create' ? '新增条款' : '编辑条款'))

const contractTypeOptions = [
  { label: '采购合同', value: 'purchase' },
  { label: '销售合同', value: 'sales' },
  { label: '保密协议', value: 'nda' },
  { label: '外包服务', value: 'outsourcing' },
  { label: '劳动合同', value: 'labor' },
  { label: '其他', value: 'other' },
]

async function fetchClauses() {
  loading.value = true
  try {
    const res = await listClauses({
      page: currentPage.value,
      pageSize: pageSize.value,
      name: searchKeyword.value || undefined,
    })
    clauseList.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchClauses()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  editingClauseId.value = null
  formData.value = { name: '', contractType: 'purchase', clauseType: '', content: '' }
  dialogVisible.value = true
}

function openEditDialog(row: StandardClause) {
  dialogMode.value = 'edit'
  editingClauseId.value = row.id
  formData.value = {
    name: row.name,
    contractType: row.contractType,
    clauseType: row.clauseType,
    content: row.content,
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!formData.value.name || !formData.value.content) {
    ElMessage.warning('请填写条款名称和内容')
    return
  }
  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      await createClause({
        name: formData.value.name,
        contractType: formData.value.contractType,
        clauseType: formData.value.clauseType,
        content: formData.value.content,
      })
      ElMessage.success('条款创建成功')
    } else {
      if (editingClauseId.value === null) return
      await updateClause(editingClauseId.value, {
        name: formData.value.name,
        contractType: formData.value.contractType,
        clauseType: formData.value.clauseType,
        content: formData.value.content,
      })
      ElMessage.success('条款已更新')
    }
    dialogVisible.value = false
    fetchClauses()
  } catch {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleDelete(row: StandardClause) {
  try {
    await ElMessageBox.confirm(`确定删除条款「${row.name}」吗？此操作不可撤销。`, '删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteClause(row.id)
    ElMessage.success('条款已删除')
    fetchClauses()
  } catch {
    // cancelled or error
  }
}

onMounted(() => {
  fetchClauses()
})
</script>

<style scoped>
.clauses-page { }

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

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid #e8e6f0;
  border-radius: 8px;
  padding: 8px 14px;
  width: 280px;
}

.search-icon {
  flex-shrink: 0;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: none;
}

.btn-add {
  background: #1a6fc4;
  border-color: #1a6fc4;
  height: 38px;
  padding: 0 20px;
  font-size: 14px;
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

.clause-name-cell {
  display: flex;
  flex-direction: column;
}

.clause-name {
  font-size: 14px;
  font-weight: 500;
  color: #1a1a2e;
}

.clause-code {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.type-tag {
  font-size: 12px;
  background: #f0eef8;
  color: #6c63a0;
  border-color: #e0ddf0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 4px;
}

.status-enabled {
  background: #f0f9f0;
  color: #67c23a;
}

.status-disabled {
  background: #fef0f0;
  color: #f56c6c;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-green {
  background: #67c23a;
}

.dot-red {
  background: #f56c6c;
}

.action-icons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}

.icon-btn:hover {
  background: #f5f3ff;
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
