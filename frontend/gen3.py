import os
def w(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Written: {os.path.basename(path)} ({len(content)} chars)')

base = r'D:\front\src\views\user'

# ========== 3. WarningsView.vue (风险预警中心) ==========
w(os.path.join(base, 'WarningsView.vue'), """<template>
  <div class="warnings-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">风险预警中心</h2>
        <p class="page-desc">监控并处理合同履行过程中的法律合规风险点。</p>
      </div>
      <div class="header-stats">
        <span class="stat-badge">待处理: 12</span>
        <span class="stat-badge overdue">已逾期: 2</span>
      </div>
    </div>

    <div class="warnings-layout">
      <!-- 左侧：预警列表 -->
      <div class="warnings-main">
        <div class="list-card">
          <div class="list-header">
            <span class="list-title">本人有效预警列表</span>
            <span class="list-status"><span class="status-dot"></span> 进行中</span>
          </div>
          <el-table :data="warningList" stripe style="width:100%">
            <el-table-column label="风险名称" min-width="220">
              <template #default="{ row }">
                <div class="risk-name-cell">
                  <div>{{ row.name }}</div>
                  <div class="risk-contract-no">合同编号: {{ row.contractNo }}</div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="风险等级" width="100">
              <template #default="{ row }">
                <el-tag :type="getLevelType(row.level)" size="small" effect="dark">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="整改截止时间" width="160">
              <template #default="{ row }">
                <span :class="{ 'text-red': row.overdue }">{{ row.dueDate }}{{ row.overdue ? ' (已逾期)' : '' }}</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160">
              <template #default>
                <el-button link type="primary" size="small">确认知悉</el-button>
                <el-button type="primary" size="small">上传修订</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pagination-bar">
            <el-pagination v-model:current-page="currentPage" :page-size="10" :total="60" layout="prev, pager, next" />
          </div>
        </div>
      </div>

      <!-- 右侧 -->
      <div class="warnings-side">
        <!-- 风控整改要求 -->
        <div class="side-card">
          <div class="side-card-title">
            <el-icon><Document /></el-icon> 风控整改要求
          </div>
          <div class="side-card-body">
            <p>根据集团风控部2023年Q4合规指引，所有逾期未处理的高风险项目将自动触发部门负责人提醒。</p>
            <div class="guide-box">
              <strong>标准化操作指南：</strong>
              <ul>
                <li>补充甲方签署授权书扫描件</li>
                <li>确保修订后合同文本加盖骑缝章</li>
                <li>上传附件需PDF格式，清晰度不低于300dpi</li>
              </ul>
            </div>
            <p class="guide-note">* 此区域为系统自动提取的合规标准，仅供参考，请严格执行。</p>
          </div>
        </div>

        <!-- 历史处置记录 -->
        <div class="side-card">
          <div class="side-card-title">
            <el-icon><Clock /></el-icon> 历史处置记录
          </div>
          <div class="side-card-body">
            <el-timeline>
              <el-timeline-item timestamp="2023-11-15 09:30" placement="top">
                <div class="timeline-title">系统检测：风险识别</div>
                <div class="timeline-desc">检测到合同编号 CON-2023-0891 履行保证金未按期缴纳。</div>
              </el-timeline-item>
              <el-timeline-item timestamp="2023-11-18 14:20" placement="top">
                <div class="timeline-title">系统提醒：二次催办</div>
                <div class="timeline-desc">系统向经办人及法务专员发送风险提醒邮件。</div>
              </el-timeline-item>
              <el-timeline-item timestamp="2023-11-20 00:00" placement="top" color="#f56c6c">
                <div class="timeline-title text-red">状态变更：已逾期</div>
                <div class="timeline-desc">整改期限届满，系统自动将风险状态标记为"逾期"。</div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { Document, Clock } from '@element-plus/icons-vue'
const currentPage = ref(1)
const warningList = ref([
  { name: '《供应协议》履行保证金缺失', contractNo: 'CON-2023-0891', level: '高风险', dueDate: '2023-11-20', overdue: true },
  { name: '发票关联信息不完整', contractNo: 'CON-2023-1022', level: '中风险', dueDate: '2023-12-05', overdue: false },
  { name: '归档附件印章模糊', contractNo: 'CON-2023-0765', level: '低风险', dueDate: '2023-12-15', overdue: false },
  { name: '未授权代理人签署风险', contractNo: 'CON-2023-1104', level: '高风险', dueDate: '2023-11-25', overdue: true },
  { name: '履约保证金交付逾期', contractNo: 'CON-2023-1522', level: '高风险', dueDate: '2023-11-25', overdue: true },
  { name: '知识产权归属条款冲突', contractNo: 'CON-2024-0045', level: '中风险', dueDate: '2024-01-15', overdue: false },
])
function getLevelType(level: string) { return { '高风险': 'danger', '中风险': 'warning', '低风险': 'info' }[level] || 'info' }
</script>
<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #909399; }
.header-stats { display: flex; gap: 12px; }
.stat-badge { font-size: 14px; color: #606266; background: #fff; padding: 6px 16px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.stat-badge.overdue { color: #f56c6c; }
.warnings-layout { display: grid; grid-template-columns: 1fr 340px; gap: 20px; }
.warnings-main { }
.list-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.list-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.list-title { font-size: 16px; font-weight: 600; color: #303133; }
.list-status { display: flex; align-items: center; gap: 6px; font-size: 14px; color: #1a6fc4; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #1a6fc4; }
.risk-name-cell { }
.risk-name-cell > div:first-child { font-size: 14px; color: #303133; font-weight: 500; }
.risk-contract-no { font-size: 12px; color: #909399; margin-top: 2px; }
.text-red { color: #f56c6c; }
.pagination-bar { display: flex; justify-content: center; margin-top: 16px; }
.warnings-side { display: flex; flex-direction: column; gap: 20px; }
.side-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.side-card-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.side-card-title .el-icon { color: #1a6fc4; }
.side-card-body { font-size: 14px; color: #606266; line-height: 1.8; }
.guide-box { background: #f5f7fa; border-radius: 6px; padding: 14px 16px; margin: 12px 0; }
.guide-box strong { display: block; margin-bottom: 6px; color: #303133; }
.guide-box ul { padding-left: 20px; }
.guide-box li { margin-bottom: 4px; }
.guide-note { font-size: 12px; color: #909399; }
.timeline-title { font-size: 14px; font-weight: 500; color: #303133; }
.timeline-desc { font-size: 13px; color: #909399; margin-top: 4px; }
</style>""")

print('WarningsView done')
