<template>
  <div class="login-container">
    <!-- 左侧品牌区域 -->
    <div class="login-left">
      <div class="brand-content">
        <h1 class="brand-title">企业合同智能审核与风险预警系统</h1>
        <p class="brand-subtitle">AI辅助风险识别 · 法务风控专业闭环决策</p>
        <p class="brand-desc">合同全生命周期智能审阅平台</p>
      </div>
      <div class="brand-footer">
        <span class="footer-link">技术支持</span>
        <span class="footer-link">安全合规</span>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="login-right">
      <div class="login-card">
        <div class="login-header">
          <span class="header-bar"></span>
          <h2 class="header-title">系统登录</h2>
        </div>

        <el-form
          ref="formRef"
          :model="loginForm"
          :rules="rules"
          class="login-form"
          size="large"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <div class="form-label">用户名</div>
            <el-input
              v-model="loginForm.username"
              placeholder="请输入工号或账号"
              clearable
              prefix-icon="User"
            />
          </el-form-item>

          <el-form-item prop="password">
            <div class="form-label">密码</div>
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入您的密码"
              show-password
              prefix-icon="Lock"
            />
          </el-form-item>

          <div class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" :underline="false" class="forgot-link">
              忘记密码？
            </el-link>
          </div>

          <el-form-item class="submit-item">
            <el-button
              type="primary"
              class="login-btn"
              :loading="loading"
              @click="handleLogin"
            >
              立即登录
            </el-button>
          </el-form-item>
        
        </el-form>

        <div class="login-footer">
          <span class="version-text">系统版本 v1.0</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const rememberMe = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
})

const rules = reactive<FormRules>({
  username: [
    { required: true, message: '请输入工号或账号', trigger: 'blur' },
    { min: 2, max: 64, message: '账号长度在 2 到 64 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 32, message: '密码长度在 6 到 32 个字符', trigger: 'blur' },
  ],
})


async function handleLogin() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      await userStore.login(loginForm.username, loginForm.password)
    } catch (err: any) {
      ElMessage.error(err.message || '登录失败，请检查账号密码')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

/* ========== 左侧品牌区域 ========== */
.login-left {
  flex: 1;
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px 80px;
  background-color: #f0f2f5;
  overflow: hidden;
}

/* 电路板背景纹理 */
.login-left::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    /* 水平线 */
    linear-gradient(90deg, transparent 0%, transparent 49.5%, rgba(180, 200, 220, 0.15) 49.5%, rgba(180, 200, 220, 0.15) 50.5%, transparent 50.5%, transparent 100%),
    linear-gradient(90deg, transparent 0%, transparent 24.5%, rgba(180, 200, 220, 0.1) 24.5%, rgba(180, 200, 220, 0.1) 25.5%, transparent 25.5%, transparent 100%),
    linear-gradient(90deg, transparent 0%, transparent 74.5%, rgba(180, 200, 220, 0.1) 74.5%, rgba(180, 200, 220, 0.1) 75.5%, transparent 75.5%, transparent 100%),
    /* 垂直线 */
    linear-gradient(0deg, transparent 0%, transparent 49.5%, rgba(180, 200, 220, 0.15) 49.5%, rgba(180, 200, 220, 0.15) 50.5%, transparent 50.5%, transparent 100%),
    linear-gradient(0deg, transparent 0%, transparent 24.5%, rgba(180, 200, 220, 0.1) 24.5%, rgba(180, 200, 220, 0.1) 25.5%, transparent 25.5%, transparent 100%),
    linear-gradient(0deg, transparent 0%, transparent 74.5%, rgba(180, 200, 220, 0.1) 74.5%, rgba(180, 200, 220, 0.1) 75.5%, transparent 75.5%, transparent 100%),
    /* 斜线装饰 */
    linear-gradient(45deg, transparent 48%, rgba(180, 200, 220, 0.08) 48%, rgba(180, 200, 220, 0.08) 52%, transparent 52%),
    linear-gradient(-45deg, transparent 48%, rgba(180, 200, 220, 0.08) 48%, rgba(180, 200, 220, 0.08) 52%, transparent 52%);
  background-size:
    200px 200px,
    200px 200px,
    200px 200px,
    200px 200px,
    200px 200px,
    200px 200px,
    280px 280px,
    280px 280px;
  opacity: 0.8;
  pointer-events: none;
}

/* 左下角电路装饰线 */
.login-left::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 500px;
  height: 300px;
  background:
    linear-gradient(135deg, transparent 30%, rgba(180, 200, 220, 0.12) 30%, rgba(180, 200, 220, 0.12) 30.5%, transparent 30.5%),
    linear-gradient(135deg, transparent 40%, rgba(180, 200, 220, 0.1) 40%, rgba(180, 200, 220, 0.1) 40.5%, transparent 40.5%),
    linear-gradient(135deg, transparent 50%, rgba(180, 200, 220, 0.08) 50%, rgba(180, 200, 220, 0.08) 50.5%, transparent 50.5%),
    linear-gradient(135deg, transparent 60%, rgba(180, 200, 220, 0.06) 60%, rgba(180, 200, 220, 0.06) 60.5%, transparent 60.5%);
  background-size: 400px 400px;
  pointer-events: none;
}

.brand-content {
  position: relative;
  z-index: 1;
  max-width: 600px;
}

.brand-title {
  font-size: 42px;
  font-weight: 700;
  color: #1a6fc4;
  line-height: 1.3;
  margin-bottom: 20px;
  letter-spacing: 2px;
}

.brand-subtitle {
  font-size: 18px;
  color: #606266;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.brand-desc {
  font-size: 15px;
  color: #909399;
  letter-spacing: 1px;
}

.brand-footer {
  position: absolute;
  bottom: 40px;
  left: 80px;
  display: flex;
  gap: 40px;
  z-index: 1;
}

.footer-link {
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  transition: color 0.3s;
}

.footer-link:hover {
  color: #1a6fc4;
}

/* ========== 右侧登录表单 ========== */
.login-right {
  width: 480px;
  min-width: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #f5f7fa;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 8px;
  padding: 40px 36px 32px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.login-header {
  display: flex;
  align-items: center;
  margin-bottom: 32px;
}

.header-bar {
  display: inline-block;
  width: 4px;
  height: 22px;
  background-color: #1a6fc4;
  border-radius: 2px;
  margin-right: 12px;
}

.header-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  letter-spacing: 1px;
}

.login-form {
  margin-bottom: 0;
}

.form-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
  font-weight: 500;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  height: 44px;
  border-radius: 4px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: box-shadow 0.3s;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #1a6fc4 inset;
}

.login-form :deep(.el-input__inner) {
  font-size: 14px;
  height: 44px;
  line-height: 44px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  margin-top: -4px;
}

.forgot-link {
  font-size: 14px;
}

.submit-item {
  margin-bottom: 0 !important;
}

.login-btn {
  width: 100%;
  height: 46px;
  font-size: 16px;
  font-weight: 500;
  letter-spacing: 4px;
  border-radius: 4px;
  background-color: #1a6fc4;
  border-color: #1a6fc4;
}

.login-btn:hover {
  background-color: #1560ad;
  border-color: #1560ad;
}

.login-footer {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  text-align: center;
}

.version-text {
  font-size: 13px;
  color: #c0c4cc;
}

/* ========== 响应式 ========== */
@media (max-width: 900px) {
  .login-left {
    display: none;
  }

  .login-right {
    width: 100%;
    min-width: unset;
  }
}

</style>



