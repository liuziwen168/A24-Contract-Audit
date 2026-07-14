 <template>
   <div class="contract-list">
     <!-- Header -->
     <div class="list-header">
       <div class="header-left">
         <h2>合同管理</h2>
         <span class="header-count" v-if="total">共 {{ total }} 份</span>
       </div>
       <div class="header-actions">
         <el-button type="primary" @click="showUploadDialog" :icon="Upload">
           上传合同
         </el-button>
       </div>
     </div>
 
     <!-- Table -->
     <div class="table-card">
       <el-table :data="contracts" v-loading="loading" stripe style="width:100%">
         <el-table-column prop="name" label="合同名称" min-width="200">
           <template #default="{ row }">
             <span class="contract-name">{{ row.name }}</span>
           </template>
         </el-table-column>
         <el-table-column label="合同类型" width="130">
           <template #default="{ row }">
             <el-tag v-if="row.contractType" size="small" effect="plain" style="border:none;background:#eef0ff;color:#4361ee;font-weight:500">
               {{ CONTRACT_TYPE_LABELS[row.contractType] || row.contractType }}
             </el-tag>
             <span v-else class="text-muted">未分类</span>
           </template>
         </el-table-column>
         <el-table-column label="状态" width="110">
           <template #default="{ row }">
             <el-tag :type="statusTagType(row.status)" size="small" effect="dark">{{ CONTRACT_STATUS_LABELS[row.status] }}</el-tag>
           </template>
         </el-table-column>
         <el-table-column label="上传时间" width="170">
           <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
         </el-table-column>
         <el-table-column label="操作" width="220" fixed="right">
           <template #default="{ row }">
             <el-button text size="small" type="primary" @click="viewContract(row.id)">详情</el-button>
             <el-button v-if="row.status === 'uploaded'" text size="small" type="success" @click="startReview(row)">发起审核</el-button>
             <el-button text size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
           </template>
         </el-table-column>
       </el-table>
 
       <div class="pagination-wrap">
         <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchContracts" />
       </div>
     </div>
 
     <!-- Upload Dialog -->
     <el-dialog v-model="uploadDialogVisible" title="上传合同" width="500px" :close-on-click-modal="false">
       <div class="upload-zone" @click="triggerFileInput" @dragover.prevent @drop.prevent="onDrop">
         <input ref="fileInputRef" type="file" accept=".docx,.pdf,.png,.jpg,.jpeg" style="display:none" @change="onFileSelected" />
         <div v-if="!uploadForm.file" class="upload-placeholder">
           <el-icon :size="40" color="#4361ee"><UploadFilled /></el-icon>
           <p>点击或拖拽文件到此处</p>
           <span>支持 DOCX、PDF、PNG、JPG 格式</span>
         </div>
         <div v-else class="upload-preview">
           <el-icon :size="32" color="#4361ee"><Document /></el-icon>
           <div class="file-info">
             <strong>{{ uploadForm.file.name }}</strong>
             <span>{{ formatFileSize(uploadForm.file.size) }}</span>
           </div>
           <el-button text type="danger" size="small" @click.stop="uploadForm.file = null">移除</el-button>
         </div>
       </div>
       <el-form :model="uploadForm" label-width="0" style="margin-top:16px">
         <el-form-item>
           <el-input v-model="uploadForm.name" placeholder="合同名称（留空使用文件名）" :prefix-icon="Edit" />
         </el-form-item>
       </el-form>
       <template #footer>
         <el-button @click="uploadDialogVisible = false">取消</el-button>
         <el-button type="primary" :loading="uploading" @click="confirmUpload">上传</el-button>
       </template>
     </el-dialog>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, onMounted } from 'vue'
 import { useRouter } from 'vue-router'
 import { ElMessage, ElMessageBox } from 'element-plus'
 import { Upload, UploadFilled, Edit, Document } from '@element-plus/icons-vue'
 import { getContractList, uploadContract, deleteContract } from '@/api/contract'
 import { createReview } from '@/api/review'
 import { generateIdempotencyKey, formatFileSize } from '@/utils/helpers'
 import type { Contract } from '@/types'
 import { CONTRACT_TYPE_LABELS, CONTRACT_STATUS_LABELS } from '@/types'
 
 const router = useRouter()
 const contracts = ref<Contract[]>([])
 const loading = ref(false)
 const page = ref(1)
 const pageSize = ref(20)
 const total = ref(0)
 const uploadDialogVisible = ref(false)
 const uploading = ref(false)
 const uploadForm = ref({ file: null as File | null, name: '' })
 const fileInputRef = ref<HTMLInputElement>()
 
 onMounted(() => fetchContracts())
 
 async function fetchContracts() {
   loading.value = true
   try { const res = await getContractList({ page: page.value, pageSize: pageSize.value }); contracts.value = res.data.items; total.value = res.data.total }
   catch { /* */ }
   finally { loading.value = false }
 }
 
 function statusTagType(s: string) {
   const map: Record<string, string> = { uploaded: '', reviewing: 'warning', reviewed: 'success', failed: 'danger', deleted: '' }
   return map[s] || 'info'
 }
 function formatTime(t: string) { return t ? t.replace('T', ' ').substring(0, 19) : '-' }
 function viewContract(id: number) { router.push(`/contracts/${id}`) }
 
 function showUploadDialog() { uploadDialogVisible.value = true }
 function triggerFileInput() { fileInputRef.value?.click() }
 function onFileSelected(e: Event) {
   const target = e.target as HTMLInputElement
   if (target.files?.[0]) { uploadForm.value.file = target.files[0]; if (!uploadForm.value.name) uploadForm.value.name = target.files[0].name.replace(/\.[^/.]+$/, '') }
 }
 function onDrop(e: DragEvent) {
   const file = e.dataTransfer?.files?.[0]
   if (file) { uploadForm.value.file = file; if (!uploadForm.value.name) uploadForm.value.name = file.name.replace(/\.[^/.]+$/, '') }
 }
 
 async function confirmUpload() {
   if (!uploadForm.value.file) { ElMessage.warning('请选择文件'); return }
   uploading.value = true
   try { await uploadContract(uploadForm.value.file, uploadForm.value.name || undefined); ElMessage.success('上传成功'); uploadDialogVisible.value = false; uploadForm.value = { file: null, name: '' }; fetchContracts() }
   catch { /* */ }
   finally { uploading.value = false }
 }
 
 async function startReview(contract: Contract) {
   try {
     await ElMessageBox.confirm(`确认对"${contract.name}"发起AI审核?`, '确认')
     const res = await createReview(contract.id, 0, 'full', generateIdempotencyKey())
     ElMessage.success('审核任务已创建')
     router.push(`/reviews/${res.data.reviewId}`)
   } catch { /* */ }
 }
 
 async function handleDelete(id: number) {
   try { await ElMessageBox.confirm('确认删除该合同?', '确认', { type: 'warning' }); await deleteContract(id); ElMessage.success('已删除'); fetchContracts() }
   catch { /* */ }
 }
 </script>
 
 <style scoped>
 .contract-list { max-width: 1100px; margin: 0 auto; }
 .list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
 .header-left { display: flex; align-items: center; gap: 12px; }
 .header-left h2 { font-size: 20px; font-weight: 700; }
 .header-count { font-size: 13px; color: var(--color-text-secondary); }
 .table-card {
   background: #fff; border-radius: 14px; padding: 0;
   box-shadow: 0 1px 3px rgba(0,0,0,0.06); overflow: hidden;
 }
 .contract-name { font-weight: 500; }
 .text-muted { color: var(--color-text-secondary); }
 .pagination-wrap { padding: 16px 20px; display: flex; justify-content: flex-end; }
 
 /* Upload Zone */
 .upload-zone {
   border: 2px dashed #d1d5db; border-radius: 12px; padding: 32px; text-align: center;
   cursor: pointer; transition: all 0.2s; background: #f8fafc;
 }
 .upload-zone:hover { border-color: #4361ee; background: #eef0ff; }
 .upload-placeholder p { margin: 12px 0 4px; font-size: 15px; font-weight: 600; color: var(--color-text); }
 .upload-placeholder span { font-size: 12px; color: var(--color-text-secondary); }
 .upload-preview { display: flex; align-items: center; gap: 12px; justify-content: center; }
 .file-info { text-align: left; }
 .file-info strong { display: block; font-size: 14px; }
 .file-info span { font-size: 12px; color: var(--color-text-secondary); }
 </style>
