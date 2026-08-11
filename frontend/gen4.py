import os
def w(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Written: {os.path.basename(path)} ({len(content)} chars)')

base = r'D:\front\src\views\user'

# ========== 4. ReportsView.vue (报告下载中心) ==========
w(os.path.join(base, 'ReportsView.vue'), """<template>
  <div class="reports-page">
    <!-- 报告说明 -->
    <div class="report-intro-card">
      <div class="intro-header">
        <el-icon class="intro-icon"><InfoFilled /></el-icon>
        <span class="intro-title">审核意见书报告说明</span>
      </div>
      <div class="intro-body">
        <div class="intro-left">
          <p class="intro-scope">权限范围：仅可下载本人提交合同对应的AI+法务联合修改意见书，无后台配置、规则编辑权限。</p>
        </div>
        <div class="intro-right">
          <div class="ai-badge">
            <el-icon><Sparkles /></el-icon>
            <span>通义千问Qwen大模型+法务人工复核联合出具报告支撑</span>
          </div>
          <p>本页面可下载文件为**AI智能风险修改意见 + 法务终审专业修订意见汇总报告**，由通义千问Qwen法律大模型先完成合同全文解析、条款瑕疵识别、自动生成整改建议，再经法务审核员人工复核修正、补充专业法律意见后统一归档生成。文件支持HTML在线只读预览、PDF格式本地下载，报告作为合同修订整改唯一参考依据，AI建议不具备法律效力，最终执行以法务书面意见为准。</p>
        </div>
      </div>
    </div>

    <!-- 报告列表 -->
    <div class="report-list-card">
      <div class="list-header">
        <div class="list-title">
          <el-icon><Download /></el-icon>
          AI&法务联合修改意见报告列表
        </div>
        <div class="list-actions">
          <el-button>合同类型</el-button>
          <el-button>报告状态</el-button>
          <el-button type="primary">
            <el-icon><Refresh /></el-icon> 刷新列表
          </el-button>
        </div>
      </div>
      <el-table :data="reportList" stripe style="width:100%">
        <el-table-column label="对应合同名称" min-width="220">
          <template #default="{ row }">
            <span class="contract-name">{{ row.contractName }}</span>
          </template>
        </el-table-column>
        <el-table-column label="报告格式" width="140">
          <template #default="{ row }">
            <el-tag v-for="fmt in row.formats" :key="fmt" size="small" :type="fmt === 'HTML' ? '' : 'danger'" effect="plain" style="margin-right:4px">{{ fmt }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="generatedAt" label="报告生成时间" width="160" />
        <el-table-column label="报告生成状态" width="130">
          <template #default="{ row }">
            <span :class="row.status === 'success' ? 'text-green' : 'text-red'">
              <span class="status-dot" :class="row.status"></span>
              {{ row.status === 'success' ? '生成成功' : '生成失败' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="220">
          <template #default="{ row }">
            <template v-if="row.status === 'success'">
              <el-button link type="primary">HTML在线预览意见书</el-button>
              <el-button link type="primary">PDF下载完整修改意见报告</el-button>
            </template>
            <template v-else>
              <div class="retry-action">
                <el-button link type="primary">重新生成</el-button>
                <div class="retry-desc">将再次调用Qwen模型重新解析合同并拉取法务终审意见合成为文档</div>
              </div>
            </template>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-bar">
        <el-pagination v-model:current-page="currentPage" :page-size="10" :total="20" layout="prev, pager, next" />
        <div class="report-notice">
          <strong>报告使用须知：</strong>
          <ul>
            <li>HTML仅在线查看AI风险点、AI修改建议、法务逐条批注，不可编辑原文；</li>
            <li>PDF用于打印存档、合同修订对照整改；</li>
            <li>重新生成会二次调取大模型解析结果与法务终审记录，请勿频繁重试。</li>
          </ul>
        </div>
      </div>
    </div>

    <!-- 页脚 -->
    <div class="page-footer">
      <div class="footer-left">
        <p>技术驱动 · 法律合规大模型落地应用</p>
        <p>© 2024 A24 Enterprise Intelligence (China). All Rights Reserved. AI████████ Qwen-Max-Ultra ████████</p>
      </div>
      <div class="footer-right">
        <p>本系统仅输出AI与法务参考性修改意见报告，不构成正式法律文书。</p>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { InfoFilled, Sparkles, Download, Refresh } from '@element-plus/icons-vue'
const currentPage = ref(1)
const reportList = ref([
  { contractName: '2024年度云服务采购框架协议', formats: ['HTML', 'PDF'], generatedAt: '2023-11-20 14:30', status: 'success' },
  { contractName: '核心算法技术授权合同-V2', formats: ['HTML'], generatedAt: '2023-11-20 12:15', status: 'failed' },
])
</script>
<style scoped>
.report-intro-card { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px; }
.intro-header { display: flex; align-items: center; gap: 8px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #ebeef5; }
.intro-icon { color: #1a6fc4; font-size: 20px; }
.intro-title { font-size: 16px; font-weight: 600; color: #303133; }
.intro-body { display: grid; grid-template-columns: 1fr 2fr; gap: 24px; }
.intro-scope { font-size: 14px; color: #909399; line-height: 1.8; }
.intro-right p { font-size: 14px; color: #606266; line-height: 1.8; }
.ai-badge { display: flex; align-items: center; gap: 8px; background: #ecf5ff; border: 1px solid #d9ecff; border-radius: 6px; padding: 10px 16px; margin-bottom: 12px; font-size: 14px; color: #1a6fc4; font-weight: 500; }
.report-list-card { background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px; }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.list-title { font-size: 16px; font-weight: 600; color: #303133; display: flex; align-items: center; gap: 8px; }
.list-title .el-icon { color: #1a6fc4; }
.list-actions { display: flex; gap: 8px; }
.contract-name { font-size: 14px; color: #303133; }
.text-green { color: #67c23a; }
.text-red { color: #f56c6c; }
.status-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; }
.status-dot.success { background: #67c23a; }
.status-dot.failed { background: #f56c6c; }
.retry-action { }
.retry-desc { font-size: 12px; color: #909399; margin-top: 2px; }
.pagination-bar { display: flex; justify-content: space-between; align-items: flex-start; margin-top: 16px; }
.report-notice { background: #fafafa; border: 1px dashed #dcdfe6; border-radius: 6px; padding: 14px 18px; font-size: 13px; color: #606266; line-height: 1.8; max-width: 400px; }
.report-notice strong { display: block; margin-bottom: 4px; color: #303133; }
.report-notice ul { padding-left: 18px; }
.page-footer { display: flex; justify-content: space-between; padding: 20px 0; font-size: 13px; color: #c0c4cc; line-height: 1.8; }
.footer-left p:first-child { color: #1a6fc4; }
</style>""")

print('ReportsView done')
