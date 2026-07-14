 <template>
   <div class="admin-page">
     <div class="list-header"><h2>反馈记录</h2><span class="header-count" v-if="total">共 {{ total }} 条</span></div>
     <div class="table-card">
       <el-table :data="feedbacks" v-loading="loading" stripe>
         <el-table-column prop="id" label="ID" width="60" />
         <el-table-column prop="reviewId" label="审核ID" width="80" />
         <el-table-column label="类型" width="120"><template #default="{ row }"><el-tag size="small" effect="plain" style="background:#f3f4f6;color:#6b7280;border:none">{{ row.targetType }}</el-tag></template></el-table-column>
         <el-table-column label="判断" width="100"><template #default="{ row }"><el-tag :type="judgmentTag(row.judgment)" size="small" effect="dark">{{ JUDGMENT_LABELS[row.judgment] }}</el-tag></template></el-table-column>
         <el-table-column prop="comment" label="说明" min-width="200" show-overflow-tooltip />
         <el-table-column prop="correctedValue" label="修订值" min-width="150" show-overflow-tooltip />
       </el-table>
       <div class="pagination-wrap"><el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchFeedbacks" /></div>
     </div>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { getFeedbackList } from '@/api/admin'
 import type { ReviewFeedback } from '@/types'
 import { JUDGMENT_LABELS } from '@/types'
 const feedbacks = ref<ReviewFeedback[]>([]); const loading = ref(false); const page = ref(1); const pageSize = ref(20); const total = ref(0)
 onMounted(() => fetchFeedbacks())
 async function fetchFeedbacks() { loading.value = true; try { const r = await getFeedbackList({ page: page.value, pageSize: pageSize.value }); feedbacks.value = r.data.items; total.value = r.data.total } catch { /* */ } finally { loading.value = false } }
 function judgmentTag(j: string) { const map: Record<string, string> = { correct: 'success', incorrect: 'danger', modified: 'warning' }; return map[j] || 'info' }
 </script>
 
 <style scoped>
 .admin-page { max-width: 1000px; margin: 0 auto; }
 .list-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
 .list-header h2 { font-size: 20px; font-weight: 700; }
 .header-count { font-size: 13px; color: var(--color-text-secondary); }
 .table-card { background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 </style>
