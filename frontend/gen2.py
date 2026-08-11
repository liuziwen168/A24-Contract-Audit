import os
def w(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Written: {os.path.basename(path)} ({len(content)} chars)')

base = r'D:\front\src\views\user'

# ========== 2. ReviewsView.vue (我的审核任务) ==========
w(os.path.join(base, 'ReviewsView.vue'), """<template>
  <div class="reviews-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">我的审核任务</h2>
        <p class="page-desc">实时追踪合同审核进度，查看AI辅助风控分析结果。</p>
      </div>
      <el-button type="primary" class="btn-new-task">
        <el-icon><Plus /></el-icon> 新建审核任务
      </el-button>
    </div>

    <div class="filter-bar">
      <div class="filter-item" style="flex:1;max-width:400px">
        <span class="filter-label">审核编号 / 合同名称检索</span>
        <el-input v-model="filters.keyword" placeholder="输入关键字搜索..." style="margin-top:8px">
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
      </div>
      <div class="filter-item">
        <span class="filter-label">审核阶段</span>
        <el-select v-model="filters.stage" placeholder="全部状态" style="width:140px;margin-top:8px">
          <el-option label="全部状态" value="" />
          <el-option label="AI初审" value="aiReview" />
          <el-option label="法务复核" value="legalReview" />
          <el-option label="审核完成" value="completed" />
          <el-option label="审核失败" value="failed" />
        </el-select>
      </div>
      <div class="filter-actions">
        <el-button type="primary" @click="doSearch">查询</el-button>
        <el-button @click="doReset">重置</el-button>
      </div>
    </div>

    <div class="task-table-card">
      <el-table :data="reviewList" stripe style="width:100%">
        <el-table-column prop="reviewNo" label="审核编号" width="140" />
        <el-table-column prop="contractName" label="对应合同名称" min-width="260" />
        <el-table-column label="当前审核阶段" width="130">
          <template #default="{ row }">
            <el-tag :type="getStageType(row.stage)" size="small" effect="plain">{{ row.stageLabel }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">查看审核结果</el-button>
            <el-button link type="danger" v-if="row.stage === 'failed'">重新发起</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 审核详情 -->
    <div class="detail-section" v-if="selectedReview">
      <div class="detail-header">
        <h3 class="detail-title">
          <el-icon><DataAnalysis /></el-icon>
          审核详情分析：{{ selectedReview.reviewNo }}
        </h3>
        <span class="detail-mode">当前显示：只读模式</span>
      </div>
      <div class="detail-grid">
        <!-- 左侧：AI识别合同要素清单 -->
        <div class="detail-card">
          <div class="card-title">AI 识别合同要素清单</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="合同主体 (甲方)">北京博远科技有限公司</el-descriptions-item>
            <el-descriptions-item label="合同主体 (乙方)">A24 技术服务有限公司</el-descriptions-item>
            <el-descriptions-item label="合同标的">软件外包开发服务</el-descriptions-item>
            <el-descriptions-item label="合同总额">¥ 2,450,000.00</el-descriptions-item>
            <el-descriptions-item label="生效日期">2024-06-01</el-descriptions-item>
          </el-descriptions>
        </div>
        <!-- 右侧：风险清单与修改建议 -->
        <div class="detail-card">
          <div class="card-title">风险清单与修改建议</div>
          <div class="risk-item">
            <div class="risk-header">
              <el-tag type="danger" size="small">高风险</el-tag>
              <span class="risk-name">违约金比例超出法定上限</span>
            </div>
            <div class="ai-suggestion risk-high">
              <strong>AI 修改建议：</strong>原合同第8.2条规定逾期违约金为每日合同总额的1%，建议调整为每日0.05%，最高不超过总额的20%。
            </div>
            <div class="legal-opinion">
              <el-icon><ChatLineSquare /></el-icon>
              <span>法务意见：同意AI建议，该条款极易引起司法争议，务必在回传前修改。</span>
            </div>
          </div>
          <div class="risk-item">
            <div class="risk-header">
              <el-tag type="warning" size="small">中风险</el-tag>
              <span class="risk-name">知识产权归属条款表述模糊</span>
            </div>
            <div class="ai-suggestion risk-medium">
              <strong>AI 修改建议：</strong>应明确开发过程中产生的所有交付物所有权均归属甲方，乙方仅保留署名权。
            </div>
          </div>
          <div class="risk-item">
            <div class="risk-header">
              <el-tag type="info" size="small">低风险</el-tag>
              <span class="risk-name">争议解决管辖地约定缺失</span>
            </div>
            <div class="ai-suggestion risk-low">
              <strong>AI 修改建议：</strong>建议增加"由甲方所在地人民法院管辖"条款。
            </div>
          </div>
        </div>
      </div>
      <!-- 风控最终结论 -->
      <div class="detail-card conclusion-card">
        <div class="card-title">风控最终结论</div>
        <div class="conclusion-content">
          <div class="conclusion-badge">
            <el-icon class="conclusion-icon-fail"><CircleCloseFilled /></el-icon>
            <div>
              <div class="conclusion-result">审核不通过</div>
              <div class="conclusion-meta">审核人：林总 (风控部) | 2024-05-18 10:20</div>
            </div>
          </div>
          <p class="conclusion-text">"由于违约金条款与我司标准模板严重偏离，且知识产权条款可能导致核心代码流失风险，本次申请予以驳回。请经办人联系乙方按照修改建议重新协商，上传修正版后再行提交。"</p>
        </div>
      </div>
    </div>

    <div class="page-footer">
      <p>ⓘ AI结果仅供参考，最终以专业人员判定为准</p>
      <p>© 2024 A24 Enterprise Intelligence Contract Audit System. All rights reserved.</p>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { Plus, Search, DataAnalysis, ChatLineSquare, CircleCloseFilled } from '@element-plus/icons-vue'
const filters = reactive({ keyword: '', stage: '' })
const reviewList = ref([
  { reviewNo: 'SH2024001', contractName: '2024年度云服务采购框架协议', stage: 'aiReview', stageLabel: 'AI初审', createdAt: '2024-05-20 14:30' },
  { reviewNo: 'SH2024005', contractName: '核心算法技术授权合同-V2', stage: 'legalReview', stageLabel: '法务复核', createdAt: '2024-05-19 09:15' },
  { reviewNo: 'SH2024012', contractName: '办公大楼租赁补充协议', stage: 'completed', stageLabel: '审核完成', createdAt: '2024-05-18 16:45' },
  { reviewNo: 'SH2024018', contractName: '软件外包服务交付合同 (A24-IT-03)', stage: 'failed', stageLabel: '审核失败', createdAt: '2024-05-18 10:20' },
])
const selectedReview = ref<any>(null)
function getStageType(s: string) { return { aiReview: '', legalReview: 'warning', completed: 'success', failed: 'danger' }[s] || 'info' }
function doSearch() {}
function doReset() { filters.keyword = ''; filters.stage = '' }
function showDetail(row: any) { selectedReview.value = row }
</script>
<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.page-title { font-size: 22px; font-weight: 600; color: #303133; margin-bottom: 4px; }
.page-desc { font-size: 14px; color: #909399; }
.btn-new-task { background: #1a6fc4; border-color: #1a6fc4; height: 40px; padding: 0 32px; font-size: 15px; }
.filter-bar { display: flex; align-items: flex-end; gap: 20px; background: #fff; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); flex-wrap: wrap; }
.filter-item { display: flex; flex-direction: column; }
.filter-label { font-size: 13px; color: #606266; font-weight: 500; }
.filter-actions { display: flex; gap: 8px; margin-left: auto; }
.task-table-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px; }
.detail-section { margin-top: 20px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.detail-title { font-size: 18px; font-weight: 600; color: #303133; display: flex; align-items: center; gap: 8px; }
.detail-mode { font-size: 13px; color: #909399; }
.detail-grid { display: grid; grid-template-columns: 1fr 1.5fr; gap: 20px; margin-bottom: 20px; }
.detail-card { background: #fff; border-radius: 8px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card-title { font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #ebeef5; }
.risk-item { margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #f2f6fc; }
.risk-item:last-child { border-bottom: none; margin-bottom: 0; }
.risk-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.risk-name { font-size: 14px; font-weight: 500; color: #303133; }
.ai-suggestion { padding: 12px 16px; border-radius: 6px; font-size: 13px; line-height: 1.6; margin-bottom: 8px; }
.ai-suggestion strong { color: #e6a23c; }
.risk-high { background: #fef0f0; border-left: 3px solid #f56c6c; }
.risk-medium { background: #fdf6ec; border-left: 3px solid #e6a23c; }
.risk-low { background: #f4f4f5; border-left: 3px solid #909399; }
.legal-opinion { display: flex; align-items: flex-start; gap: 6px; font-size: 13px; color: #606266; }
.legal-opinion .el-icon { color: #909399; margin-top: 2px; }
.conclusion-card { }
.conclusion-content { }
.conclusion-badge { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.conclusion-icon-fail { font-size: 36px; color: #f56c6c; }
.conclusion-result { font-size: 18px; font-weight: 600; color: #f56c6c; }
.conclusion-meta { font-size: 13px; color: #909399; margin-top: 2px; }
.conclusion-text { font-size: 14px; color: #606266; line-height: 1.8; background: #fafafa; padding: 16px; border-radius: 6px; }
.page-footer { text-align: center; padding: 30px 0 10px; font-size: 13px; color: #c0c4cc; line-height: 2; }
</style>""")

print('ReviewsView done')
