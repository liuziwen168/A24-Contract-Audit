 <template>
   <div class="login-container">
     <!-- Animated background -->
     <div class="bg-pattern">
       <div class="bg-circle bg-circle-1"></div>
       <div class="bg-circle bg-circle-2"></div>
       <div class="bg-circle bg-circle-3"></div>
       <div class="bg-orb bg-orb-1"></div>
       <div class="bg-orb bg-orb-2"></div>
     </div>
 
     <div class="login-card">
       <div class="login-brand">
         <div class="brand-icon">
           <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
             <rect x="3" y="6" width="34" height="28" rx="4" stroke="#4361ee" stroke-width="2.5" fill="none"/>
             <path d="M11 13h18M11 18.5h12M11 24h14" stroke="#4361ee" stroke-width="2" stroke-linecap="round"/>
             <circle cx="32" cy="15" r="6" fill="#4361ee" opacity="0.9"/>
             <path d="M32 12.5v5M29.5 15h5" stroke="#fff" stroke-width="2" stroke-linecap="round"/>
           </svg>
         </div>
         <h1 class="login-title">A24 合同智能审核</h1>
         <p class="login-subtitle">基于大模型的企业合同智能审核与风险预警系统</p>
       </div>
 
       <el-form
         ref="formRef"
         :model="form"
         :rules="rules"
         label-width="0"
         size="large"
         @keyup.enter="handleLogin"
         class="login-form"
       >
         <el-form-item prop="username">
           <el-input
             v-model="form.username"
             placeholder="请输入用户名"
             :prefix-icon="User"
             class="login-input"
           />
         </el-form-item>
         <el-form-item prop="password">
           <el-input
             v-model="form.password"
             type="password"
             placeholder="请输入密码"
             show-password
             :prefix-icon="Lock"
             class="login-input"
           />
         </el-form-item>
         <el-form-item>
           <el-button
             type="primary"
             size="large"
             :loading="loading"
             class="login-btn"
             @click="handleLogin"
           >
             <span v-if="!loading">登 录</span>
           </el-button>
         </el-form-item>
         <div class="login-hint">
           <div class="hint-item">
             <span class="hint-dot" style="background:#e74c3c"></span>
             <span>管理员：admin / admin123</span>
           </div>
           <div class="hint-item">
             <span class="hint-dot" style="background:#f39c12"></span>
             <span>法务：legal / legal123</span>
           </div>
           <div class="hint-item">
             <span class="hint-dot" style="background:#2ecc71"></span>
             <span>风控：risk / risk123 | 用户：user / user123</span>
           </div>
         </div>
       </el-form>
     </div>
   </div>
 </template>

 <script setup lang="ts">
 import { ref, reactive } from 'vue'
 import { useRouter } from 'vue-router'
 import { useAuthStore } from '@/stores/auth'
 import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
 import { User, Lock } from '@element-plus/icons-vue'

 const router = useRouter()
 const authStore = useAuthStore()
 const formRef = ref<FormInstance>()
 const loading = ref(false)

 const form = reactive({
   username: '',
   password: '',
 })

 const rules: FormRules = {
   username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
   password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
 }

 async function handleLogin() {
   const valid = await formRef.value?.validate().catch(() => false)
   if (!valid) return

   loading.value = true
   try {
     await authStore.login(form.username, form.password)
     ElMessage.success('登录成功')
     router.push('/dashboard')
   } catch (err: any) {
     ElMessage.error(err?.message || '登录失败，请检查用户名和密码')
   } finally {
     loading.value = false
   }
 }
 </script>

 <style scoped>
 .login-container {
   min-height: 100vh;
   display: flex;
   align-items: center;
   justify-content: center;
   background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
   position: relative;
   overflow: hidden;
 }
 
 /* Animated background elements */
 .bg-pattern {
   position: absolute;
   inset: 0;
   overflow: hidden;
 }
 .bg-circle {
   position: absolute;
   border-radius: 50%;
   opacity: 0.03;
 }
 .bg-circle-1 {
   width: 600px; height: 600px;
   background: radial-gradient(circle, #4361ee, transparent);
   top: -200px; right: -100px;
   animation: float-slow 12s ease-in-out infinite;
 }
 .bg-circle-2 {
   width: 400px; height: 400px;
   background: radial-gradient(circle, #6366f1, transparent);
   bottom: -150px; left: -150px;
   animation: float-slow 15s ease-in-out infinite reverse;
 }
 .bg-circle-3 {
   width: 300px; height: 300px;
   background: radial-gradient(circle, #8b5cf6, transparent);
   top: 40%; left: 60%;
   animation: float-slow 10s ease-in-out infinite 3s;
 }
 .bg-orb {
   position: absolute;
   width: 800px; height: 800px;
   border-radius: 50%;
   filter: blur(80px);
   opacity: 0.04;
 }
 .bg-orb-1 {
   background: #4361ee;
   top: -300px; left: -200px;
   animation: float-rotate 20s linear infinite;
 }
 .bg-orb-2 {
   background: #8b5cf6;
   bottom: -300px; right: -200px;
   animation: float-rotate 25s linear infinite reverse;
 }
 @keyframes float-slow {
   0%, 100% { transform: translateY(0) scale(1); }
   50% { transform: translateY(-30px) scale(1.05); }
 }
 @keyframes float-rotate {
   0% { transform: rotate(0deg) translateY(0); }
   100% { transform: rotate(360deg) translateY(0); }
 }
 
 .login-card {
   width: 440px;
   padding: 48px 40px 40px;
   background: rgba(255, 255, 255, 0.97);
   border-radius: 20px;
   box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255,255,255,0.05);
   position: relative;
   z-index: 1;
   animation: card-enter 0.6s cubic-bezier(0.16, 1, 0.3, 1);
 }
 @keyframes card-enter {
   from { opacity: 0; transform: translateY(24px) scale(0.96); }
   to { opacity: 1; transform: translateY(0) scale(1); }
 }
 
 .login-brand {
   text-align: center;
   margin-bottom: 36px;
 }
 .brand-icon {
   display: flex;
   justify-content: center;
   margin-bottom: 16px;
 }
 .brand-icon svg {
   filter: drop-shadow(0 2px 8px rgba(67, 97, 238, 0.25));
 }
 .login-title {
   font-size: 22px;
   font-weight: 700;
   color: var(--color-text);
   margin-bottom: 6px;
   letter-spacing: 1px;
 }
 .login-subtitle {
   font-size: 13px;
   color: var(--color-text-secondary);
   line-height: 1.5;
 }
 
 .login-form {
   max-width: 360px;
   margin: 0 auto;
 }
 .login-input :deep(.el-input__wrapper) {
   border-radius: 10px;
   padding: 0 16px;
   box-shadow: 0 0 0 1px #e5e7eb !important;
   transition: box-shadow 0.2s;
 }
 .login-input :deep(.el-input__wrapper:hover) {
   box-shadow: 0 0 0 1px #c4b5fd !important;
 }
 .login-input :deep(.el-input__wrapper.is-focus) {
   box-shadow: 0 0 0 2px #4361ee !important;
 }
 .login-input :deep(.el-input__inner) {
   height: 48px;
 }
 .login-input :deep(.el-input__prefix-inner) {
   color: #9ca3af;
 }
 .login-btn {
   width: 100%;
   height: 48px;
   border-radius: 10px;
   font-size: 16px;
   font-weight: 600;
   letter-spacing: 2px;
   background: linear-gradient(135deg, #4361ee 0%, #6366f1 100%);
   border: none;
   transition: all 0.25s;
   box-shadow: 0 4px 14px rgba(67, 97, 238, 0.35);
 }
 .login-btn:hover {
   transform: translateY(-1px);
   box-shadow: 0 6px 20px rgba(67, 97, 238, 0.45);
 }
 .login-btn:active {
   transform: translateY(0);
 }
 
 .login-hint {
   text-align: left;
   padding: 16px 0 0;
   border-top: 1px solid #f3f4f6;
 }
 .hint-item {
   display: flex;
   align-items: center;
   gap: 8px;
   font-size: 12px;
   color: #9ca3af;
   margin-bottom: 4px;
   line-height: 1.6;
 }
 .hint-dot {
   width: 6px;
   height: 6px;
   border-radius: 50%;
   flex-shrink: 0;
 }
 </style>
