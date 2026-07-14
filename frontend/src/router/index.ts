 import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
 import { useAuthStore } from '@/stores/auth'
 import type { Role } from '@/types'

 const routes: RouteRecordRaw[] = [
   {
     path: '/login',
     name: 'Login',
     component: () => import('@/views/login/LoginView.vue'),
     meta: { requiresAuth: false },
   },
   {
     path: '/',
     component: () => import('@/layouts/MainLayout.vue'),
     meta: { requiresAuth: true },
     redirect: '/dashboard',
     children: [
       {
         path: 'dashboard',
         name: 'Dashboard',
         component: () => import('@/views/dashboard/DashboardView.vue'),
         meta: { title: '工作台', roles: ['admin', 'legalReviewer', 'riskReviewer', 'user'] as Role[] },
       },
       {
         path: 'contracts',
         name: 'ContractList',
         component: () => import('@/views/contract/ContractListView.vue'),
         meta: { title: '合同管理', roles: ['user', 'admin'] as Role[] },
       },
       {
         path: 'contracts/:id',
         name: 'ContractDetail',
         component: () => import('@/views/contract/ContractDetailView.vue'),
         meta: { title: '合同详情', roles: ['user', 'legalReviewer', 'riskReviewer', 'admin'] as Role[] },
       },
       {
         path: 'reviews/:id',
         name: 'ReviewDetail',
         component: () => import('@/views/review/ReviewDetailView.vue'),
         meta: { title: '审核详情', roles: ['user', 'legalReviewer', 'riskReviewer', 'admin'] as Role[] },
       },
       {
         path: 'reviews',
         name: 'ReviewHistory',
         component: () => import('@/views/review/ReviewHistoryView.vue'),
         meta: { title: '审核历史', roles: ['user', 'legalReviewer', 'riskReviewer', 'admin'] as Role[] },
       },
       {
         path: 'admin/users',
         name: 'AdminUsers',
         component: () => import('@/views/admin/UserManageView.vue'),
         meta: { title: '用户管理', roles: ['admin'] as Role[] },
       },
       {
         path: 'admin/standard-clauses',
         name: 'AdminStandardClauses',
         component: () => import('@/views/admin/StandardClauseView.vue'),
         meta: { title: '标准条款管理', roles: ['admin'] as Role[] },
       },
       {
         path: 'admin/risk-rules',
         name: 'AdminRiskRules',
         component: () => import('@/views/admin/RiskRuleView.vue'),
         meta: { title: '风险规则管理', roles: ['admin'] as Role[] },
       },
       {
         path: 'admin/feedback',
         name: 'AdminFeedback',
         component: () => import('@/views/admin/FeedbackView.vue'),
         meta: { title: '反馈记录', roles: ['admin'] as Role[] },
       },
       {
         path: 'admin/operation-logs',
         name: 'AdminOperationLogs',
         component: () => import('@/views/admin/OperationLogView.vue'),
         meta: { title: '运行日志', roles: ['admin'] as Role[] },
       },
     ],
   },
 ]

 const router = createRouter({
   history: createWebHistory(),
   routes,
 })

 router.beforeEach((to, _from, next) => {
   const authStore = useAuthStore()
   const requiresAuth = to.meta.requiresAuth !== false

   if (requiresAuth && !authStore.isLoggedIn) {
     next('/login')
     return
   }

   if (to.path === '/login' && authStore.isLoggedIn) {
     next('/dashboard')
     return
   }

   const roles = to.meta.roles as Role[] | undefined
   if (roles && authStore.role && !roles.includes(authStore.role)) {
     next('/dashboard')
     return
   }

   next()
 })

 export default router
