 <template>
   <div class="admin-page">
     <div class="list-header">
       <h2>用户管理</h2>
       <el-button type="primary" size="default" @click="showAddDialog = true" :icon="Plus">新增用户</el-button>
     </div>
     <div class="table-card">
       <el-table :data="users" v-loading="loading" stripe style="width:100%">
         <el-table-column prop="id" label="ID" width="60" />
         <el-table-column prop="username" label="用户名" width="160" />
         <el-table-column label="角色" width="140">
           <template #default="{ row }">
             <el-tag :type="roleTagType(row.role)" size="small" effect="dark">{{ USER_ROLE_LABELS[row.role] }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="状态" width="100">
           <template #default="{ row }">
             <el-tag :type="row.userStatus === 'active' ? 'success' : 'danger'" size="small" effect="dark">
               {{ row.userStatus === 'active' ? '正常' : '停用' }}
             </el-tag>
           </template>
         </el-table-column>
         <el-table-column label="操作" width="120" fixed="right">
           <template #default="{ row }">
             <el-button text :type="row.userStatus === 'active' ? 'warning' : 'success'" size="small" @click="toggleStatus(row)">
               {{ row.userStatus === 'active' ? '停用' : '启用' }}
             </el-button>
           </template>
         </el-table-column>
       </el-table>
       <div class="pagination-wrap">
         <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchUsers" />
       </div>
     </div>
 
     <el-dialog v-model="showAddDialog" title="新增用户" width="460px" :close-on-click-modal="false">
       <el-form :model="addForm" label-width="70px">
         <el-form-item label="用户名"><el-input v-model="addForm.username" placeholder="请输入用户名" /></el-form-item>
         <el-form-item label="密码"><el-input v-model="addForm.password" type="password" placeholder="请输入密码" show-password /></el-form-item>
         <el-form-item label="角色">
           <el-select v-model="addForm.role" style="width:100%">
             <el-option label="普通用户" value="user" />
             <el-option label="法务审核员" value="legalReviewer" />
             <el-option label="风控审核员" value="riskReviewer" />
             <el-option label="管理员" value="admin" />
           </el-select>
         </el-form-item>
       </el-form>
       <template #footer>
         <el-button @click="showAddDialog = false">取消</el-button>
         <el-button type="primary" :loading="saving" @click="addUser">保存</el-button>
       </template>
     </el-dialog>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { ElMessage } from 'element-plus'
 import { Plus } from '@element-plus/icons-vue'
 import { getUserList, createUser, updateUserStatus } from '@/api/admin'
 import type { User } from '@/types'
 import { USER_ROLE_LABELS } from '@/types'
 
 const users = ref<User[]>([]); const loading = ref(false); const page = ref(1); const pageSize = ref(20); const total = ref(0)
 const showAddDialog = ref(false); const saving = ref(false)
 const addForm = ref({ username: '', password: '', role: 'user' })
 
 onMounted(() => fetchUsers())
 async function fetchUsers() {
   loading.value = true
   try { const res = await getUserList({ page: page.value, pageSize: pageSize.value }); users.value = res.data.items; total.value = res.data.total }
   catch { /* */ } finally { loading.value = false }
 }
 function roleTagType(role: string) { const map: Record<string, string> = { admin: 'danger', legalReviewer: 'warning', riskReviewer: 'success', user: '' }; return map[role] || 'info' }
 async function toggleStatus(user: User) { try { await updateUserStatus(user.id, user.userStatus === 'active' ? 'disabled' : 'active'); ElMessage.success('状态已更新'); fetchUsers() } catch { /* */ } }
 async function addUser() {
   saving.value = true
   try { await createUser(addForm.value); ElMessage.success('用户已创建'); showAddDialog.value = false; addForm.value = { username: '', password: '', role: 'user' }; fetchUsers() }
   catch { /* */ } finally { saving.value = false }
 }
 </script>
 
 <style scoped>
 .admin-page { max-width: 1000px; margin: 0 auto; }
 .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
 .list-header h2 { font-size: 20px; font-weight: 700; }
 .table-card { background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 </style>
