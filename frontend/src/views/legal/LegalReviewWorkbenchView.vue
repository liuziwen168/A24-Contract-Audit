<template>
  <div class="workbench-page" v-loading="loading">
    <div v-if="!reviewId" class="empty-state">
      <el-empty description="缺少审核ID" />
      <el-button type="primary" @click="$router.push('/legal/todo')">返回任务列表</el-button>
    </div>

    <template v-else-if="review">
      <div class="top-bar">
        <el-button @click="$router.push('/legal/todo')">← 返回列表</el-button>
        <span class="title">法务复核 — 审查 #{{ review.id }}</span>
        <el-tag :type="review.reviewStage === 'completed' ? 'success' : 'warning'">
          {{ review.reviewStage === 'legalReview' ? '待法务复核' : review.reviewStage }}
        </el-tag>
      </div>

      <div class="body-grid">
        <!-- 左：AI 提取的合同要素 -->
        <div class="card">
          <h3>合同要素</h3>
          <el-table :data="review.elements || []" size="small" stripe>
            <el-table-column prop="elementName" label="要素名" width="120" />
            <el-table-column prop="value" label="AI 提取值" min-width="180" />
            <el-table-column label="修订值" min-width="180">
              <template #default="{ row, $index }">
                <el-input v-model="elementEdits[$index]" :placeholder="row.value" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row, $index }">
                <el-button size="small" type="primary" @click="saveElement(row, $index)">保存</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 右：风险清单 -->
        <div class="card">
          <h3>风险清单 ({{ (review.risks || []).length }} 项)</h3>
          <div class="risk-item" v-for="(risk, ri) in review.risks" :key="risk.riskId || ri">
            <div class="risk-top">
              <el-tag :type="riskLevelTag(risk.riskLevel)" size="small">{{ risk.riskLevel }}</el-tag>
              <strong>{{ risk.riskName }}</strong>
              <el-tag v-if="riskJudgments[ri]" size="small" type="success" effect="plain">
                {{ riskJudgments[ri] === 'correct' ? '✓ 正确' : '✗ 错误' }}
              </el-tag>
            </div>
            <div class="risk-detail">
              <p><b>原文：</b>{{ risk.clauseText }}</p>
              <p><b>依据：</b>{{ risk.basis }}</p>
              <p><b>建议：</b>{{ risk.suggestion }}</p>
            </div>
            <div class="risk-actions">
              <el-button size="small" type="success" plain @click="judgeRisk(risk, 'correct', ri)">判断正确</el-button>
              <el-button size="small" type="danger" plain @click="judgeRisk(risk, 'incorrect', ri)">判断错误</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部：意见 + 提交 -->
      <div class="card footer-card">
        <h3>法务审核意见</h3>
        <el-input v-model="legalOpinion" type="textarea" :rows="4" placeholder="请输入法务专业意见..." />
        <div class="submit-row">
          <el-tag v-if="allJudged" type="success">全部 {{ (review.risks || []).length }} 项已判定</el-tag>
          <el-tag v-else type="warning">已判定 {{ judgedCount }} / {{ (review.risks || []).length }} 项</el-tag>
          <el-button
            type="primary"
            :disabled="!allJudged"
            :loading="submitting"
            @click="handleConfirm"
            style="margin-left:auto"
          >
            提交法务确认 → 进入风控复核
          </el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getReview, updateElement, submitFeedback, confirmLegal } from '@/api/reviews'

const route = useRoute()
const router = useRouter()

const loading = ref(false)
const submitting = ref(false)
const reviewId = computed(() => Number(route.query.reviewId) || 0)
const review = ref<any>(null)
const elementEdits = reactive<Record<number, string>>({})
const legalOpinion = ref('')

// 风险判定状态，数组下标对应 review.risks 的顺序
const riskJudgments = ref<string[]>([])
const judgedCount = computed(() => riskJudgments.value.filter(Boolean).length)
const allJudged = computed(() => judgedCount.value >= (review.value?.risks?.length || 0))

function riskLevelTag(level: string) {
  const m: Record<string, string> = { low: 'info', medium: 'warning', high: 'danger', critical: 'danger' }
  return m[level] || 'info'
}

async function loadReview() {
  if (!reviewId.value) return
  loading.value = true
  try {
    const r = await getReview(reviewId.value)
    review.value = r
    legalOpinion.value = r.legalOpinion || ''
    // 初始化要素编辑值
    ;(r.elements || []).forEach((el: any, i: number) => {
      elementEdits[i] = el.value || ''
    })
    // 恢复已保存的反馈判定
    const fb = (r as any).feedback || []
    riskJudgments.value = (r.risks || []).map((risk: any) => {
      const match = fb.find((f: any) => f.targetId === (risk.riskId || risk.rule_id))
      return match ? match.judgment : ''
    })
  } catch {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

async function saveElement(el: any, index: number) {
  const newValue = elementEdits[index]
  if (!newValue || newValue === el.value) return
  try {
    await updateElement(reviewId.value, el.id || index, newValue)
    el.value = newValue
    ElMessage.success('要素已更新')
  } catch {
    // handled
  }
}

async function judgeRisk(risk: any, judgment: string, index: number) {
  try {
    const targetId = risk.riskId || risk.rule_id || 0
    await submitFeedback(reviewId.value, {
      targetType: 'risk',
      targetId,
      judgment,
      comment: '',
    })
    // 用数组下标记录判定，确保与模板 v-for 同步
    riskJudgments.value[index] = judgment
    ElMessage.success(judgment === 'correct' ? '已标记为正确' : '已标记为错误')
  } catch {
    // handled
  }
}

async function handleConfirm() {
  if (!allJudged.value) {
    ElMessage.warning('请先对所有风险项进行判定')
    return
  }
  submitting.value = true
  try {
    await confirmLegal(reviewId.value, legalOpinion.value || undefined)
    ElMessage.success('法务确认已提交，审查已进入风控复核阶段')
    router.push('/legal/todo')
  } catch {
    // handled
  } finally {
    submitting.value = false
  }
}

onMounted(() => loadReview())
</script>

<style scoped>
.workbench-page { }
.top-bar { display: flex; align-items: center; gap: 16px; margin-bottom: 20px; }
.title { font-size: 18px; font-weight: 600; }
.empty-state { text-align: center; padding: 80px 0; }
.body-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
.card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.card h3 { margin: 0 0 16px; font-size: 16px; color: #303133; }
.risk-item { padding: 12px 0; border-bottom: 1px solid #ebeef5; }
.risk-item:last-child { border-bottom: none; }
.risk-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.risk-detail { font-size: 13px; color: #606266; line-height: 1.7; }
.risk-detail p { margin: 4px 0; }
.risk-actions { margin-top: 8px; display: flex; gap: 8px; }
.footer-card { }
.submit-row { display: flex; align-items: center; gap: 12px; margin-top: 16px; }
</style>
