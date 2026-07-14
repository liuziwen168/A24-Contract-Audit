 <template>
   <div class="review-detail" v-loading="loading" element-loading-text="加载中...">
     <!-- Status Bar -->
     <div class="status-bar">
       <div class="status-track">
         <div class="stage-item" :class="{ active: stageIndex >= 0, done: stageIndex > 0 }">
           <div class="stage-dot" :style="{ background: stageIndex >= 0 ? '#4361ee' : '#e5e7eb' }">
             <el-icon v-if="stageIndex > 0"><Check /></el-icon>
             <span v-else>1</span>
           </div>
           <span class="stage-name">AI 初审</span>
         </div>
         <div class="stage-line" :class="{ active: stageIndex >= 1 }"></div>
         <div class="stage-item" :class="{ active: stageIndex >= 1, done: stageIndex > 1 }">
           <div class="stage-dot" :style="{ background: stageIndex >= 1 ? '#f59e0b' : '#e5e7eb' }">
             <el-icon v-if="stageIndex > 1"><Check /></el-icon>
             <span v-else>2</span>
           </div>
           <span class="stage-name">法务复核</span>
         </div>
         <div class="stage-line" :class="{ active: stageIndex >= 2 }"></div>
         <div class="stage-item" :class="{ active: stageIndex >= 2, done: stageIndex > 2 }">
           <div class="stage-dot" :style="{ background: stageIndex >= 2 ? '#10b981' : '#e5e7eb' }">
             <el-icon v-if="stageIndex > 2"><Check /></el-icon>
             <span v-else>3</span>
           </div>
           <span class="stage-name">风控复核</span>
         </div>
       </div>
 
       <div class="status-meta">
         <el-tag v-if="reviewResult" :type="statusTagType" effect="dark" size="small">
           {{ REVIEW_STATUS_LABELS[reviewResult.reviewStatus] }}
         </el-tag>
         <el-tag v-if="reviewResult" type="info" effect="plain" size="small">
           {{ REVIEW_STAGE_LABELS[reviewResult.reviewStage] }}
         </el-tag>
         <div v-if="reviewResult?.effectiveResult?.overallRiskLevel" class="overall-risk-tag">
           <span class="risk-dot" :style="{ background: getRiskColor(reviewResult.effectiveResult.overallRiskLevel) }"></span>
           {{ getRiskLevelLabel(reviewResult.effectiveResult.overallRiskLevel) }}
           <span v-if="reviewResult.effectiveResult.overallScore" class="score-badge">{{ reviewResult.effectiveResult.overallScore }}分</span>
         </div>
         <el-button text size="small" class="back-link" @click="router.back()">
           <el-icon><ArrowLeft /></el-icon> 返回
         </el-button>
       </div>
 
       <div v-if="isPolling" class="polling-banner">
         <el-icon class="is-loading" style="margin-right:6px"><Loading /></el-icon>
         AI 初审正在进行中，系统自动刷新...
       </div>
     </div>
 
     <!-- Error state -->
     <div v-if="showError" class="error-section">
       <div class="error-box">
         <el-icon :size="48" color="#e74c3c"><CircleClose /></el-icon>
         <h3>审核处理失败</h3>
         <p>{{ errorMessage }}</p>
         <el-button type="primary" @click="router.back()">返回</el-button>
       </div>
     </div>
 
     <!-- Main content -->
     <template v-if="reviewResult?.aiResult && !showError">
       <!-- Contract Info -->
       <div class="section-card">
         <div class="section-title">
           <el-icon><InfoFilled /></el-icon>
           <span>合同信息</span>
         </div>
         <div class="info-grid">
           <div class="info-item">
             <span class="info-label">合同类型</span>
             <span class="info-value">
               <el-tag size="small" effect="dark" style="background:#4361ee;border:none">
                 {{ CONTRACT_TYPE_LABELS[reviewResult.aiResult.contractType] || reviewResult.aiResult.contractType }}
               </el-tag>
               <span class="conf-badge">{{ (reviewResult.aiResult.typeConfidence * 100).toFixed(0) }}%</span>
             </span>
           </div>
           <div class="info-item">
             <span class="info-label">缺失条款</span>
             <span class="info-value">
               <span v-if="reviewResult.aiResult.missingClauses?.length">
                 <el-tag v-for="mc in reviewResult.aiResult.missingClauses" :key="mc" size="small" type="danger" style="margin:2px;border:none">{{ mc }}</el-tag>
               </span>
               <span v-else class="text-muted">无缺失</span>
             </span>
           </div>
           <div class="info-item" v-if="reviewResult.aiResult.modelName">
             <span class="info-label">AI 模型</span>
             <span class="info-value text-muted">{{ reviewResult.aiResult.modelName }} / {{ reviewResult.aiResult.modelVersion }}</span>
           </div>
           <div class="info-item" v-if="reviewResult.aiResult.processingTimeMs">
             <span class="info-label">处理耗时</span>
             <span class="info-value text-muted">{{ (reviewResult.aiResult.processingTimeMs / 1000).toFixed(1) }}秒</span>
           </div>
         </div>
       </div>
 
       <!-- Elements -->
       <div class="section-card">
         <div class="section-title">
           <el-icon><List /></el-icon>
           <span>关键要素</span>
         </div>
         <div class="elements-grid">
           <div v-for="el in elementsDisplay" :key="el.elementType" class="element-card">
             <div class="element-name">{{ el.elementName }}</div>
             <div class="element-value">
               <div v-if="isLegalEditing && el.elementType !== 'partyA' && el.elementType !== 'partyB'" class="element-edit">
                 <el-input v-model="el.editValue" size="small" />
                 <el-button size="small" type="primary" link @click="saveElement(el)">保存</el-button>
               </div>
               <span v-else>{{ el.value || '未提取' }}</span>
             </div>
             <div class="element-meta">
               <span class="confidence-dot" :style="{ background: getConfColor(el.confidence) }"></span>
               <span>{{ el.confidence ? (el.confidence * 100).toFixed(0) + '%' : '-' }}</span>
               <span style="margin-left:8px" v-if="el.page">第{{ el.page }}页</span>
             </div>
           </div>
         </div>
       </div>
 
       <!-- Risks -->
       <div class="section-card">
         <div class="section-title">
           <el-icon><WarningFilled /></el-icon>
           <span>风险记录</span>
           <div class="risk-summary">
             <span class="risk-count high">{{ highCount }}高</span>
             <span class="risk-count medium">{{ mediumCount }}中</span>
             <span class="risk-count low">{{ lowCount }}低</span>
           </div>
         </div>
 
         <div v-if="risks.length === 0" class="empty-risks">
           <el-icon :size="36" color="#10b981"><CircleCheck /></el-icon>
           <p>未识别出风险项</p>
         </div>
 
         <div v-for="risk in risks" :key="risk.id" class="risk-card" :class="'risk-card--' + risk.riskLevel">
           <div class="risk-top">
             <div class="risk-badge">
               <span class="risk-level-dot" :style="{ background: getRiskColor(risk.riskLevel) }"></span>
               <span>{{ getRiskLevelLabel(risk.riskLevel) }}</span>
             </div>
             <strong class="risk-name">{{ risk.riskName }}</strong>
             <el-tag v-if="risk.status !== 'active'" size="small" type="warning" effect="plain">{{ RISK_STATUS_LABELS[risk.status] }}</el-tag>
           </div>
           <div class="risk-details">
             <div class="risk-detail-row">
               <span class="detail-label">原文</span>
               <span class="detail-text">{{ risk.clauseText }}</span>
             </div>
             <div class="risk-detail-row" v-if="risk.page">
               <span class="detail-label">位置</span>
               <span class="detail-text">第{{ risk.page }}页 {{ risk.paragraphIndex != null ? '· 段落' + risk.paragraphIndex : '' }}</span>
             </div>
             <div class="risk-detail-row">
               <span class="detail-label">依据</span>
               <span class="detail-text">{{ risk.basis }}</span>
             </div>
             <div class="risk-detail-row">
               <span class="detail-label">建议</span>
               <span class="detail-text">{{ risk.suggestion }}</span>
             </div>
             <div class="risk-detail-row" v-if="risk.confidence">
               <span class="detail-label">置信度</span>
               <span class="detail-text">
                 <span class="conf-bar">
                   <span class="conf-fill" :style="{ width: (risk.confidence * 100) + '%', background: getRiskColor(risk.riskLevel) }"></span>
                 </span>
                 <span style="margin-left:6px">{{ (risk.confidence * 100).toFixed(0) }}%</span>
               </span>
             </div>
           </div>
 
           <div v-if="canEditRisks" class="risk-actions">
             <el-select v-model="risk.editLevel" size="small" placeholder="等级" style="width:110px">
               <el-option label="高风险" value="high" />
               <el-option label="中风险" value="medium" />
               <el-option label="低风险" value="low" />
             </el-select>
             <el-select v-model="risk.editStatus" size="small" placeholder="状态" style="width:110px">
               <el-option label="有效" value="active" />
               <el-option label="已修订" value="modified" />
               <el-option label="已忽略" value="dismissed" />
             </el-select>
             <el-button size="small" type="primary" @click="saveRisk(risk)">保存</el-button>
             <el-button size="small" @click="submitRiskFeedback(risk, 'correct')">✓ 正确</el-button>
             <el-button size="small" type="danger" @click="submitRiskFeedback(risk, 'incorrect')">✗ 错误</el-button>
           </div>
         </div>
       </div>
 
       <!-- Legal Review -->
       <div v-if="canLegalReview" class="section-card review-action-card">
         <div class="section-title" style="color:#f59e0b">
           <el-icon><EditPen /></el-icon>
           <span>法务复核</span>
         </div>
         <el-input v-model="legalOpinion" type="textarea" :rows="3" placeholder="输入法务审核意见..." class="opinion-input" />
         <div class="action-footer">
           <el-button type="warning" :loading="legalConfirming" @click="handleLegalConfirm" size="large">
             <el-icon><CircleCheck /></el-icon> 确认完成法务审核
           </el-button>
         </div>
       </div>
       <div v-else-if="reviewResult?.legalReview" class="section-card review-result-card">
         <div class="section-title" style="color:#f59e0b">
           <el-icon><CircleCheck /></el-icon>
           <span>法务复核结果</span>
         </div>
         <div class="result-content">
           <div class="result-row"><span class="result-label">意见</span><span>{{ reviewResult.legalReview.opinion || '无' }}</span></div>
           <div class="result-row"><span class="result-label">时间</span><span>{{ reviewResult.legalReview.reviewedAt || '待完成' }}</span></div>
         </div>
       </div>
 
       <!-- Risk Review -->
       <div v-if="canRiskReview" class="section-card review-action-card">
         <div class="section-title" style="color:#10b981">
           <el-icon><TrendCharts /></el-icon>
           <span>风控复核</span>
         </div>
         <div class="risk-review-form">
           <div class="form-row">
             <div class="form-group">
               <label>总体风险等级</label>
               <el-select v-model="overallRiskLevel" style="width:160px">
                 <el-option label="高风险" value="high" />
                 <el-option label="中风险" value="medium" />
                 <el-option label="低风险" value="low" />
               </el-select>
             </div>
             <div class="form-group">
               <label>风险分数</label>
               <el-input-number v-model="overallScore" :min="0" :max="100" />
             </div>
           </div>
           <el-input v-model="riskOpinion" type="textarea" :rows="3" placeholder="输入风控审核意见..." class="opinion-input" />
           <div class="action-footer">
             <el-button type="success" :loading="riskConfirming" @click="handleRiskConfirm" size="large">
               <el-icon><CircleCheck /></el-icon> 确认完成风控审核
             </el-button>
           </div>
         </div>
       </div>
       <div v-else-if="reviewResult?.riskReview" class="section-card review-result-card">
         <div class="section-title" style="color:#10b981">
           <el-icon><CircleCheck /></el-icon>
           <span>风控复核结果</span>
         </div>
         <div class="result-content">
           <div class="result-row">
             <span class="result-label">总体风险</span>
             <span v-if="reviewResult.riskReview.overallRiskLevel">
               <el-tag :color="getRiskColor(reviewResult.riskReview.overallRiskLevel)" style="color:#fff;border:none" size="small">
                 {{ getRiskLevelLabel(reviewResult.riskReview.overallRiskLevel) }}
               </el-tag>
             </span>
           </div>
           <div class="result-row"><span class="result-label">分数</span><span>{{ reviewResult.riskReview.overallScore }}</span></div>
           <div class="result-row"><span class="result-label">意见</span><span>{{ reviewResult.riskReview.opinion || '无' }}</span></div>
           <div class="result-row"><span class="result-label">时间</span><span>{{ reviewResult.riskReview.reviewedAt || '待完成' }}</span></div>
         </div>
       </div>
 
       <!-- Report -->
       <div v-if="reviewResult.reviewStatus === 'completed'" class="section-card">
         <div class="section-title" style="color:#4361ee">
           <el-icon><Download /></el-icon>
           <span>导出报告</span>
         </div>
         <div class="report-actions">
           <el-button type="primary" @click="generateAndDownload('html')">
             <el-icon><Document /></el-icon> 下载 HTML 报告
           </el-button>
           <el-button type="primary" plain @click="generateAndDownload('pdf')">
             <el-icon><Document /></el-icon> 下载 PDF 报告
           </el-button>
         </div>
       </div>
     </template>
   </div>
 </template>
 
 <script setup lang="ts">
 import { ref, computed, onMounted, onUnmounted } from 'vue'
 import { useRoute, useRouter } from 'vue-router'
 import { ElMessage } from 'element-plus'
 import { Check, Loading, ArrowLeft, CircleClose, InfoFilled, WarningFilled, CircleCheck, EditPen, TrendCharts, Download, Document, List } from '@element-plus/icons-vue'
 import { useAuthStore } from '@/stores/auth'
 import { getReviewResult, getReviewProgress, patchElement, submitFeedback, legalConfirm, riskConfirm, patchOverallRisk } from '@/api/review'
 import { patchRisk } from '@/api/risk'
 import { generateReport, downloadReport } from '@/api/report'
 import type { ReviewResult, ContractElement, RiskRecord } from '@/types'
 import { CONTRACT_TYPE_LABELS, REVIEW_STATUS_LABELS, REVIEW_STAGE_LABELS, RISK_STATUS_LABELS } from '@/types'
 import { getRiskColor, getRiskLevelLabel } from '@/utils/helpers'
 
 const route = useRoute()
 const router = useRouter()
 const authStore = useAuthStore()
 
 const reviewResult = ref<ReviewResult | null>(null)
 const loading = ref(true)
 const showError = ref(false)
 const errorMessage = ref('')
 const isPolling = ref(false)
 const legalOpinion = ref('')
 const riskOpinion = ref('')
 const overallRiskLevel = ref('medium')
 const overallScore = ref(50)
 const legalConfirming = ref(false)
 const riskConfirming = ref(false)
 let pollTimer: ReturnType<typeof setInterval> | null = null
 
 const stageIndex = computed(() => {
   const map: Record<string, number> = { aiReview: 0, legalReview: 1, riskReview: 2, completed: 3 }
   return reviewResult.value ? map[reviewResult.value.reviewStage] ?? 0 : 0
 })
 
 const statusTagType = computed(() => {
   const map: Record<string, string> = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger', cancelled: 'info' }
   return map[reviewResult.value?.reviewStatus || 'pending'] || 'info'
 })
 
 const isLegalEditing = computed(() => authStore.isLegalReviewer && reviewResult.value?.reviewStage === 'legalReview')
 const canLegalReview = computed(() => authStore.isLegalReviewer && reviewResult.value?.reviewStage === 'legalReview')
 const canRiskReview = computed(() => authStore.isRiskReviewer && reviewResult.value?.reviewStage === 'riskReview')
 const canEditRisks = computed(() => (authStore.isLegalReviewer && reviewResult.value?.reviewStage === 'legalReview') || (authStore.isRiskReviewer && reviewResult.value?.reviewStage === 'riskReview'))
 
 const risks = computed(() => (reviewResult.value?.aiResult?.risks || []).map((r: any) => ({ ...r, editLevel: r.riskLevel, editStatus: r.status })))
 const elementsDisplay = computed(() => (reviewResult.value?.effectiveResult?.elements || reviewResult.value?.aiResult?.elements || []).map((e: any) => ({ ...e, editValue: e.value })))
 
 const highCount = computed(() => risks.value.filter((r) => r.riskLevel === 'high').length)
 const mediumCount = computed(() => risks.value.filter((r) => r.riskLevel === 'medium').length)
 const lowCount = computed(() => risks.value.filter((r) => r.riskLevel === 'low').length)
 
 function getConfColor(conf: number | null) {
   if (!conf) return '#e5e7eb'
   if (conf >= 0.8) return '#10b981'
   if (conf >= 0.6) return '#f59e0b'
   return '#e74c3c'
 }
 
 onMounted(() => loadReview())
 onUnmounted(() => stopPolling())
 
 async function loadReview() {
   const id = Number(route.params.id)
   if (isNaN(id)) { loading.value = false; return }
   try {
     const res = await getReviewResult(id)
     reviewResult.value = res.data
     if (res.data.reviewStage === 'aiReview' && res.data.reviewStatus === 'processing') startPolling(id)
     if (res.data.reviewStatus === 'failed') { showError.value = true; errorMessage.value = res.data.aiResult?.warnings?.[0] || 'AI审核处理失败' }
   } catch (err: any) { showError.value = true; errorMessage.value = err?.message || '加载失败' }
   finally { loading.value = false }
 }
 
 function startPolling(reviewId: number) {
   isPolling.value = true
   let attempts = 0
   pollTimer = setInterval(async () => {
     attempts++
     if (attempts > 150) { stopPolling(); ElMessage.warning('轮询超时，请手动刷新'); return }
     try {
       const res = await getReviewProgress(reviewId)
       if (res.data.reviewStage !== 'aiReview' || res.data.reviewStatus === 'failed') { stopPolling(); loadReview() }
     } catch { /* noop */ }
   }, 2000)
 }
 
 function stopPolling() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } isPolling.value = false }
 
 async function saveElement(element: any) {
   if (!reviewResult.value) return
   try { await patchElement(reviewResult.value.reviewId, element.id, element.editValue); ElMessage.success('要素已更新'); loadReview() } catch { /* noop */ }
 }
 async function saveRisk(risk: any) {
   try { await patchRisk(risk.id, { riskLevel: risk.editLevel, riskStatus: risk.editStatus }); ElMessage.success('风险已更新'); loadReview() } catch { /* noop */ }
 }
 async function submitRiskFeedback(risk: any, judgment: string) {
   if (!reviewResult.value) return
   try { await submitFeedback(reviewResult.value.reviewId, 'risk', judgment, risk.id, undefined, `AI ${judgment === 'correct' ? '正确' : '错误'}`); ElMessage.success('反馈已提交') } catch { /* noop */ }
 }
 async function handleLegalConfirm() {
   if (!reviewResult.value) return
   legalConfirming.value = true
   try { await legalConfirm(reviewResult.value.reviewId, legalOpinion.value); ElMessage.success('法务审核已确认'); loadReview() } catch { /* noop */ }
   finally { legalConfirming.value = false }
 }
 async function handleRiskConfirm() {
   if (!reviewResult.value) return
   riskConfirming.value = true
   try { await patchOverallRisk(reviewResult.value.reviewId, overallRiskLevel.value, overallScore.value); await riskConfirm(reviewResult.value.reviewId, riskOpinion.value); ElMessage.success('风控审核已确认'); loadReview() } catch { /* noop */ }
   finally { riskConfirming.value = false }
 }
 async function generateAndDownload(format: string) {
   if (!reviewResult.value) return
   try {
     const genRes = await generateReport(reviewResult.value.reviewId, format)
     const blob = await downloadReport(genRes.data.reportId)
     const url = window.URL.createObjectURL(blob)
     const a = document.createElement('a'); a.href = url; a.download = `report_${reviewResult.value.reviewId}.${format}`; a.click()
     window.URL.revokeObjectURL(url); ElMessage.success('报告已下载')
   } catch { /* noop */ }
 }
 </script>
 
 <style scoped>
 .review-detail { max-width: 900px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
 
 /* Status Bar */
 .status-bar {
   background: #fff; border-radius: 14px; padding: 20px 24px;
   box-shadow: 0 1px 3px rgba(0,0,0,0.06);
 }
 .status-track { display: flex; align-items: center; gap: 0; margin-bottom: 14px; }
 .stage-item { display: flex; align-items: center; gap: 8px; }
 .stage-dot {
   width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
   font-size: 12px; font-weight: 700; color: #fff; transition: all 0.3s;
 }
 .stage-line {
   flex: 1; height: 3px; background: #e5e7eb; margin: 0 8px; border-radius: 2px; transition: background 0.3s;
 }
 .stage-line.active { background: #4361ee; }
 .stage-name { font-size: 13px; color: #9ca3af; font-weight: 500; }
 .stage-item.active .stage-name { color: var(--color-text); }
 .stage-item.done .stage-name { color: var(--color-text); }
 
 .status-meta { display: flex; align-items: center; gap: 8px; }
 .back-link { margin-left: auto; color: var(--color-text-secondary) !important; font-size: 13px; }
 .overall-risk-tag {
   display: inline-flex; align-items: center; gap: 6px;
   padding: 4px 12px; background: #f3f4f6; border-radius: 20px; font-size: 13px; font-weight: 600;
 }
 .risk-dot { width: 8px; height: 8px; border-radius: 50%; }
 .score-badge { font-size: 11px; color: var(--color-text-secondary); margin-left: 2px; }
 .polling-banner {
   margin-top: 12px; padding: 10px 14px; background: #fffbeb; border-radius: 8px;
   font-size: 13px; color: #d97706; display: flex; align-items: center;
 }
 
 /* Error */
 .error-section { display: flex; justify-content: center; padding: 60px 0; }
 .error-box { text-align: center; }
 .error-box h3 { margin: 16px 0 8px; font-size: 18px; }
 .error-box p { color: var(--color-text-secondary); margin-bottom: 20px; font-size: 14px; }
 
 /* Section Card */
 .section-card {
   background: #fff; border-radius: 14px; padding: 20px 24px;
   box-shadow: 0 1px 3px rgba(0,0,0,0.06);
 }
 .section-title {
   display: flex; align-items: center; gap: 8px;
   font-size: 15px; font-weight: 600; margin-bottom: 16px; padding-bottom: 12px;
   border-bottom: 1px solid var(--color-border);
 }
 
 /* Info Grid */
 .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
 .info-item { display: flex; flex-direction: column; gap: 4px; }
 .info-label { font-size: 12px; color: var(--color-text-secondary); font-weight: 500; }
 .info-value { font-size: 14px; display: flex; align-items: center; gap: 6px; }
 .conf-badge {
   font-size: 11px; padding: 1px 8px; background: #eef0ff; color: #4361ee;
   border-radius: 10px; font-weight: 600;
 }
 
 /* Elements */
 .elements-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
 .element-card {
   padding: 14px; background: #f8fafc; border-radius: 10px;
   border: 1px solid var(--color-border); transition: border-color 0.2s;
 }
 .element-card:hover { border-color: #c4b5fd; }
 .element-name { font-size: 12px; color: var(--color-text-secondary); font-weight: 500; margin-bottom: 6px; }
 .element-value { font-size: 14px; font-weight: 600; margin-bottom: 6px; }
 .element-edit { display: flex; gap: 4px; }
 .element-meta { font-size: 11px; color: #9ca3af; display: flex; align-items: center; gap: 4px; }
 .confidence-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
 
 /* Risk Cards */
 .risk-summary { margin-left: auto; display: flex; gap: 10px; font-size: 12px; font-weight: 500; }
 .risk-count.high { color: #dc2626; }
 .risk-count.medium { color: #d97706; }
 .risk-count.low { color: #6b7280; }
 .empty-risks { padding: 40px 0; text-align: center; color: var(--color-text-secondary); }
 .empty-risks p { margin-top: 8px; }
 
 .risk-card {
   border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
   background: #f8fafc; transition: box-shadow 0.2s;
 }
 .risk-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
 .risk-card--high { border-left: 4px solid #dc2626; }
 .risk-card--medium { border-left: 4px solid #d97706; }
 .risk-card--low { border-left: 4px solid #9ca3af; }
 
 .risk-top { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
 .risk-badge {
   display: inline-flex; align-items: center; gap: 4px;
   padding: 2px 10px; background: #fff; border-radius: 12px;
   font-size: 12px; font-weight: 600; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
 }
 .risk-level-dot { width: 6px; height: 6px; border-radius: 50%; }
 .risk-name { font-size: 14px; }
 
 .risk-details { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
 .risk-detail-row { display: flex; gap: 8px; font-size: 13px; line-height: 1.5; }
 .detail-label {
   min-width: 44px; font-size: 12px; color: var(--color-text-secondary);
   font-weight: 500; flex-shrink: 0; padding-top: 1px;
 }
 .detail-text { color: var(--color-text); }
 
 .conf-bar {
   display: inline-block; width: 80px; height: 6px; background: #e5e7eb;
   border-radius: 3px; overflow: hidden; vertical-align: middle;
 }
 .conf-fill { display: block; height: 100%; border-radius: 3px; transition: width 0.5s; }
 
 .risk-actions {
   padding-top: 10px; border-top: 1px solid var(--color-border);
   display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
 }
 
 /* Review Actions */
 .review-action-card { border: 1px solid transparent; }
 .review-action-card:has(.el-button--warning) { border-color: #fde68a; }
 .review-action-card:has(.el-button--success) { border-color: #bbf7d0; }
 .opinion-input { margin-bottom: 12px; }
 .action-footer { display: flex; justify-content: flex-end; }
 
 .review-result-card { }
 .result-content { display: flex; flex-direction: column; gap: 8px; }
 .result-row { display: flex; gap: 12px; font-size: 14px; }
 .result-label { min-width: 80px; color: var(--color-text-secondary); font-weight: 500; }
 
 .risk-review-form { }
 .form-row { display: flex; gap: 20px; margin-bottom: 12px; }
 .form-group { display: flex; flex-direction: column; gap: 4px; }
 .form-group label { font-size: 13px; color: var(--color-text-secondary); font-weight: 500; }
 
 .report-actions { display: flex; gap: 12px; }
 
 .text-muted { color: var(--color-text-secondary); }
 </style>
