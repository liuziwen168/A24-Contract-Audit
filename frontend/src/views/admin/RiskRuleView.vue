 <template>
   <div class="admin-page">
     <div class="list-header">
       <h2>风险规则管理</h2>
       <el-button type="primary" @click="openEdit(null)" :icon="Plus">新增规则</el-button>
     </div>
     <div class="table-card">
       <el-table :data="rules" v-loading="loading" stripe style="width:100%">
         <el-table-column prop="ruleCode" label="编号" width="90" />
         <el-table-column prop="name" label="规则名称" width="140" />
         <el-table-column prop="riskType" label="风险类型" width="140" />
         <el-table-column label="等级" width="80">
           <template #default="{ row }"><el-tag :color="getRiskColor(row.riskLevel)" style="color:#fff;border:none" size="small">{{ getRiskLevelLabel(row.riskLevel) }}</el-tag></template>
         </el-table-column>
         <el-table-column prop="ruleContent" label="规则内容" min-width="260" show-overflow-tooltip />
         <el-table-column label="状态" width="70">
           <template #default="{ row }"><el-tag :type="row.configStatus === 'active' ? 'success' : 'danger'" size="small" effect="dark">{{ row.configStatus === 'active' ? '启用' : '停用' }}</el-tag></template>
         </el-table-column>
         <el-table-column label="操作" width="80" fixed="right">
           <template #default="{ row }"><el-button text type="primary" size="small" @click="openEdit(row)">编辑</el-button></template>
         </el-table-column>
       </el-table>
       <div class="pagination-wrap"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchRules" /></div>
     </div>
 
     <el-dialog v-model="dialogVisible" :title="editingId ? '编辑规则' : '新增规则'" width="600px" :close-on-click-modal="false">
       <el-form :model="form" label-width="90px">
         <el-form-item label="规则编号"><el-input v-model="form.ruleCode" /></el-form-item>
         <el-form-item label="规则名称"><el-input v-model="form.name" /></el-form-item>
         <el-form-item label="风险类型"><el-input v-model="form.riskType" /></el-form-item>
         <el-form-item label="风险等级"><el-select v-model="form.riskLevel" style="width:100%"><el-option label="高" value="high" /><el-option label="中" value="medium" /><el-option label="低" value="low" /></el-select></el-form-item>
         <el-form-item label="规则内容"><el-input v-model="form.ruleContent" type="textarea" :rows="4" /></el-form-item>
         <el-form-item label="状态"><el-switch v-model="form.active" active-text="启用" inactive-text="停用" /></el-form-item>
       </el-form>
       <template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveRule">保存</el-button></template>
     </el-dialog>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { ElMessage } from 'element-plus'
 import { Plus } from '@element-plus/icons-vue'
 import { getRiskRuleList, createRiskRule, updateRiskRule } from '@/api/admin'
 import type { RiskRule } from '@/types'
 import { getRiskColor, getRiskLevelLabel } from '@/utils/helpers'
 const rules = ref<RiskRule[]>([]); const loading = ref(false); const page = ref(1); const pageSize = ref(20); const total = ref(0)
 const dialogVisible = ref(false); const saving = ref(false); const editingId = ref<number | null>(null)
 const form = ref({ ruleCode: '', name: '', riskType: '', riskLevel: 'medium', ruleContent: '', active: true })
 
 onMounted(() => fetchRules())
 async function fetchRules() { loading.value = true; try { const r = await getRiskRuleList({ page: page.value, pageSize: pageSize.value }); rules.value = r.data.items; total.value = r.data.total } catch { /* */ } finally { loading.value = false } }
 function openEdit(row: RiskRule | null) {
   if (row) { editingId.value = row.id; form.value = { ruleCode: row.ruleCode, name: row.name, riskType: row.riskType, riskLevel: row.riskLevel, ruleContent: row.ruleContent, active: row.configStatus === 'active' } }
   else { editingId.value = null; form.value = { ruleCode: '', name: '', riskType: '', riskLevel: 'medium', ruleContent: '', active: true } }
   dialogVisible.value = true
 }
 async function saveRule() {
   saving.value = true; const data = { ...form.value, configStatus: form.value.active ? 'active' : 'disabled' }
   try { if (editingId.value) { await updateRiskRule(editingId.value, data); ElMessage.success('已更新') } else { await createRiskRule(data); ElMessage.success('已创建') } dialogVisible.value = false; fetchRules() } catch { /* */ } finally { saving.value = false }
 }
 </script>
 
 <style scoped>
 .admin-page { max-width: 1100px; margin: 0 auto; }
 .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
 .list-header h2 { font-size: 20px; font-weight: 700; }
 .table-card { background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 </style>
