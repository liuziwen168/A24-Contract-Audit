 <template>
   <div class="review-history">
     <div class="list-header">
       <h2>审核历史</h2>
       <span class="header-count" v-if="total">共 {{ total }} 条</span>
     </div>
 
     <div class="table-card">
       <el-table :data="reviews" v-loading="loading" stripe style="width:100%">
         <el-table-column prop="id" label="审核ID" width="70" />
         <el-table-column prop="contractId" label="合同ID" width="70" />
         <el-table-column label="状态" width="110">
           <template #default="{ row }">
             <el-tag :type="statusTagType(row.status)" size="small" effect="dark">{{ REVIEW_STATUS_LABELS[row.status] }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="阶段" width="110">
           <template #default="{ row }">
             <el-tag type="info" size="small" effect="plain" style="border:none;background:#f3f4f6;color:#6b7280;font-weight:500">
               {{ REVIEW_STAGE_LABELS[row.reviewStage] }}
             </el-tag>
           </template>
         </el-table-column>
         <el-table-column label="总体风险" width="110">
           <template #default="{ row }">
             <el-tag v-if="row.overallRiskLevel" :color="getRiskColor(row.overallRiskLevel)" style="color:#fff;border:none" size="small">
               {{ getRiskLevelLabel(row.overallRiskLevel) }}
             </el-tag>
             <span v-else class="text-muted">-</span>
           </template>
         </el-table-column>
         <el-table-column label="创建时间" width="170">
           <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
         </el-table-column>
         <el-table-column label="操作" width="80" fixed="right">
           <template #default="{ row }">
             <el-button text size="small" type="primary" @click="viewReview(row.id)">详情</el-button>
           </template>
         </el-table-column>
       </el-table>
 
       <div class="pagination-wrap">
         <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchReviews" />
       </div>
     </div>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { useRouter } from 'vue-router'
 import { getReviewHistory } from '@/api/review'
 import type { ReviewRecord } from '@/types'
 import { REVIEW_STATUS_LABELS, REVIEW_STAGE_LABELS } from '@/types'
 import { getRiskColor, getRiskLevelLabel } from '@/utils/helpers'
 
 const router = useRouter()
 const reviews = ref<ReviewRecord[]>([])
 const loading = ref(false)
 const page = ref(1)
 const pageSize = ref(20)
 const total = ref(0)
 
 onMounted(() => fetchReviews())
 
 async function fetchReviews() {
   loading.value = true
   try { const res = await getReviewHistory({ page: page.value, pageSize: pageSize.value }); reviews.value = res.data.items; total.value = res.data.total }
   catch { /* */ }
   finally { loading.value = false }
 }
 
 function statusTagType(s: string) {
   const map: Record<string, string> = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger', cancelled: '' }
   return map[s] || 'info'
 }
 function formatTime(t: string) { return t ? t.replace('T', ' ').substring(0, 19) : '-' }
 function viewReview(id: number) { router.push(`/reviews/${id}`) }
 </script>
 
 <style scoped>
 .review-history { max-width: 1000px; margin: 0 auto; }
 .list-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
 .list-header h2 { font-size: 20px; font-weight: 700; }
 .header-count { font-size: 13px; color: var(--color-text-secondary); }
 .table-card { background: #fff; border-radius: 14px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 .text-muted { color: var(--color-text-secondary); }
 </style>
