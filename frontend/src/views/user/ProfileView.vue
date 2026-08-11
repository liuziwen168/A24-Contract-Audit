<template>
  <div class="profile-page">
    <!-- 基础信息 -->
    <div class="info-card">
      <div class="card-header">
        <el-icon><OfficeBuilding /></el-icon>
        <span class="card-title">基础信息</span>
      </div>
      <div class="info-body">
        <div class="info-left">
          <h2 class="user-display-name">张三</h2>
          <el-tag type="primary" size="small" effect="plain" class="role-tag">合同经办人</el-tag>
          <p class="permission-desc">权限范围：合同上传及起草、初审任务提交、风险整改反馈、合同台账查询、审核报告导出下载。</p>
        </div>
        <div class="info-right">
          <div class="ai-badge">
            <el-icon><Star /></el-icon>
            <span>通义千问Qwen大模型智能服务支持</span>
          </div>
          <p>本系统深度融合阿里通义千问Qwen大模型核心能力，支持合同智能解析、复杂法律条款识别及动态风险评估。系统利用NLP语义分析及法律知识图谱技术，能够自动捕捉合同文本中的潜在法律瑕疵与商务风险，为您提供精准的风险预警与修正建议。</p>
        </div>
      </div>
    </div>

    <!-- 安全设置 -->
    <div class="security-card">
      <div class="card-header">
        <el-icon><Lock /></el-icon>
        <span class="card-title">安全设置 · 登录密码修改</span>
      </div>
      <div class="security-body">
        <div class="form-section">
          <el-form :model="pwdForm" :rules="pwdRules" ref="pwdFormRef" label-position="top" style="max-width:560px">
            <el-form-item label="原登录密码" prop="oldPassword">
              <el-input v-model="pwdForm.oldPassword" type="password" placeholder="请输入当前使用的密码" show-password />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input v-model="pwdForm.newPassword" type="password" placeholder="设置新密码" show-password />
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input v-model="pwdForm.confirmPassword" type="password" placeholder="请再次输入新密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" class="btn-save" @click="handleSave">保存修改</el-button>
              <el-button class="btn-reset" @click="handleReset">重置表单</el-button>
            </el-form-item>
          </el-form>
        </div>
        <div class="security-notice">
          <div class="notice-title">
            <el-icon><Key /></el-icon> 账号安全须知
          </div>
          <div class="notice-item">
            <span class="notice-num">1</span>
            <span>密码修改后，当前会话将立即失效，系统将强制跳转至登录页要求重新验证身份。</span>
          </div>
          <div class="notice-item">
            <span class="notice-num">2</span>
            <span>严禁将账号密码借予他人使用。由于本账号涉及合同机密权限，所有操作均将被审计留存日志。</span>
          </div>
          <div class="notice-item">
            <span class="notice-num">3</span>
            <span>审计备注：根据企业合规要求，敏感账户每90天需进行一次密码更新，逾期将限制导出权限。</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 页脚 -->
    <div class="page-footer">
      <div class="footer-left">
        <p>技术驱动 · 法律合规大模型落地应用</p>
        <p>© 2024 A24 Enterprise Intelligence (China). All Rights Reserved. 企业级合同风控赋能平台。</p>
      </div>
      <div class="footer-right">
        <p>本系统依托 AI 技术辅助审核，审核结论仅供专业参考，不构成法律咨询意见。</p>
        <p>AI 算法支撑：通义千问 Qwen-Max-Ultra 法律合规定制版</p>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { OfficeBuilding, Star, Lock, Key } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const pwdFormRef = ref<FormInstance>()
const pwdForm = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const pwdRules = reactive<FormRules>({
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请设置新密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: (_rule, value, callback) => { if (value !== pwdForm.newPassword) callback(new Error('两次输入密码不一致')); else callback() }, trigger: 'blur' },
  ],
})

function handleSave() {
  pwdFormRef.value?.validate((valid) => {
    if (valid) ElMessage.success('密码修改成功，请重新登录')
  })
}
function handleReset() { pwdForm.oldPassword = ''; pwdForm.newPassword = ''; pwdForm.confirmPassword = '' }
</script>
<style scoped>
.profile-page { }
.info-card, .security-card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px; }
.card-header { display: flex; align-items: center; gap: 8px; padding: 20px 24px 16px; border-bottom: 1px solid #ebeef5; }
.card-header .el-icon { color: #1a6fc4; font-size: 18px; }
.card-title { font-size: 16px; font-weight: 600; color: #303133; }
.info-body { display: grid; grid-template-columns: 1fr 1.5fr; gap: 24px; padding: 24px; }
.user-display-name { font-size: 28px; font-weight: 600; color: #303133; margin-bottom: 12px; }
.role-tag { margin-bottom: 12px; }
.permission-desc { font-size: 14px; color: #909399; line-height: 1.8; }
.info-right p { font-size: 14px; color: #606266; line-height: 1.8; }
.ai-badge { display: flex; align-items: center; gap: 8px; background: #ecf5ff; border: 1px solid #d9ecff; border-radius: 6px; padding: 10px 16px; margin-bottom: 12px; font-size: 14px; color: #1a6fc4; font-weight: 500; }
.security-body { display: grid; grid-template-columns: 1.5fr 1fr; gap: 24px; padding: 24px; }
.btn-save { background: #1a6fc4; border-color: #1a6fc4; }
.btn-reset { }
.security-notice { background: #fafafa; border: 1px dashed #dcdfe6; border-radius: 8px; padding: 20px; }
.notice-title { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 600; color: #303133; margin-bottom: 16px; }
.notice-title .el-icon { color: #e6a23c; }
.notice-item { display: flex; gap: 10px; margin-bottom: 14px; font-size: 13px; color: #606266; line-height: 1.6; }
.notice-num { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 50%; background: #ecf5ff; color: #1a6fc4; font-size: 12px; font-weight: 600; flex-shrink: 0; }
.page-footer { display: flex; justify-content: space-between; padding: 20px 0; font-size: 13px; color: #c0c4cc; line-height: 1.8; }
.footer-left p:first-child { color: #1a6fc4; }
</style>

