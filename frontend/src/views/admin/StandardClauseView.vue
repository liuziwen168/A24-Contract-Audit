 <template>
   <div class="admin-page">
     <div class="list-header">
       <h2>标准条款管理</h2>
       <el-button type="primary" @click="openEdit(null)" :icon="Plus">新增条款</el-button>
     </div>
     <div class="table-card">
       <el-table :data="clauses" v-loading="loading" stripe style="width:100%">
         <el-table-column prop="name" label="条款名" width="140" />
         <el-table-column label="合同类型" width="130">
           <template #default="{ row }"><el-tag size="small" effect="plain" style="background:#eef0ff;color:#4361ee;border:none;font-weight:500">{{ CONTRACT_TYPE_LABELS[row.contractType] }}</el-tag></template>
         </el-table-column>
         <el-table-column prop="clauseType" label="类别" width="120" />
         <el-table-column prop="content" label="内容" min-width="280" show-overflow-tooltip />
         <el-table-column label="状态" width="80">
           <template #default="{ row }"><el-tag :type="row.configStatus === 'active' ? 'success' : 'danger'" size="small" effect="dark">{{ row.configStatus === 'active' ? '启用' : '停用' }}</el-tag></template>
         </el-table-column>
         <el-table-column label="操作" width="80" fixed="right">
           <template #default="{ row }"><el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button></template>
         </el-table-column>
       </el-table>
       <div class="pagination-wrap"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchClauses" /></div>
     </div>
 
     <el-dialog v-model="dialogVisible" :title="editingId ? '编辑条款' : '新增条款'" width="600px" :close-on-click-modal="false">
       <el-form :model="form" label-width="100px">
         <el-form-item label="条款名"><el-input v-model="form.name" /></el-form-item>
         <el-form-item label="合同类型"><el-select v-model="form.contractType" style="width:100%"><el-option v-for="(l, v) in CONTRACT_TYPE_LABELS" :key="v" :label="l" :value="v" /></el-select></el-form-item>
         <el-form-item label="条款类别"><el-input v-model="form.clauseType" /></el-form-item>
         <el-form-item label="内容"><el-input v-model="form.content" type="textarea" :rows="4" /></el-form-item>
         <el-form-item label="状态"><el-switch v-model="form.active" active-text="启用" inactive-text="停用" /></el-form-item>
       </el-form>
       <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveClause">保存</el-button></template>
     </el-dialog>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { ElMessage } from 'element-plus'
 import { Plus } from '@element-plus/icons-vue'
 import { getStandardClauseList, createStandardClause, updateStandardClause } from '@/api/admin'
 import type { StandardClause } from '@/types'
 import { CONTRACT_TYPE_LABELS } from '@/types'
 const clauses = ref<StandardClause[]>([]); const loading = ref(false); const page = ref(1); const pageSize = ref(20); const total = ref(0)
 const dialogVisible = ref(false); const saving = ref(false); const editingId = ref<number | null>(null)
 const form = ref({ name: '', contractType: 'purchase', clauseType: '', content: '', active: true })
 
 onMounted(() => fetchClauses())
 async function fetchClauses() { loading.value = true; try { const r = await getStandardClauseList({ page: page.value, pageSize: pageSize.value }); clauses.value = r.data.items; total.value = r.data.total } catch { /* */ } finally { loading.value = false } }
 function openEdit(row: StandardClause | null) {
   if (row) { editingId.value = row.id; form.value = { name: row.name, contractType: row.contractType, clauseType: row.clauseType, content: row.content, active: row.configStatus === 'active' } }
   else { editingId.value = null; form.value = { name: '', contractType: 'purchase', clauseType: '', content: '', active: true } }
   dialogVisible.value = true
 }
 async function saveClause() {
   saving.value = true; const data = { ...form.value, configStatus: form.value.active ? 'active' : 'disabled' }
   try { if (editingId.value) { await updateStandardClause(editingId.value, data); ElMessage.success('已更新') } else { await createStandardClause(data); ElMessage.success('已创建') } dialogVisible.value = false; fetchClauses() } catch { /* */ } finally { saving.value = false }
 }
 </script>
 
 <style scoped>
 .admin-page { max-width: 1100px; margin: 0 auto; }
 .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
 .list-header h2 { font-size: 20px; font-weight: 700; }
 .table-card { background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 </style>
