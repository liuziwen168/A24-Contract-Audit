<template>
  <div class="page" v-loading="loading">
    <h2>合规预警处置</h2>
    <p class="desc">待法务确认的风险预警，确认后进入风控处置或撤回</p>

    <el-table :data="warningList" stripe empty-text="暂无待处理预警">
      <el-table-column label="预警ID" width="80"><template #default="{ row }">#{{ row.id }}</template></el-table-column>
      <el-table-column label="风险名称" min-width="180">
        <template #default="{ row }">{{ row.sourceSnapshot?.riskName || '-' }}</template>
      </el-table-column>
      <el-table-column label="风险等级" width="100">
        <template #default="{ row }">
          <el-tag :type="levelTag(row.warningLevel)" size="small">{{ row.warningLevel }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag size="small" type="warning" effect="plain">待法务确认</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="170">
        <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="primary" @click="confirmOne(row)">确认</el-button>
          <el-button size="small" type="danger" @click="withdrawOne(row)">撤回</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 撤回对话框 -->
    <el-dialog v-model="withdrawDialog" title="撤回预警" width="400px">
      <el-input v-model="withdrawComment" type="textarea" :rows="3" placeholder="请输入撤回原因..." />
      <template #footer>
        <el-button @click="withdrawDialog = false">取消</el-button>
        <el-button type="primary" :loading="withdrawing" @click="doWithdraw">确认撤回</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listWarnings, legalConfirm, legalWithdraw } from '@/api/warnings'

const loading = ref(false)
const warningList = ref<any[]>([])

const withdrawDialog = ref(false)
const withdrawComment = ref('')
const withdrawing = ref(false)
const withdrawTarget = ref<any>(null)

function levelTag(l: string) {
  const m: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return m[l] || 'info'
}
function fmt(s: string) {
  if (!s) return '-'
  try { return new Date(s).toLocaleString('zh-CN') } catch { return s }
}

async function fetchData() {
  loading.value = true
  try {
    const res = await listWarnings({ warningStatus: 'pendingLegal', pageSize: 100 })
    warningList.value = res.items
  } finally {
    loading.value = false
  }
}

async function confirmOne(row: any) {
  try {
    await ElMessageBox.confirm('确认该预警？确认后进入风控审核流程', '确认预警')
    await legalConfirm(row.id)
    ElMessage.success('已确认')
    fetchData()
  } catch { /* cancelled */ }
}

function withdrawOne(row: any) {
  withdrawTarget.value = row
  withdrawComment.value = ''
  withdrawDialog.value = true
}

async function doWithdraw() {
  if (!withdrawTarget.value || !withdrawComment.value.trim()) {
    ElMessage.warning('请输入撤回原因')
    return
  }
  withdrawing.value = true
  try {
    await legalWithdraw(withdrawTarget.value.id, withdrawComment.value.trim())
    ElMessage.success('已撤回')
    withdrawDialog.value = false
    fetchData()
  } finally {
    withdrawing.value = false
  }
}

onMounted(() => fetchData())
</script>

<style scoped>
.page { }
.desc { color: #909399; font-size: 14px; margin-bottom: 16px; }
</style>
