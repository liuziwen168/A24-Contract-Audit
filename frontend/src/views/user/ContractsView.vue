<template>
  <div class="contracts-page" v-loading="loading">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card" v-for="card in statCards" :key="card.label">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value" :class="card.colorClass">{{ card.value }}</div>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" class="btn-upload" @click="showUpload = true">
        <el-icon><Upload /></el-icon> 上传合同
      </el-button>
      <el-button class="btn-report" @click="$router.push('/user/reports')">
        <el-icon><View /></el-icon> 查看审核报告
      </el-button>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <span class="filter-label">合同类型:</span>
        <el-select v-model="filters.contractType" placeholder="全部类型" style="width:140px" @change="fetchContracts">
          <el-option label="全部类型" value="" />
          <el-option label="采购合同" value="purchase" />
          <el-option label="销售合同" value="sales" />
          <el-option label="保密协议" value="nda" />
          <el-option label="服务外包" value="outsourcing" />
          <el-option label="劳动合同" value="labor" />
        </el-select>
      </div>
      <div class="filter-item">
        <span class="filter-label">合同状态:</span>
        <el-select v-model="filters.contractStatus" placeholder="全部状态" style="width:140px" @change="fetchContracts">
          <el-option label="全部状态" value="" />
          <el-option label="已上传" value="uploaded" />
          <el-option label="审核中" value="reviewing" />
          <el-option label="审核完成" value="reviewed" />
          <el-option label="审核失败" value="failed" />
        </el-select>
      </div>
      <el-button link type="primary" class="reset-btn" @click="resetFilters">
        <el-icon><Refresh /></el-icon> 重置筛选
      </el-button>
    </div>

    <!-- 合同列表 -->
    <div class="task-table-card">
      <div class="table-header">
        <span class="table-title">合同列表</span>
        <span class="table-total">共 {{ total }} 条记录</span>
      </div>
      <el-table :data="contractList" stripe style="width:100%" :row-class-name="rowClass" row-key="contractId" :expand-row-keys="expandKeys" @expand-change="onExpand">
        <el-table-column prop="name" label="合同名称" min-width="220" />
        <el-table-column label="合同类型" width="120">
          <template #default="{ row }">
            {{ contractTypeLabels[row.contractType] || row.contractType || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.contractStatus)" size="small" effect="plain">
              {{ statusLabels[row.contractStatus] || row.contractStatus }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="updatedAt" label="更新时间" width="180">
          <template #default="{ row }">{{ formatDate(row.updatedAt) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="toggleDetail(row)">查看</el-button>
            <el-button link type="success" @click.stop="handleRetryReview(row)" :loading="retryingId === row.contractId">重新审核</el-button>
            <el-button link type="danger" @click.stop="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>

        <!-- 展开的审核联动面板 -->
        <el-table-column type="expand" width="1">
          <template #default="{ row }">
            <div v-if="expandedId === row.contractId" class="expand-panel" v-loading="detailLoading">
              <div class="expand-contract-info">
                <div class="expand-contract-left">
                  <div class="expand-icon">
                    <svg viewBox="0 0 24 24" fill="none"><path d="M14 3H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V9z" stroke="currentColor" stroke-width="1.8"/><path d="M14 3v6h6" stroke="currentColor" stroke-width="1.8"/></svg>
                  </div>
                  <div>
                    <strong>{{ row.name }}</strong>
                    <div class="expand-meta">
                      <span>{{ contractTypeLabels[row.contractType] || '-' }}</span>
                      <span>文件：{{ detailContract?.files?.[0]?.fileName || '-' }}</span>
                      <span>{{ detailContract?.files?.[0]?.fileSize ? formatFileSize(detailContract.files[0].fileSize) : '' }}</span>
                    </div>
                  </div>
                </div>
                <div class="expand-contract-right">
                  <el-button size="small" @click.stop="downloadFile(row.contractId, detailContract?.files?.[0]?.contractFileId || 0)" :disabled="!detailContract?.files?.[0]">下载原文件</el-button>
                  <el-button size="small" type="primary" @click.stop="handleRetryReview(row)">发起新审核</el-button>
                </div>
              </div>

              <!-- 审核记录 -->
              <div v-if="detailReviews.length" class="expand-reviews">
                <div class="expand-reviews-title">审核记录（{{ detailReviews.length }} 条）</div>
                <div class="review-timeline">
                  <div v-for="(rv, i) in detailReviews" :key="rv.id" class="timeline-item">
                    <div class="timeline-dot" :class="rv.reviewStage || 'aiReview'"></div>
                    <div class="timeline-card" @click.stop="goToReview(rv.id)">
                      <div class="timeline-head">
                        <span class="timeline-id">#{{ rv.id }}</span>
                        <el-tag :type="stageTag(rv.reviewStage)" size="small" effect="dark">{{ stageLabels[rv.reviewStage] || rv.reviewStage }}</el-tag>
                        <el-tag v-if="rv.overallRiskLevel" :type="levelTag(rv.overallRiskLevel)" size="small">{{ levelLabels[rv.overallRiskLevel] || rv.overallRiskLevel }}</el-tag>
                        <span v-if="rv.overallScore != null" class="timeline-score">评分 {{ rv.overallScore }}</span>
                      </div>
                      <div class="timeline-meta">
                        <span>{{ formatDate(rv.createdAt) }}</span>
                        <span v-if="rv.errorCode" class="timeline-error">错误：{{ rv.errorMessage || rv.errorCode }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else class="expand-empty">暂无审核记录，点击"发起新审核"开始</div>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <div class="page-size">
          <span>每页显示</span>
          <el-select v-model="pageSize" style="width:80px;margin:0 8px" @change="fetchContracts">
            <el-option :value="10" label="10 条" />
            <el-option :value="20" label="20 条" />
          </el-select>
        </div>
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next, jumper"
          @current-change="fetchContracts"
        />
      </div>
    </div>

        <!-- 上传对话框 -->
    <el-dialog v-model="showUpload" title="上传合同" width="500px" @close="resetUpload">
      <el-upload
        drag
        :http-request="customUpload"
        :before-upload="beforeUpload"
        :file-list="fileList"
        :limit="1"
        accept=".pdf,.docx,.doc,.jpg,.jpeg,.png"
        class="enhanced-upload"
      >
        <div class="upload-drop-area">
          <div class="upload-icon-box">
            <svg viewBox="0 0 48 48" fill="none" width="44" height="44">
              <path d="M24 10v20M14 22l10-12 10 12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M10 34h28" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="upload-text">
            <strong>将文件拖到此处</strong>
            <span>或 <em>点击选择文件</em></span>
          </div>
        </div>
        <template #tip>
          <div class="upload-tip-bar">
            <span class="tip-chip">PDF</span>
            <span class="tip-chip">DOCX</span>
            <span class="tip-chip">JPG</span>
            <span class="tip-chip">PNG</span>
            <span class="tip-limit">最大 20MB</span>
          </div>
        </template>
      </el-upload>
      <div v-if="uploading" class="upload-progress-bar">
        <el-progress :percentage="uploadPercent" :stroke-width="10" :color="uploadPercent >= 100 ? '#42c98a' : '#1a6fc4'" :striped="uploadPercent < 100" :striped-flow="uploadPercent < 100" />
        <span class="progress-text">{{ uploadPercent >= 100 ? '上传完成，正在发起审核…' : '上传中 ' + uploadPercent + '%' }}</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, View, Refresh } from '@element-plus/icons-vue'
import { listContracts, deleteContract, downloadContract, uploadContract, getContract } from '@/api/contracts'
import { createReview, listReviews as fetchReviews } from '@/api/reviews'
import type { Contract } from '@/types'

const router = useRouter()

const contractTypeLabels: Record<string, string> = {
  purchase: '采购合同', sales: '销售合同', nda: '保密协议', outsourcing: '服务外包', labor: '劳动合同',
}
const statusLabels: Record<string, string> = { uploaded: '已上传', reviewing: '审核中', reviewed: '审核完成', failed: '审核失败', deleted: '已删除' }
const stageLabels: Record<string, string> = { pending: '等待AI', aiReview: 'AI初审', legalReview: '法务复核', riskReview: '风控复核', completed: '已完成', failed: '失败' }
const levelLabels: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' }

const statCards = ref([
  { label: '合同总数', value: '0', colorClass: '' },
  { label: '审核中', value: '0', colorClass: 'text-blue' },
  { label: '已完成', value: '0', colorClass: '' },
  { label: '审核失败', value: '0', colorClass: 'text-red' },
])

const loading = ref(false)
const contractList = ref<Contract[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const filters = reactive({ contractType: '', contractStatus: '' })

const showUpload = ref(false)
const uploading = ref(false)
const fileList = ref<any[]>([]); const uploadPercent = ref(0)

// 展开面板
const expandedId = ref(0)
const detailLoading = ref(false)
const detailContract = ref<any>(null)
const detailReviews = ref<any[]>([])

const retryingId = ref(0); const expandKeys = ref<number[]>([])

function getStatusType(status: string) { const m: Record<string, string> = { uploaded: '', reviewing: 'warning', reviewed: 'success', failed: 'danger' }; return m[status] || 'info' }
function stageTag(s: string) { const m: Record<string, string> = { pending: 'info', aiReview: '', legalReview: 'warning', riskReview: 'danger', completed: 'success', failed: 'danger' }; return m[s] || 'info' }
function levelTag(l: string) { const m: Record<string, string> = { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }; return m[l] || 'info' }
function formatDate(s: string) { if (!s) return '-'; try { return new Date(s).toLocaleString('zh-CN') } catch { return s } }
function formatFileSize(bytes: number) { if (!bytes) return '0 B'; if (bytes < 1024) return bytes + ' B'; if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'; return (bytes / (1024 * 1024)).toFixed(1) + ' MB' }
function rowClass({ row }: any) { return row.contractId === expandedId.value ? 'row-expanded' : '' }

async function toggleDetail(row: Contract) {
  if (expandedId.value === row.contractId) { expandedId.value = 0; expandKeys.value = []; return }
  expandedId.value = row.contractId; expandKeys.value = [row.contractId]
  detailLoading.value = true
  try {
    const [contract, reviews] = await Promise.all([
      getContract(row.contractId),
      fetchReviews({ contractId: row.contractId, pageSize: 50 }),
    ])
    detailContract.value = contract
    detailReviews.value = reviews.items || []
  } catch {
    detailContract.value = null
    detailReviews.value = []
    expandKeys.value = []
  } finally { detailLoading.value = false }
}

function onExpand(row: any, expandedRows: any[]) {
  if (expandedRows.length === 0) { expandedId.value = 0; expandKeys.value = []; return }
  toggleDetail(row)
}

function goToReview(reviewId: number) {
  router.push('/user/reviews')
}

async function fetchContracts() {
  loading.value = true
  try {
    const params: any = { page: currentPage.value, pageSize: pageSize.value }
    if (filters.contractType) params.contractType = filters.contractType
    if (filters.contractStatus) params.contractStatus = filters.contractStatus
    const res = await listContracts(params)
    contractList.value = res.items; total.value = res.total
    const counts: Record<string, number> = {}
    res.items.forEach((c) => { counts[c.contractStatus] = (counts[c.contractStatus] || 0) + 1 })
    statCards.value[0].value = String(res.total)
    statCards.value[1].value = String(counts['reviewing'] || 0)
    statCards.value[2].value = String(counts['reviewed'] || 0)
    statCards.value[3].value = String(counts['failed'] || 0)
  } finally { loading.value = false }
}

function resetFilters() { filters.contractType = ''; filters.contractStatus = ''; currentPage.value = 1; fetchContracts() }

async function downloadFile(contractId: number, fileId: number) {
  if (!fileId) return
  try {
    const res = await downloadContract(contractId, fileId)
    const url = URL.createObjectURL(res.data); const a = document.createElement('a'); a.href = url; a.download = ''; a.click(); URL.revokeObjectURL(url)
  } catch { }
}

async function handleRetryReview(row: Contract) {
  if (!row.contractFileId) {
    try {
      const detail = await getContract(row.contractId)
      const fileId = detail.files?.[0]?.contractFileId
      if (!fileId) { ElMessage.warning('未找到合同文件'); return }
      row.contractFileId = fileId
    } catch { ElMessage.error('获取合同信息失败'); return }
  }
  retryingId.value = row.contractId
  try {
    const key = `retry-${row.contractId}-${Date.now()}`
    await createReview({ contractId: row.contractId, contractFileId: row.contractFileId, reviewMode: 'full' }, key)
    ElMessage.success('已重新发起 AI 审核'); fetchContracts()
  } catch (e: any) {
    if (String(e?.message || '').includes('ALREADY_RUNNING')) ElMessage.warning('该合同已有进行中的审核任务')
  } finally { retryingId.value = 0 }
}

async function handleDelete(row: Contract) {
  try {
    await ElMessageBox.confirm(`确认删除合同「${row.name}」？`, '提示', { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' })
    await deleteContract(row.contractId); ElMessage.success('删除成功'); fetchContracts()
  } catch { }
}

function resetUpload() { fileList.value = []; uploadPercent.value = 0 }
function beforeUpload(file: File) { if (file.size > 20 * 1024 * 1024) { ElMessage.error(chr(39)+"???????? 20MB"+chr(39)); return false }; return true }

async function customUpload(options: any) {
  uploading.value = true; uploadPercent.value = 0
  try {
    uploadPercent.value = 40; const result = await uploadContract(options.file, (pct: number) => { uploadPercent.value = Math.round(pct) }); uploadPercent.value = 90
    const contractId = result.contractId; const contractFileId = result.contractFileId
    if (!contractId || !contractFileId) { ElMessage.error('上传失败'); return }
    try {
      await createReview({ contractId, contractFileId, reviewMode: 'full' }, `auto-${contractId}-${Date.now()}`)
      uploadPercent.value = 100; ElMessage.success('上传成功，AI 审核已自动发起')
    } catch (e: any) {
      uploadPercent.value = 100; ElMessage.success('合同已上传，请手动创建审核')
    }
    setTimeout(() => { fileList.value = []; showUpload.value = false; uploadPercent.value = 0; fetchContracts() }, 600)
  } catch { uploadPercent.value = 0; uploadFileError.value = '上传失败，请重试' }
  finally { uploading.value = false }
}

onMounted(() => fetchContracts())
</script>

<style scoped>
.stat-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
.stat-card { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.stat-label { font-size: 14px; color: #909399; margin-bottom: 12px; }
.stat-value { font-size: 32px; font-weight: 700; color: #303133; }
.stat-value.text-blue { color: #1a6fc4; }
.stat-value.text-red { color: #f56c6c; }
.action-bar { display: flex; gap: 12px; margin-bottom: 20px; }
.btn-upload { background: #1a6fc4; border-color: #1a6fc4; height: 40px; padding: 0 24px; font-size: 14px; }
.btn-report { height: 40px; padding: 0 24px; font-size: 14px; background: #fff; border: 1px solid #dcdfe6; }
.filter-bar { display: flex; align-items: center; gap: 20px; background: #fff; padding: 16px 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); flex-wrap: wrap; }
.filter-item { display: flex; align-items: center; gap: 8px; }
.filter-label { font-size: 14px; color: #606266; white-space: nowrap; }
.reset-btn { margin-left: auto; }
.task-table-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.table-title { font-size: 16px; font-weight: 600; color: #303133; }
.table-total { font-size: 13px; color: #909399; }
.pagination-bar { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; }
.page-size { display: flex; align-items: center; font-size: 14px; color: #606266; }

/* ---- Expand Panel ---- */
:deep(.el-table__expanded-cell) { padding: 0 !important; }
:deep(.row-expanded) { background: #f5f8fc !important; }
.expand-panel { padding: 20px 24px; border-top: 2px solid #1a6fc4; }
.expand-contract-info { display: flex; align-items: center; justify-content: space-between; gap: 20px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #edf0f5; }
.expand-contract-left { display: flex; align-items: center; gap: 14px; }
.expand-icon { width: 40px; height: 40px; border-radius: 10px; background: #e8f3ff; color: #1a6fc4; display: grid; place-items: center; }
.expand-icon svg { width: 20px; height: 20px; }
.expand-contract-left strong { font-size: 15px; color: #1f2a3a; }
.expand-meta { display: flex; gap: 16px; margin-top: 4px; font-size: 12px; color: #8899aa; }
.expand-contract-right { display: flex; gap: 8px; flex-shrink: 0; }
.expand-reviews-title { font-size: 13px; font-weight: 600; color: #4a6388; margin-bottom: 14px; }

/* ---- Timeline ---- */
.review-timeline { display: flex; flex-direction: column; gap: 12px; }
.timeline-item { display: flex; gap: 14px; align-items: flex-start; }
.timeline-dot { width: 12px; height: 12px; border-radius: 50%; margin-top: 10px; flex-shrink: 0; background: #c8d6e4; position: relative; }
.timeline-dot::after { content: ''; position: absolute; top: 12px; left: 5px; width: 2px; height: calc(100% + 12px); background: #e8ecf2; }
.timeline-item:last-child .timeline-dot::after { display: none; }
.timeline-dot.completed { background: #42c98a; }
.timeline-dot.legalReview { background: #8764d8; }
.timeline-dot.riskReview { background: #f0a145; }
.timeline-dot.aiReview { background: #4e9df0; }
.timeline-dot.failed { background: #e85d6f; }
.timeline-dot.pending { background: #c8d6e4; }
.timeline-card { flex: 1; padding: 14px 16px; border-radius: 10px; background: #f8fafc; border: 1px solid #edf0f5; cursor: pointer; transition: all .15s; }
.timeline-card:hover { border-color: #c0d4ec; background: #f0f5fb; box-shadow: 0 2px 6px rgba(26,111,196,.06); }
.timeline-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.timeline-id { font-size: 12px; color: #98a4b4; font-family: monospace; }
.timeline-score { font-size: 12px; color: #6b7a90; margin-left: auto; }
.timeline-meta { display: flex; gap: 16px; margin-top: 6px; font-size: 12px; color: #98a4b4; }
.timeline-error { color: #e85d6f; }
.expand-empty { text-align: center; padding: 30px; color: #98a4b4; font-size: 13px; }

@media (max-width: 760px) { .stat-cards { grid-template-columns: repeat(2,1fr); } }
</style>

