<template>
  <div class="profile-page">
    <div class="page-header">
      <h1 class="page-title">个人设置</h1>
      <p class="page-desc">管理您的个人信息、通知偏好和安全设置。</p>
    </div>

    <div class="profile-content">
      <!-- 基础信息 -->
      <div class="info-card">
        <div class="card-header">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1a6fc4" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span class="card-title">基础信息</span>
        </div>
        <div class="info-body">
          <div class="info-left">
            <div class="user-avatar-lg">
              <svg viewBox="0 0 80 80" width="80" height="80"><circle cx="40" cy="40" r="40" fill="#1a6fc4"/><text x="40" y="48" text-anchor="middle" fill="#fff" font-size="28" font-weight="600">R</text></svg>
            </div>
            <div class="user-info">
              <h2 class="user-display-name">riskReviewer</h2>
              <el-tag type="primary" size="small" effect="plain" class="role-tag">风控专员</el-tag>
              <p class="permission-desc">权限范围：合同风控复核、预警处置、逾期监控、审核报告生成、风险等级最终裁断。</p>
            </div>
          </div>
          <div class="info-right">
            <div class="ai-badge">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#1a6fc4" stroke-width="2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
              <span>通义千问 Qwen 大模型智能风控服务支持</span>
            </div>
            <p>本系统深度融合阿里通义千问 Qwen 大模型核心能力，支持合同风险智能识别、条款合规性自动检测及动态风险评估。系统利用 NLP 语义分析及法律知识图谱技术，能够自动捕捉合同文本中的潜在法律瑕疵与商务风险，为您提供精准的风险预警与裁断建议。</p>
          </div>
        </div>
      </div>

      <!-- 通知设置 -->
      <div class="info-card">
        <div class="card-header">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1a6fc4" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
          <span class="card-title">通知设置</span>
        </div>
        <div class="setting-list">
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">新任务通知</div>
              <div class="setting-desc">当有新的风控复核任务分配时发送通知</div>
            </div>
            <el-switch v-model="settings.newTask" />
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">逾期预警通知</div>
              <div class="setting-desc">当合同审核流程出现逾期时发送提醒</div>
            </div>
            <el-switch v-model="settings.overdue" />
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">高风险预警通知</div>
              <div class="setting-desc">当系统识别出高风险条款时立即通知</div>
            </div>
            <el-switch v-model="settings.highRisk" />
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">邮件通知</div>
              <div class="setting-desc">同时发送邮件到工作邮箱</div>
            </div>
            <el-switch v-model="settings.email" />
          </div>
        </div>
      </div>

      <!-- 安全设置 -->
      <div class="info-card">
        <div class="card-header">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#1a6fc4" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
          <span class="card-title">安全设置</span>
        </div>
        <div class="setting-list">
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">修改密码</div>
              <div class="setting-desc">定期更换密码以保障账户安全</div>
            </div>
            <el-button size="small">修改</el-button>
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">双因素认证</div>
              <div class="setting-desc">启用后登录时需要额外验证</div>
            </div>
            <el-switch v-model="settings.twoFactor" />
          </div>
          <div class="setting-item">
            <div class="setting-info">
              <div class="setting-label">登录日志</div>
              <div class="setting-desc">查看最近的登录记录和设备信息</div>
            </div>
            <el-button size="small">查看</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'

const settings = reactive({
  newTask: true,
  overdue: true,
  highRisk: true,
  email: false,
  twoFactor: false,
})
</script>

<style scoped>
.profile-page { }

.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
  margin-bottom: 8px;
}

.page-desc {
  font-size: 14px;
  color: #909399;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.info-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

.info-left {
  display: flex;
  gap: 20px;
}

.user-avatar-lg {
  flex-shrink: 0;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user-display-name {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.role-tag {
  align-self: flex-start;
}

.permission-desc {
  font-size: 13px;
  color: #909399;
  line-height: 1.6;
  margin: 0;
}

.info-right {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #ecf5ff;
  color: #1a6fc4;
  font-size: 13px;
  padding: 6px 14px;
  border-radius: 20px;
  align-self: flex-start;
}

.info-right p {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  margin: 0;
}

.setting-list {
  display: flex;
  flex-direction: column;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid #f5f5f5;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-label {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.setting-desc {
  font-size: 13px;
  color: #909399;
}
</style>
