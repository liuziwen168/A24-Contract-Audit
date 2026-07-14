 <template>
   <div class="admin-page">
     <div class="list-header"><h2>运行日志</h2><span class="header-count" v-if="total">共 {{ total }} 条</span></div>
     <div class="table-card">
       <el-table :data="logs" v-loading="loading" stripe>
         <el-table-column prop="id" label="ID" width="60" />
         <el-table-column prop="userId" label="用户" width="70" />
         <el-table-column prop="action" label="操作" width="160" />
         <el-table-column prop="resourceType" label="资源" width="120" />
         <el-table-column prop="resourceId" label="资源ID" width="80" />
         <el-table-column prop="ip" label="IP" width="140" />
         <el-table-column label="时间" width="170"><template #default="{ row }">{{ formatTime(row.createdAt) }}</template></el-table-column>
       </el-table>
       <div class="pagination-wrap"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchLogs" /></div>
     </div>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { getOperationLogs } from '@/api/admin'
 import type { OperationLog } from '@/types'
 const logs = ref<OperationLog[]>([]); const loading = ref(false); const page = ref(1); const pageSize = ref(20); const total = ref(0)
 onMounted(() => fetchLogs())
 async function fetchLogs() { loading.value = true; try { const r = await getOperationLogs({ page: page.value, pageSize: pageSize.value }); logs.value = r.data.items; total.value = r.data.total } catch { /* */ } finally { loading.value = false } }
 function formatTime(t: string) { return t ? t.replace('T', ' ').substring(0, 19) : '-' }
 </script>
 
 <style scoped>
 .admin-page { max-width: 1100px; margin: 0 auto; }
 .list-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
 .list-header h2 { font-size: 20px; font-weight: 700; }
 .header-count { font-size: 13px; color: var(--color-text-secondary); }
 .table-card { background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 </style>
