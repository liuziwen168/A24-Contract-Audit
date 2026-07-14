 <template>
   <div class="layout-container">
     <el-container style="height: 100vh">
       <transition name="slide-side">
         <el-aside :width="isCollapse ? '64px' : '240px'" class="layout-aside">
           <div class="logo-area">
             <div class="logo-icon">
               <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                 <rect x="2" y="4" width="24" height="20" rx="3" stroke="#4361ee" stroke-width="2" fill="none"/>
                 <path d="M8 10h12M8 14h8M8 18h10" stroke="#4361ee" stroke-width="2" stroke-linecap="round"/>
                 <circle cx="22" cy="10" r="4" fill="#4361ee"/>
                 <path d="M22 8.5v3M20.5 10h3" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
               </svg>
             </div>
             <span v-if="!isCollapse" class="logo-text">A24 合同审核</span>
           </div>
 
           <div class="menu-scroll">
             <el-menu
               :default-active="activeMenu"
               :collapse="isCollapse"
               :router="true"
               :collapse-transition="false"
               background-color="transparent"
               text-color="var(--sidebar-text)"
               active-text-color="#fff"
             >
               <div class="menu-section-label" v-if="!isCollapse">概览</div>
               <el-menu-item index="/dashboard">
                 <el-icon><Odometer /></el-icon>
                 <template #title>工作台</template>
               </el-menu-item>
 
               <div class="menu-section-label" v-if="!isCollapse">业务</div>
               <el-menu-item v-if="authStore.isRegularUser || authStore.isAdmin" index="/contracts">
                 <el-icon><Document /></el-icon>
                 <template #title>合同管理</template>
               </el-menu-item>
 
               <el-menu-item v-if="authStore.isReviewer || authStore.isRegularUser || authStore.isAdmin" index="/reviews">
                 <el-icon><List /></el-icon>
                 <template #title>审核历史</template>
               </el-menu-item>
 
               <div class="menu-section-label" v-if="authStore.isAdmin && !isCollapse">系统</div>
               <el-sub-menu v-if="authStore.isAdmin" index="admin">
                 <template #title>
                   <el-icon><Setting /></el-icon>
                   <span>系统管理</span>
                 </template>
                 <el-menu-item index="/admin/users">用户管理</el-menu-item>
                 <el-menu-item index="/admin/standard-clauses">标准条款</el-menu-item>
                 <el-menu-item index="/admin/risk-rules">风险规则</el-menu-item>
                 <el-menu-item index="/admin/feedback">反馈记录</el-menu-item>
                 <el-menu-item index="/admin/operation-logs">运行日志</el-menu-item>
               </el-sub-menu>
             </el-menu>
           </div>
 
           <div class="sidebar-footer" v-if="!isCollapse">
             <div class="footer-divider"></div>
             <div class="user-badge">
               <div class="user-avatar-mini">{{ authStore.username.charAt(0).toUpperCase() }}</div>
               <div class="user-info-mini">
                 <span class="user-name-mini">{{ authStore.username }}</span>
                 <span class="user-role-mini">{{ roleLabel }}</span>
               </div>
             </div>
           </div>
         </el-aside>
       </transition>
 
       <el-container>
         <el-header class="layout-header">
           <div class="header-left">
             <el-button :icon="isCollapse ? Expand : Fold" text @click="toggleCollapse" class="collapse-btn" />
             <el-breadcrumb separator="|">
               <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
               <el-breadcrumb-item v-if="route.meta?.title">{{ route.meta.title }}</el-breadcrumb-item>
             </el-breadcrumb>
           </div>
           <div class="header-right">
             <div class="header-actions">
               <el-tag v-if="authStore.role" :type="roleTagType" size="small" effect="plain" class="role-tag">
                 {{ roleLabel }}
               </el-tag>
               <div class="user-dropdown">
                 <div class="user-avatar">{{ authStore.username.charAt(0).toUpperCase() }}</div>
                 <span class="user-name">{{ authStore.username }}</span>
               </div>
               <el-button text size="small" class="logout-btn" @click="handleLogout">
                 <el-icon><SwitchButton /></el-icon>
                 <span style="margin-left:4px">退出</span>
               </el-button>
             </div>
           </div>
         </el-header>
 
         <el-main class="layout-main">
           <router-view v-slot="{ Component }">
             <transition name="fade" mode="out-in">
               <component :is="Component" />
             </transition>
           </router-view>
         </el-main>
       </el-container>
     </el-container>
   </div>
 </template>

 <script setup lang="ts">
 import { ref, computed } from 'vue'
 import { useRoute, useRouter } from 'vue-router'
 import { useAuthStore } from '@/stores/auth'
 import { Fold, Expand, Odometer, Document, List, Setting, SwitchButton } from '@element-plus/icons-vue'
 import { USER_ROLE_LABELS } from '@/types'

 const route = useRoute()
 const router = useRouter()
 const authStore = useAuthStore()
 const isCollapse = ref(false)

 const activeMenu = computed(() => route.path)
 const roleLabel = computed(() => USER_ROLE_LABELS[authStore.role || ''] || '')
 const roleTagType = computed(() => {
   const map: Record<string, string> = { admin: 'danger', legalReviewer: 'warning', riskReviewer: 'success', user: 'info' }
   return map[authStore.role || ''] || 'info'
 })

 function toggleCollapse() {
   isCollapse.value = !isCollapse.value
 }

 function handleLogout() {
   authStore.logout()
   router.push('/login')
 }
 </script>

 <style scoped>
 .layout-container {
   height: 100vh;
   overflow: hidden;
 }
 <style scoped>
 .layout-container {
   height: 100vh;
   overflow: hidden;
   background: var(--color-bg);
 }
 .layout-aside {
   background: var(--sidebar-bg);
   transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
   display: flex;
   flex-direction: column;
   overflow: hidden;
   border-right: 1px solid rgba(255,255,255,0.06);
 }
 .logo-area {
   height: 64px;
   display: flex;
   align-items: center;
   gap: 10px;
   padding: 0 16px;
   border-bottom: 1px solid rgba(255,255,255,0.06);
   flex-shrink: 0;
 }
 .logo-icon {
   display: flex;
   align-items: center;
   flex-shrink: 0;
 }
 .logo-text {
   color: #fff;
   font-size: 17px;
   font-weight: 700;
   letter-spacing: 0.5px;
   white-space: nowrap;
 }
 .menu-scroll {
   flex: 1;
   overflow-y: auto;
   overflow-x: hidden;
   padding: 8px 0;
 }
 .menu-scroll::-webkit-scrollbar { width: 3px; }
 .menu-scroll::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
 
 .menu-section-label {
   padding: 16px 20px 6px;
   font-size: 11px;
   font-weight: 600;
   text-transform: uppercase;
   letter-spacing: 0.8px;
   color: rgba(255,255,255,0.25);
 }
 
 .el-menu {
   border-right: none !important;
 }
 .el-menu-item {
   margin: 2px 8px;
   border-radius: 8px;
   height: 40px;
   line-height: 40px;
   padding: 0 12px !important;
 }
 .el-menu-item:hover {
   background-color: rgba(255,255,255,0.08) !important;
 }
 .el-menu-item.is-active {
   background: linear-gradient(135deg, var(--sidebar-active), #6366f1) !important;
   box-shadow: 0 4px 12px rgba(67, 97, 238, 0.35);
 }
 .el-sub-menu__title {
   margin: 2px 8px;
   border-radius: 8px;
   height: 40px;
   line-height: 40px;
   padding: 0 12px !important;
 }
 .el-sub-menu__title:hover {
   background-color: rgba(255,255,255,0.08) !important;
 }
 
 .sidebar-footer {
   flex-shrink: 0;
   padding: 12px 16px 16px;
 }
 .footer-divider {
   height: 1px;
   background: rgba(255,255,255,0.06);
   margin-bottom: 12px;
 }
 .user-badge {
   display: flex;
   align-items: center;
   gap: 10px;
 }
 .user-avatar-mini {
   width: 32px;
   height: 32px;
   border-radius: 8px;
   background: linear-gradient(135deg, #4361ee, #6366f1);
   color: #fff;
   display: flex;
   align-items: center;
   justify-content: center;
   font-size: 14px;
   font-weight: 700;
   flex-shrink: 0;
 }
 .user-info-mini {
   display: flex;
   flex-direction: column;
   gap: 2px;
   overflow: hidden;
 }
 .user-name-mini {
   font-size: 13px;
   font-weight: 600;
   color: rgba(255,255,255,0.85);
   white-space: nowrap;
   overflow: hidden;
   text-overflow: ellipsis;
 }
 .user-role-mini {
   font-size: 11px;
   color: rgba(255,255,255,0.4);
 }
 
 .layout-header {
   display: flex;
   align-items: center;
   justify-content: space-between;
   padding: 0 24px;
   background: rgba(255,255,255,0.85);
   backdrop-filter: blur(12px);
   -webkit-backdrop-filter: blur(12px);
   border-bottom: 1px solid var(--color-border);
   height: 64px;
 }
 .header-left {
   display: flex;
   align-items: center;
   gap: 16px;
 }
 .collapse-btn {
   color: var(--color-text-secondary) !important;
   font-size: 18px;
 }
 .header-right {
   display: flex;
   align-items: center;
 }
 .header-actions {
   display: flex;
   align-items: center;
   gap: 14px;
 }
 .role-tag {
   font-weight: 500;
   border-radius: 6px;
 }
 .user-dropdown {
   display: flex;
   align-items: center;
   gap: 8px;
   cursor: pointer;
 }
 .user-avatar {
   width: 32px;
   height: 32px;
   border-radius: 8px;
   background: linear-gradient(135deg, #6366f1, #8b5cf6);
   color: #fff;
   display: flex;
   align-items: center;
   justify-content: center;
   font-size: 14px;
   font-weight: 700;
 }
 .user-name {
   font-size: 14px;
   font-weight: 500;
   color: var(--color-text);
 }
 .logout-btn {
   color: var(--color-text-secondary) !important;
 }
 .logout-btn:hover {
   color: var(--color-danger) !important;
 }
 .layout-main {
   padding: 24px;
   overflow-y: auto;
   height: calc(100vh - 64px);
   background: var(--color-bg);
 }
 
 /* Slide transition for sidebar */
.slide-side-enter-active, .slide-side-leave-active {
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
