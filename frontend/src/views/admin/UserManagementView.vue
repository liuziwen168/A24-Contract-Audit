<template>
  <div class="user-mgmt-page" v-loading="loading">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <el-button type="primary" class="btn-add" @click="openCreateDialog">
        <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:6px;vertical-align:middle"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        新增账号
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <div class="search-input-wrap">
        <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#909399" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <el-input v-model="searchKeyword" placeholder="搜索用户名..." class="search-input" @keyup.enter="handleSearch" />
      </div>
      <el-button class="btn-filter" @click="handleSearch">查询</el-button>
    </div>

    <!-- 表格 -->
    <div class="table-card">
      <el-table :data="userList" stripe style="width:100%">
        <el-table-column label="用户名" min-width="260">
          <template #default="{ row }">
            <div class="user-cell">
              <div class="user-avatar" :style="{ background: getAvatarColor(row.id) }">
                {{ getAvatarText(row.username) }}
              </div>
              <div class="user-info">
                <div class="user-name-row">
                  <span class="user-name">{{ row.username }}</span>
                  <el-tag v-if="row.id === currentUserId" size="small" type="info" effect="plain" class="current-tag">当前</el-tag>
                </div>
                <span class="user-id-label">ID: {{ row.id }}</span>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="160">
          <template #default="{ row }">
            {{ roleLabelMap[row.role] || row.role }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="140">
          <template #default="{ row }">
            <span class="status-badge" :class="row.userStatus === 'active' ? 'status-active' : 'status-disabled'">
              <span class="status-dot" :class="row.userStatus === 'active' ? 'dot-green' : 'dot-gray'"></span>
              {{ row.userStatus === 'active' ? '启用' : '停用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="200">
          <template #default="{ row }">
            {{ row.createdAt ? new Date(row.createdAt).toLocaleString('zh-CN') : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" align="center">
          <template #default="{ row }">
            <div class="action-btns">
              <button class="action-btn edit-btn" :disabled="row.id === currentUserId" @click="openEditDialog(row)">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                修改
              </button>
              <button v-if="row.userStatus === 'active'" class="action-btn disable-btn" :disabled="row.id === currentUserId" @click="handleToggleStatus(row)">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
                停用
              </button>
              <button v-else class="action-btn enable-btn" @click="handleToggleStatus(row)">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#67c23a" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                启用
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="table-footer">
        <span class="table-total">共 {{ total }} 条记录</span>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next" @current-change="fetchUsers" />
      </div>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="480px" destroy-on-close>
      <el-form :model="formData" label-width="80px">
        <el-form-item v-if="dialogMode === 'create'" label="用户名">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item v-if="dialogMode === 'create'" label="密码">
          <el-input v-model="formData.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="formData.role" style="width:100%">
            <el-option v-for="item in roleOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="dialogMode === 'edit'" label="状态">
          <el-select v-model="formData.status" style="width:100%">
            <el-option label="启用" value="active" />
            <el-option label="停用" value="disabled" />
          </el-select>
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
import { ElMessage } from 'element-plus'
import { listUsers, createUser, updateUser } from '@/api/admin'
import { useUserStore } from '@/stores/user'
import type { UserInfo } from '@/types'

const userStore = useUserStore()

const loading = ref(false)
const submitting = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const userList = ref<UserInfo[]>([])
const total = ref(0)

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editingUserId = ref<number | null>(null)

const currentUserId = computed(() => userStore.userInfo?.id ?? null)

interface FormData {
  username: string
  password: string
  role: string
  status: string
}

const formData = ref<FormData>({
  username: '',
  password: '',
  role: 'user',
  status: 'active',
})

const dialogTitle = computed(() => (dialogMode.value === 'create' ? '新增账号' : '修改用户'))

const roleOptions = [
  { label: '普通用户', value: 'user' },
  { label: '法务审核员', value: 'legalReviewer' },
  { label: '风控审核员', value: 'riskReviewer' },
  { label: '管理员', value: 'admin' },
]

const roleLabelMap: Record<string, string> = {
  user: '普通用户',
  legalReviewer: '法务审核员',
  riskReviewer: '风控审核员',
  admin: '管理员',
}

const avatarColors = ['#1a6fc4', '#e6a23c', '#67c23a', '#f56c6c', '#909399', '#6c63a0']

function getAvatarColor(id: number) {
  return avatarColors[id % avatarColors.length]
}

function getAvatarText(name: string) {
  return name.slice(0, 2).toUpperCase()
}

async function fetchUsers() {
  loading.value = true
  try {
    const res = await listUsers({
      page: currentPage.value,
      pageSize: pageSize.value,
      username: searchKeyword.value || undefined,
    })
    userList.value = res.items
    total.value = res.total
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  currentPage.value = 1
  fetchUsers()
}

function openCreateDialog() {
  dialogMode.value = 'create'
  editingUserId.value = null
  formData.value = { username: '', password: '', role: 'user', status: 'active' }
  dialogVisible.value = true
}

function openEditDialog(row: UserInfo) {
  dialogMode.value = 'edit'
  editingUserId.value = row.id
  formData.value = {
    username: row.username,
    password: '',
    role: row.role,
    status: row.userStatus,
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  submitting.value = true
  try {
    if (dialogMode.value === 'create') {
      if (!formData.value.username || !formData.value.password) {
        ElMessage.warning('请填写用户名和密码')
        submitting.value = false
        return
      }
      await createUser({
        username: formData.value.username,
        password: formData.value.password,
        role: formData.value.role,
      })
      ElMessage.success('用户创建成功')
    } else {
      if (editingUserId.value === null) return
      await updateUser(editingUserId.value, {
        role: formData.value.role,
        status: formData.value.status,
      })
      ElMessage.success('用户信息已更新')
    }
    dialogVisible.value = false
    fetchUsers()
  } catch {
    // error handled by interceptor
  } finally {
    submitting.value = false
  }
}

async function handleToggleStatus(row: UserInfo) {
  if (row.id === currentUserId.value) {
    ElMessage.warning('不能停用自己的账号')
    return
  }
  const newStatus = row.userStatus === 'active' ? 'disabled' : 'active'
  try {
    await updateUser(row.id, { status: newStatus })
    ElMessage.success(newStatus === 'active' ? '已启用' : '已停用')
    fetchUsers()
  } catch {
    // error handled by interceptor
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
.user-mgmt-page { }

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

/* 搜索栏 */
.search-bar {
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

.search-input-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 320px;
}

.search-icon {
  flex-shrink: 0;
}

.search-input :deep(.el-input__wrapper) {
  box-shadow: none;
  border: none;
}

.search-input :deep(.el-input__inner) {
  font-size: 14px;
}

.btn-filter {
  height: 36px;
  font-size: 14px;
  background: #fff;
  border: 1px solid #dcdfe6;
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

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
}

.current-tag {
  font-size: 12px;
}

.user-id-label {
  font-size: 12px;
  color: #909399;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  padding: 4px 12px;
  border-radius: 4px;
}

.status-active {
  background: #f0f9f0;
  color: #67c23a;
}

.status-disabled {
  background: #f4f4f5;
  color: #909399;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot-green {
  background: #67c23a;
}

.dot-gray {
  background: #909399;
}

.action-btns {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 13px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.edit-btn {
  color: #1a6fc4;
}

.edit-btn:hover:not(:disabled) {
  background: #ecf5ff;
}

.disable-btn {
  color: #f56c6c;
}

.disable-btn:hover:not(:disabled) {
  background: #fef0f0;
}

.enable-btn {
  color: #67c23a;
}

.enable-btn:hover {
  background: #f0f9f0;
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
