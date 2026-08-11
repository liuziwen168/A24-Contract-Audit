<template>
  <div class="reviews-page" v-loading="loading">
    <h2 class="page-title">我的审核任务</h2>

    <!-- 列表 -->
    <div class="card">
      <el-table :data="reviewList" stripe empty-text="暂无审核记录" @row-click="viewDetail" highlight-current-row>
        <el-table-column label="编号" width="70"><template #default="{ row }">#{{ row.id }}</template></el-table-column>
        <el-table-column label="合同" min-width="180">
          <template #default="{ row }">{{ row.contractName || '合同 #' + row.contractId }}</template>
        </el-table-column>
        <el-table-column label="阶段" width="110">
          <template #default="{ row }">
            <el-tag :type="stageTag(row.reviewStage)" size="small" effect="dark">{{ stageLabels[row.reviewStage] || row.reviewStage }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="风险等级" width="90">
          <template #default="{ row }">
            <el-tag v-if="row.overallRiskLevel" :type="levelTag(row.overallRiskLevel)" size="small">{{ levelLabels[row.overallRiskLevel] || row.overallRiskLevel }}</el-tag>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160"><template #default="{ row }">{{ fmt(row.createdAt) }}</template></el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="primary" @click.stop="viewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="fetchReviews" style="margin-top:16px;justify-content:flex-end" />
    </div>

    <!-- 审核中进度 -->
    <div v-if="showProgress" class="progress-card">
      <div class="progress-icon"><svg viewBox="0 0 48 48" fill="none"><circle cx="24" cy="24" r="21" stroke="currentColor" stroke-width="2.5" stroke-dasharray="8 4"/><path d="M18 18l12 12M30 18l-12 12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" opacity=".4"/></svg></div>
      <h3>AI 审核处理中</h3>
      <el-progress :percentage="reviewProgress" :stroke-width="14" :text-inside="false" color="#1a6fc4" style="max-width:340px;margin:0 auto" />
      <p class="progress-tip">{{ progressTip }}</p>
      <el-button type="primary" @click="retryDetail" :loading="detailLoading">刷新状态</el-button>
    </div>

    <!-- 审核失败 -->
    <div v-if="detail && detail.reviewStatus === 'failed'" class="fail-card">
      <div class="fail-icon"><svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/><path d="M12 8v4M12 16h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div>
      <div>
        <h3>审核失败</h3>
        <p>{{ detail.errorMessage || 'AI 处理异常' }}</p>
      </div>
      <el-button type="primary" @click="retryCurrent">重新审核</el-button>
    </div>

    <!-- 审核详情 -->
    <div v-if="detail && detail.reviewStatus !== 'failed'" class="detail-section" v-loading="detailLoading">
      <!-- 概要卡片 -->
      <div class="summary-card">
        <div class="summary-left">
          <div class="contract-badge">
            <svg viewBox="0 0 24 24" fill="none" width="20" height="20"><path d="M14 3H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V9z" stroke="currentColor" stroke-width="1.8"/><path d="M14 3v6h6" stroke="currentColor" stroke-width="1.8"/></svg>
          </div>
          <div>
            <h2>{{ detail.contractName || '合同 #' + detail.contractId }}</h2>
            <div class="summary-meta">
              <el-tag :type="stageTag(detail.reviewStage)" size="small" effect="dark">{{ stageLabels[detail.reviewStage] || detail.reviewStage }}</el-tag>
              <span v-if="detail.contractType" class="meta-item">{{ typeLabels[detail.contractType] || detail.contractType }}</span>
              <span class="meta-item">#{{ detail.id }}</span>
            </div>
          </div>
        </div>
        <div class="summary-right">
          <div class="score-ring" :style="{ '--pct': scorePercent + '%', '--clr': scoreColor }">
            <svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="42" class="track"/><circle cx="50" cy="50" r="42" class="fill" :style="{ strokeDashoffset: 264 - 264 * scorePercent / 100 }"/></svg>
            <div class="score-inner"><strong>{{ detail.overallScore ?? '--' }}</strong><small>风险分</small></div>
          </div>
          <el-tag v-if="detail.overallRiskLevel" :type="levelTag(detail.overallRiskLevel)" size="large" effect="dark">{{ levelLabels[detail.overallRiskLevel] || detail.overallRiskLevel }}</el-tag>
        </div>
      </div>

      <!-- 审核阶段流转 -->
      <div class="stage-stepper">
        <div v-for="s in stages" :key="s.key" :class="['step', { done: s.done, active: s.active }]">
          <div class="step-dot"><svg v-if="s.done" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/><path d="M5 8l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg><span v-else>{{ s.num }}</span></div>
          <div class="step-label">{{ s.label }}</div>
          <div v-if="s.time" class="step-time">{{ s.time }}</div>
        </div>
      </div>

      <!-- 合同要素 -->
      <div class="card">
        <div class="card-head">
          <h3>AI 提取合同要素</h3>
          <span class="badge">{{ (detail.elements || []).length }} 项</span>
        </div>
        <div v-if="(detail.elements || []).length" class="elements-grid">
          <div v-for="el in detail.elements" :key="el.id" class="element-card">
            <div class="el-icon">
              <svg viewBox="0 0 20 20" fill="none"><rect x="2" y="3" width="16" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M6 8h8M6 12h5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
            </div>
            <div class="el-body">
              <div class="el-name">{{ el.elementName }}</div>
              <div class="el-value">{{ el.valueText || '-' }}</div>
            </div>
            <div class="el-meta">
              <span v-if="el.confidence" class="el-conf" :class="{ low: el.confidence < 0.6 }">{{ (el.confidence * 100).toFixed(0) }}%</span>
              <span v-if="el.page" class="el-pos">P{{ el.page }}</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无要素数据" :image-size="60" />
      </div>

      <!-- 缺失条款 -->
      <div v-if="(detail.missingClauses || []).length" class="missing-bar">
        <svg viewBox="0 0 20 20" fill="none" width="18" height="18"><circle cx="10" cy="10" r="8.5" stroke="currentColor" stroke-width="1.5"/><path d="M10 6v5M10 14h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <span>缺失条款：</span>
        <el-tag v-for="c in detail.missingClauses" :key="c" size="small" type="warning">{{ clauseLabels[c] || c }}</el-tag>
      </div>

      <!-- 风险清单 -->
      <div class="card">
        <div class="card-head">
          <h3>风险识别结果</h3>
          <span class="badge danger">{{ (detail.risks || []).length }} 项</span>
        </div>
        <div v-if="(detail.risks || []).length" class="risks-list">
          <div v-for="risk in detail.risks" :key="risk.id" :class="['risk-card', risk.riskLevel]">
            <div class="risk-header">
              <div class="risk-level-tag" :class="risk.riskLevel">{{ levelLabels[risk.riskLevel] || risk.riskLevel }}</div>
              <strong>{{ risk.riskName }}</strong>
              <el-tag v-if="risk.riskId && feedbackTags[risk.riskId]" size="small" effect="plain" type="success">{{ feedbackTags[risk.riskId] }}</el-tag>
              <span v-if="risk.confidence" class="risk-conf">{{ (risk.confidence * 100).toFixed(0) }}%</span>
            </div>
            <div class="risk-body">
              <div class="risk-clause">
                <div class="risk-label">条款原文</div>
                <blockquote>{{ risk.clauseText }}</blockquote>
                <div class="risk-position" v-if="risk.page || risk.paragraphIndex != null">
                  <svg viewBox="0 0 16 16" fill="none" width="14" height="14"><circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.3"/><circle cx="8" cy="8" r="2" fill="currentColor"/></svg>
                  第{{ risk.page || '?' }}页 · 段落{{ risk.paragraphIndex != null ? risk.paragraphIndex + 1 : '?' }}
                </div>
              </div>
              <div class="risk-basis">
                <div class="risk-label">判定依据</div>
                <p>{{ risk.basis }}</p>
              </div>
              <div class="risk-suggestion">
                <div class="risk-label">修改建议</div>
                <p>{{ risk.suggestion }}</p>
              </div>
            </div>
          </div>
        </div>
        <el-empty v-else description="未发现风险项" :image-size="60" />
      </div>

      <!-- 法务意见 -->
      <div v-if="detail.legalOpinion || detail.legalReviewerId" class="opinion-card legal">
        <div class="opinion-head">
          <div class="opinion-avatar legal-avatar">
            <svg viewBox="0 0 20 20" fill="none"><circle cx="10" cy="7" r="3.5" stroke="currentColor" stroke-width="1.5"/><path d="M3 18c0-3.3 3.1-6 7-6s7 2.7 7 6" stroke="currentColor" stroke-width="1.5"/></svg>
          </div>
          <div>
            <strong>法务审核意见</strong>
            <div class="opinion-by">法务审核员 · {{ fmt(detail.legalReviewedAt) }}</div>
          </div>
          <div class="opinion-badge done">已复核</div>
        </div>
        <p v-if="detail.legalOpinion" class="opinion-text">{{ detail.legalOpinion }}</p>
        <div v-if="detail.feedback" class="feedback-chips">
          <el-tag v-for="(f, i) in detail.feedback.filter((x:any) => x.targetType === 'risk')" :key="i" :type="f.judgment === 'correct' ? 'success' : 'danger'" size="small" effect="plain">
            {{ f.judgment === 'correct' ? '✓' : '✗' }} 风险#{{ f.targetId }}
          </el-tag>
        </div>
      </div>

      <!-- 风控意见 -->
      <div v-if="detail.riskOpinion || detail.riskReviewerId" class="opinion-card risk-ops">
        <div class="opinion-head">
          <div class="opinion-avatar risk-avatar">
            <svg viewBox="0 0 20 20" fill="none"><path d="M10 2l7 12H3l7-12z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/><circle cx="10" cy="14" r="1" fill="currentColor"/></svg>
          </div>
          <div>
            <strong>风控审核意见</strong>
            <div class="opinion-by">风控审核员 · {{ fmt(detail.riskReviewedAt) }}</div>
          </div>
          <div class="opinion-badge done">已完成</div>
        </div>
        <p v-if="detail.riskOpinion" class="opinion-text">{{ detail.riskOpinion }}</p>
        <div class="final-verdict">
          <span>最终评级：</span><el-tag :type="levelTag(detail.overallRiskLevel)" size="small" effect="dark">{{ levelLabels[detail.overallRiskLevel] || detail.overallRiskLevel }}</el-tag>
          <span style="margin-left:12px">最终评分：</span><strong>{{ detail.overallScore }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { listReviews, getReview, getReviewProgress, createReview } from '@/api/reviews'

const loading = ref(false); const detailLoading = ref(false)
const reviewList = ref<any[]>([]); const page = ref(1); const pageSize = ref(20); const total = ref(0)
const detail = ref<any>(null); const showProgress = ref(false)
const reviewProgress = ref(0); const lastReviewId = ref(0); const progressStage = ref('')

const stageLabels: Record<string, string> = { pending: '等待AI', aiReview: 'AI初审', legalReview: '法务复核', riskReview: '风控复核', completed: '已完成', failed: '失败' }
const levelLabels: Record<string, string> = { low: '低风险', medium: '中风险', high: '高风险', critical: '严重风险' }
const typeLabels: Record<string, string> = { purchase: '采购合同', sales: '销售合同', nda: '保密协议', outsourcing: '服务外包', labor: '劳动合同', other: '其他' }
const clauseLabels: Record<string, string> = { disputeResolution: '争议解决', confidentiality: '保密条款', performanceTerm: '履行期限', forceMajeure: '不可抗力', acceptance: '验收标准', intellectualProperty: '知识产权' }

const feedbackTags = computed(() => {
  const m: Record<number, string> = {}
  if (detail.value?.feedback) {
    (detail.value.feedback as any[]).forEach((f: any) => {
      if (f.targetType === 'risk') m[f.targetId] = f.judgment === 'correct' ? '法务确认有效' : '法务标记错误'
    })
  }
  return m
})

const scorePercent = computed(() => {
  const s = detail.value?.overallScore
  if (s == null) return 0
  return Math.min(100, Math.max(0, Number(s)))
})
const scoreColor = computed(() => {
  const s = scorePercent.value
  if (s >= 70) return '#e85d6f'
  if (s >= 40) return '#f0a145'
  return '#42c98a'
})

const stageOrder = ['aiReview', 'legalReview', 'riskReview', 'completed']
const stages = computed(() => {
  const current = detail.value?.reviewStage || ''
  const idx = stageOrder.indexOf(current)
  return [
    { key: 'aiReview', label: 'AI 初审', num: 1, done: idx >= 0, active: current === 'aiReview', time: null },
    { key: 'legalReview', label: '法务复核', num: 2, done: idx >= 1, active: current === 'legalReview', time: detail.value?.legalReviewedAt },
    { key: 'riskReview', label: '风控复核', num: 3, done: idx >= 2, active: current === 'riskReview', time: detail.value?.riskReviewedAt },
    { key: 'completed', label: '审核完成', num: 4, done: idx >= 3, active: current === 'completed', time: null },
  ]
})

const progressTip = computed(() => {
  if (detail.value?.reviewStage === 'aiReview') return 'AI 正在解析合同文档并识别风险条款…'
  if (detail.value?.reviewStage === 'legalReview') return '法务审核员正在复核合同要素与法律风险…'
  if (detail.value?.reviewStage === 'riskReview') return '风控审核员正在评估风险等级与最终结论…'
  return '处理中…'
})

function stageTag(s: string) { const m: Record<string, string> = { pending: 'info', aiReview: '', legalReview: 'warning', riskReview: 'danger', completed: 'success', failed: 'danger' }; return m[s] || 'info' }
function levelTag(l: string) { const m: Record<string, string> = { low: 'success', medium: 'warning', high: 'danger', critical: 'danger' }; return m[l] || 'info' }
function fmt(s: string) { if (!s) return '-'; try { return new Date(s).toLocaleString('zh-CN') } catch { return s } }

async function fetchReviews() {
  loading.value = true
  try {
    const res = await listReviews({ page: page.value, pageSize: pageSize.value })
    reviewList.value = res.items; total.value = res.total
  } finally { loading.value = false }
}

async function viewDetail(row: any) {
  detailLoading.value = true; detail.value = null; showProgress.value = false
  lastReviewId.value = row.id
  if (row.reviewStatus === 'failed') { detail.value = row; detailLoading.value = false; return }
  try {
    const r = await getReview(row.id)
    detail.value = r; showProgress.value = false
  } catch (e: any) {
    const code = e?.response?.data?.code || ''
    if (code === 'REVIEW_RESULT_NOT_READY' || e?.response?.status === 409) {
      showProgress.value = true
      try { const p = await getReviewProgress(row.id); reviewProgress.value = p.progress || 0; progressStage.value = p.reviewStage || '' } catch { reviewProgress.value = 0 }
    }
  } finally { detailLoading.value = false }
}

async function retryCurrent() {
  if (!detail.value) return
  const r = detail.value
  try {
    await createReview({ contractId: r.contractId, contractFileId: r.contractFileId, reviewMode: 'full' }, `retry-${r.contractId}-${Date.now()}`)
    ElMessage.success('已重新发起'); detail.value = null; fetchReviews()
  } catch { }
}

function retryDetail() { if (lastReviewId.value) { const row = reviewList.value.find((r: any) => r.id === lastReviewId.value); if (row) viewDetail(row) } }

onMounted(() => fetchReviews())
</script>

<style scoped>
.reviews-page { max-width: 1100px; margin: 0 auto; }
.page-title { font-size: 22px; font-weight: 700; color: #1f2a3a; margin: 0 0 18px; }
.card { background: #fff; border-radius: 14px; padding: 22px 26px; box-shadow: 0 2px 12px rgba(0,0,0,.04); margin-bottom: 18px; }
.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.card-head h3 { margin: 0; font-size: 16px; color: #1f2a3a; }
.badge { padding: 4px 10px; border-radius: 8px; background: #e8f3ff; color: #1a6fc4; font-size: 12px; font-weight: 600; }
.badge.danger { background: #fff0f0; color: #d9545e; }
.muted { color: #98a4b4; font-size: 13px; }

/* ---- Progress ---- */
.progress-card { text-align: center; padding: 48px 20px; background: #fff; border-radius: 14px; box-shadow: 0 2px 12px rgba(0,0,0,.04); }
.progress-icon { width: 60px; height: 60px; margin: 0 auto 16px; color: #1a6fc4; animation: spin 3s linear infinite; }
.progress-icon svg { width: 100%; height: 100%; }
@keyframes spin { to { transform: rotate(360deg); } }
.progress-card h3 { margin: 0 0 20px; color: #1f2a3a; }
.progress-tip { color: #6b7a90; font-size: 14px; margin: 16px 0 20px; }

/* ---- Fail ---- */
.fail-card { display: flex; align-items: center; gap: 20px; padding: 24px 28px; background: #fff; border-radius: 14px; border: 1px solid #ffe0e4; box-shadow: 0 2px 12px rgba(0,0,0,.04); }
.fail-icon { width: 44px; height: 44px; color: #e85d6f; flex-shrink: 0; }
.fail-icon svg { width: 100%; height: 100%; }
.fail-card h3 { margin: 0 0 4px; color: #d9545e; font-size: 16px; }
.fail-card p { margin: 0; color: #8899aa; font-size: 13px; }
.fail-card .el-button { margin-left: auto; }

/* ---- Summary ---- */
.summary-card { display: flex; align-items: center; justify-content: space-between; padding: 24px 28px; background: linear-gradient(135deg,#1a3d6e,#1a6fc4); border-radius: 16px; color: #fff; margin-bottom: 18px; box-shadow: 0 8px 24px rgba(26,111,196,.2); }
.summary-left { display: flex; align-items: center; gap: 16px; }
.contract-badge { width: 44px; height: 44px; border-radius: 12px; background: rgba(255,255,255,.18); display: grid; place-items: center; color: #fff; }
.summary-left h2 { margin: 0 0 6px; font-size: 18px; }
.summary-meta { display: flex; align-items: center; gap: 10px; }
.meta-item { font-size: 12px; opacity: .8; }
.summary-right { display: flex; align-items: center; gap: 16px; flex-shrink: 0; }
.score-ring { position: relative; width: 74px; height: 74px; }
.score-ring svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.score-ring .track { fill: none; stroke: rgba(255,255,255,.18); stroke-width: 5; }
.score-ring .fill { fill: none; stroke: var(--clr, #42c98a); stroke-width: 5; stroke-linecap: round; stroke-dasharray: 264; transition: stroke-dashoffset .6s; }
.score-inner { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.score-inner strong { font-size: 22px; line-height: 1; }
.score-inner small { font-size: 10px; opacity: .7; margin-top: 2px; }

/* ---- Stepper ---- */
.stage-stepper { display: flex; align-items: center; justify-content: space-between; padding: 20px 28px; background: #fff; border-radius: 14px; margin-bottom: 18px; box-shadow: 0 2px 12px rgba(0,0,0,.04); }
.step { display: flex; flex-direction: column; align-items: center; gap: 6px; position: relative; flex: 1; }
.step::after { content: ''; position: absolute; top: 14px; left: calc(50% + 22px); width: calc(100% - 44px); height: 2px; background: #e8ecf2; }
.step:last-child::after { display: none; }
.step.done::after { background: #1a6fc4; }
.step-dot { width: 28px; height: 28px; border-radius: 50%; background: #eef2f6; color: #8899aa; display: grid; place-items: center; font-size: 12px; font-weight: 700; }
.step.done .step-dot { background: #e8f3ff; color: #1a6fc4; }
.step.active .step-dot { background: #1a6fc4; color: #fff; }
.step-dot svg { width: 16px; height: 16px; }
.step-label { font-size: 12px; color: #8899aa; font-weight: 500; }
.step.done .step-label { color: #4a6388; }
.step.active .step-label { color: #1a6fc4; font-weight: 700; }
.step-time { font-size: 10px; color: #b4bfcc; }

/* ---- Elements ---- */
.elements-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.element-card { display: flex; gap: 12px; padding: 16px; border-radius: 11px; background: #f8fafc; border: 1px solid #edf0f5; transition: box-shadow .2s; }
.element-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,.04); }
.el-icon { width: 36px; height: 36px; border-radius: 8px; background: #e8f3ff; color: #1a6fc4; display: grid; place-items: center; flex-shrink: 0; }
.el-icon svg { width: 18px; height: 18px; }
.el-body { flex: 1; min-width: 0; }
.el-name { font-size: 12px; color: #8899aa; margin-bottom: 4px; }
.el-value { font-size: 14px; color: #1f2a3a; font-weight: 600; word-break: break-all; }
.el-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
.el-conf { font-size: 11px; padding: 2px 7px; border-radius: 6px; background: #e8faf0; color: #2db271; font-weight: 600; }
.el-conf.low { background: #fff2e4; color: #e0901d; }
.el-pos { font-size: 11px; color: #b4bfcc; }

/* ---- Missing ---- */
.missing-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 14px 20px; border-radius: 10px; background: #fff9e6; border: 1px solid #f5e6b8; margin-bottom: 18px; font-size: 13px; color: #8a6d20; }
.missing-bar svg { color: #e0a020; flex-shrink: 0; }

/* ---- Risks ---- */
.risks-list { display: flex; flex-direction: column; gap: 16px; }
.risk-card { border-radius: 12px; border: 1px solid #edf0f5; overflow: hidden; background: #fff; transition: box-shadow .2s; }
.risk-card:hover { box-shadow: 0 4px 14px rgba(0,0,0,.05); }
.risk-card.high, .risk-card.critical { border-left: 4px solid #e85d6f; }
.risk-card.medium { border-left: 4px solid #f0a145; }
.risk-card.low { border-left: 4px solid #42c98a; }
.risk-header { display: flex; align-items: center; gap: 10px; padding: 14px 18px; background: #fafbfc; border-bottom: 1px solid #f0f2f5; }
.risk-level-tag { padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.risk-level-tag.high, .risk-level-tag.critical { background: #fff0f0; color: #d9545e; }
.risk-level-tag.medium { background: #fff6ed; color: #d97a20; }
.risk-level-tag.low { background: #e8faf0; color: #2db271; }
.risk-header strong { font-size: 14px; color: #1f2a3a; }
.risk-conf { margin-left: auto; font-size: 12px; color: #8899aa; }
.risk-body { padding: 16px 18px; display: flex; flex-direction: column; gap: 14px; }
.risk-label { font-size: 11px; text-transform: uppercase; letter-spacing: .5px; color: #98a4b4; margin-bottom: 6px; font-weight: 600; }
.risk-clause blockquote { margin: 0; padding: 10px 14px; background: #f8f9fb; border-radius: 8px; font-size: 13px; color: #44536b; line-height: 1.7; border-left: 3px solid #dce3ed; }
.risk-position { display: flex; align-items: center; gap: 6px; margin-top: 8px; font-size: 12px; color: #98a4b4; }
.risk-basis p, .risk-suggestion p { margin: 0; font-size: 13px; color: #44536b; line-height: 1.7; }
.risk-suggestion { background: #f0f6ff; padding: 12px 14px; border-radius: 8px; }

/* ---- Opinions ---- */
.opinion-card { padding: 20px 24px; border-radius: 14px; margin-bottom: 18px; box-shadow: 0 2px 12px rgba(0,0,0,.04); }
.opinion-card.legal { background: #f5f8ff; border: 1px solid #dce8f8; }
.opinion-card.risk-ops { background: #fff8f0; border: 1px solid #f5e4cf; }
.opinion-head { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.opinion-avatar { width: 38px; height: 38px; border-radius: 10px; display: grid; place-items: center; }
.legal-avatar { background: #e0ecff; color: #4e86d8; }
.risk-avatar { background: #ffe8d0; color: #e09038; }
.opinion-avatar svg { width: 20px; height: 20px; }
.opinion-head strong { font-size: 15px; color: #1f2a3a; }
.opinion-by { font-size: 12px; color: #8899aa; margin-top: 2px; }
.opinion-badge { margin-left: auto; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 600; }
.opinion-badge.done { background: #e8faf0; color: #2db271; }
.opinion-text { font-size: 14px; color: #44536b; line-height: 1.8; margin: 0 0 12px; }
.feedback-chips { display: flex; gap: 6px; flex-wrap: wrap; }
.final-verdict { display: flex; align-items: center; margin-top: 10px; font-size: 13px; color: #5a6b80; }
.final-verdict strong { color: #1f2a3a; font-size: 16px; }

/* ---- Table ---- */
:deep(.el-table) { cursor: pointer; }
:deep(.el-table__row:hover) { background: #f5f8fc; }
</style>
