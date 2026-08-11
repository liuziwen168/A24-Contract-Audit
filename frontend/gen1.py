import base64, os

def w(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Written: {os.path.basename(path)} ({len(content)} chars)')

base = r'D:\front\src\views\user'
os.makedirs(base, exist_ok=True)

# ========== 1. ContractsView.vue ==========
w(os.path.join(base, 'ContractsView.vue'), """<template>
  <div class="contracts-page">
    <div class="stat-cards">
      <div class="stat-card" v-for="card in statCards" :key="card.label">
        <div class="stat-label">{{ card.label }}</div>
        <div class="stat-value" :class="card.colorClass">{{ card.value }}</div>
      </div>
    </div>
    <div class="action-bar">
      <el-button type="primary" class="btn-upload" @click="showUpload = true">
        <el-icon><Upload /></el-icon> 上传合同
      </el-button>
      <el-button class="btn-report" @click="$router.push('/user/reports')">
        <el-icon><View /></el-icon> 查看审核报告
      </el-button>
    </div>
    <div class="filter-bar">
      <div class="filter-item">
        <span class="filter-label">合同类型:</span>
        <el-select v-model="filters.contractType" placeholder="全部类型" style="width:140px">
          <el-option label="全部类型" value="" />
          <el-option label="采购合同" value="purchase" />
          <el-option label="销售合同" value="sales" />
          <el-option label="保密协议" value="nda" />
          <el-option label="服务外包" value="outsourcing" />
          <el-option label="劳动合同" value="labor" />
        </el-select>
      </div>
      <div class="filter-item">
        <span class="filter-label">审核状态:</span>
        <el-select v-model="filters.reviewStatus" placeholder="全部状态" style="width:140px">
          <el-option label="全部状态" value="" />
          <el-option label="审核中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="待整改" value="failed" />
        </el-select>
      </div>
      <div class="filter-item">
        <span class="filter-label">上传时间区间:</span>
        <el-date-picker v-model="filters.dateRange" type="daterange" range-separator="至" start-placeholder="mm/dd/yyyy" end-placeholder="mm/dd/yyyy" style="width:280px" />
      </div>
      <el-button link type="primary" class="reset-btn" @click="resetFilters">
        <el-icon><Refresh /></el-icon> 重置筛选
      </el-button>
    </div>
    <div class="task-table-card">
      <div class="table-header">
        <span class="table-title">最近任务列表</span>
        <span class="table-total">共 {{ total }} 条记录</span>
      </div>
      <el-table :data="taskList" stripe style="width:100%">
        <el-table-column prop="taskType" label="任务类型" width="160" />
        <el-table-column prop="contractName" label="对应合同名称" min-width="280" />
        <el-table-column prop="updatedAt" label="更新时间" width="180" />
        <el-table-column label="状态标签" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small" effect="plain">{{ row.statusLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default>
            <el-button link type="primary">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <div class="page-size">
          <span>每页显示</span>
          <el-select v-model="pageSize" style="width:80px;margin:0 8px">
            <el-option :value="20" label="20 条" />
          </el-select>
        </div>
        <el-pagination v-model:current-page="currentPage" :page-size="pageSize" :total="total" layout="prev, pager, next, jumper" />
      </div>
    </div>
    <el-dialog v-model="showUpload" title="上传合同" width="500px">
      <el-upload drag action="/api/v1/contracts" :headers="uploadHeaders">
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
        <template #tip><div class="el-upload__tip">支持 .docx / .pdf / 图片格式，最大 20MB</div></template>
      </el-upload>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Upload, View, Refresh, UploadFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()
const uploadHeaders = { Authorization: 'Bearer ' + userStore.accessToken }
const statCards = ref([
  { label: '我上传合同总数', value: '1,248', colorClass: '' },
  { label: '审核中合同数量', value: '42', colorClass: 'text-blue' },
  { label: '待整改预警数量', value: '18', colorClass: 'text-red' },
  { label: '已完成合同数量', value: '1,188', colorClass: '' },
])
const filters = reactive({ contractType: '', reviewStatus: '', dateRange: null as any })
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(5291)
const showUpload = ref(false)
const taskList = ref([
  { taskType: '智能初审', contractName: '关于2024年度云服务采购框架协议.pdf', updatedAt: '2023-11-24 14:30:21', status: 'processing', statusLabel: '审核中' },
  { taskType: '风险复核', contractName: '华东区办公用品长期供应合同-V2.docx', updatedAt: '2023-11-23 18:15:00', status: 'failed', statusLabel: '待整改' },
  { taskType: '合规性审查', contractName: '核心研发团队知识产权保密协议_2023.pdf', updatedAt: '2023-11-23 09:44:12', status: 'completed', statusLabel: '已出结果' },
  { taskType: '财务条款审查', contractName: '海外分部市场营销服务协议_ENG.pdf', updatedAt: '2023-11-22 16:20:55', status: 'processing', statusLabel: '审核中' },
  { taskType: '印章法律效力审查', contractName: 'XX地产集团战略合作谅解备忘录.docx', updatedAt: '2023-11-22 11:05:30', status: 'completed', statusLabel: '已出结果' },
])
function getStatusType(s: string) { return { processing: '', failed: 'warning', completed: 'info' }[s] || 'info' }
function resetFilters() { filters.contractType = ''; filters.reviewStatus = ''; filters.dateRange = null }
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
</style>""")

print('All done!')
