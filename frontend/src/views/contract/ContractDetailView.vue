 <template>
   <div class="contract-detail">
     <div class="detail-header">
       <h2>合同详情</h2>
       <el-button @click="router.back()" text>
         <el-icon><ArrowLeft /></el-icon> 返回
       </el-button>
     </div>
 
     <div class="content-card" v-loading="loading">
       <div v-if="contractDetail">
         <div class="detail-grid">
           <div class="detail-field">
             <span class="field-label">合同名称</span>
             <span class="field-value">{{ contractDetail.contract.name }}</span>
           </div>
           <div class="detail-field">
             <span class="field-label">合同类型</span>
             <span class="field-value">
               <el-tag v-if="contractDetail.contract.contractType" size="small" effect="plain" style="background:#eef0ff;color:#4361ee;border:none">
                 {{ CONTRACT_TYPE_LABELS[contractDetail.contract.contractType] }}
               </el-tag>
               <span v-else class="text-muted">未分类</span>
             </span>
           </div>
           <div class="detail-field">
             <span class="field-label">状态</span>
             <span class="field-value">
               <el-tag :type="statusTag" size="small" effect="dark">{{ CONTRACT_STATUS_LABELS[contractDetail.contract.status] }}</el-tag>
             </span>
           </div>
           <div class="detail-field">
             <span class="field-label">上传时间</span>
             <span class="field-value">{{ formatTime(contractDetail.contract.createdAt) }}</span>
           </div>
         </div>
 
         <div class="section-block">
           <div class="block-title"><el-icon><FolderOpened /></el-icon> 原始文件</div>
           <el-table :data="contractDetail.files" stripe size="small">
             <el-table-column prop="fileName" label="文件名" />
             <el-table-column prop="fileType" label="格式" width="80" />
             <el-table-column label="大小" width="100">
               <template #default="{ row }">{{ formatFileSize(row.fileSize) }}</template>
             </el-table-column>
           </el-table>
         </div>
 
         <div v-if="contractDetail.latestReview" class="section-block">
           <div class="block-title"><el-icon><Search /></el-icon> 最近审核</div>
           <div class="review-card">
             <div class="review-info">
               <span class="review-tag">审核ID: {{ contractDetail.latestReview.id }}</span>
               <el-tag size="small" :type="statusTag" effect="dark">{{ CONTRACT_STATUS_LABELS[contractDetail.contract.status] }}</el-tag>
               <span class="review-stage">{{ REVIEW_STAGE_LABELS[contractDetail.latestReview.reviewStage] }}</span>
             </div>
             <el-button type="primary" size="small" @click="router.push(`/reviews/${contractDetail!.latestReview!.id}`)">查看审核详情</el-button>
           </div>
         </div>
       </div>
       <el-empty v-else-if="!loading" description="未找到合同信息" />
     </div>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, computed, onMounted } from 'vue'
 import { useRoute, useRouter } from 'vue-router'
 import { getContractDetail } from '@/api/contract'
 import type { ContractDetail } from '@/types'
 import { CONTRACT_TYPE_LABELS, CONTRACT_STATUS_LABELS, REVIEW_STATUS_LABELS, REVIEW_STAGE_LABELS } from '@/types'
 import { formatFileSize } from '@/utils/helpers'
 import { ArrowLeft, FolderOpened, Search } from '@element-plus/icons-vue'
 
 const route = useRoute()
 const router = useRouter()
 const contractDetail = ref<ContractDetail | null>(null)
 const loading = ref(true)
 
 const statusTag = computed(() => {
   const map: Record<string, string> = { uploaded: '', reviewing: 'warning', reviewed: 'success', failed: 'danger', deleted: '' }
   return map[contractDetail.value?.contract?.status || ''] || 'info'
 })
 
 onMounted(async () => {
   const id = Number(route.params.id)
   if (isNaN(id)) { loading.value = false; return }
   try { const res = await getContractDetail(id); contractDetail.value = res.data }
   catch { /* */ }
   finally { loading.value = false }
 })
 
 function formatTime(t: string) { return t ? t.replace('T', ' ').substring(0, 19) : '-' }
 </script>
 
 <style scoped>
 .contract-detail { max-width: 800px; margin: 0 auto; }
 .detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
 .detail-header h2 { font-size: 20px; font-weight: 700; }
 .content-card { background: #fff; border-radius: 14px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
 .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
 .detail-field { display: flex; flex-direction: column; gap: 4px; }
 .field-label { font-size: 12px; color: var(--color-text-secondary); font-weight: 500; }
 .field-value { font-size: 14px; font-weight: 500; }
 .text-muted { color: var(--color-text-secondary); }
 
 .section-block { margin-top: 20px; }
 .block-title { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 600; margin-bottom: 12px; color: var(--color-text); }
 
 .review-card {
   display: flex; justify-content: space-between; align-items: center;
   padding: 16px; background: #f8fafc; border-radius: 10px; border: 1px solid var(--color-border);
 }
 .review-info { display: flex; align-items: center; gap: 10px; font-size: 13px; }
 .review-tag { color: var(--color-text-secondary); }
 .review-stage { font-weight: 500; }
 </style>
