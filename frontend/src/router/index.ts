import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/login/LoginView.vue'),
    meta: { title: '系统登录', requiresAuth: false },
  },
  {
    path: '/',
    redirect: (to: any) => {
      // 根据 localStorage 缓存角色决定首页跳转
      try {
        const stored = localStorage.getItem('userInfo')
        if (stored) {
          const u = JSON.parse(stored)
          return roleHomeMap[u.role] || '/user/contracts'
        }
      } catch { /* fall through */ }
      return '/login'
    },
  },
  {
    path: '/user',
    component: () => import('@/views/layout/LayoutView.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/user/contracts' },
      {
        path: 'contracts',
        name: 'UserContracts',
        component: () => import('@/views/user/ContractsView.vue'),
        meta: { title: '合同管理' },
      },
      {
        path: 'reviews',
        name: 'UserReviews',
        component: () => import('@/views/user/ReviewsView.vue'),
        meta: { title: '我的审核任务' },
      },
      {
        path: 'warnings',
        name: 'UserWarnings',
        component: () => import('@/views/user/WarningsView.vue'),
        meta: { title: '风险预警中心' },
      },
      {
        path: 'reports',
        name: 'UserReports',
        component: () => import('@/views/user/ReportsView.vue'),
        meta: { title: '报告下载中心' },
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/user/ProfileView.vue'),
        meta: { title: '个人中心' },
      },
      {
        path: 'ai-bot',
        name: 'UserAiBot',
        component: () => import('@/views/user/AiBotView.vue'),
        meta: { title: '智能 AI 机器人' },
      },
    ],
  },
  // ========== 法务审核员角色 ==========
  {
    path: '/legal',
    component: () => import('@/views/legal/LegalLayoutView.vue'),
    meta: { requiresAuth: true, role: 'legalReviewer' },
    redirect: '/legal/todo',
    children: [
      {
        path: 'todo',
        name: 'LegalTodo',
        component: () => import('@/views/legal/LegalTodoView.vue'),
        meta: { title: '法务待办列表' },
      },
      {
        path: 'cases',
        name: 'LegalCases',
        component: () => import('@/views/legal/CaseManagementView.vue'),
        meta: { title: '案件管理' },
      },
      {
        path: 'workbench',
        name: 'LegalWorkbench',
        component: () => import('@/views/legal/LegalReviewWorkbenchView.vue'),
        meta: { title: '法务复核工作台' },
      },
      {
        path: 'archive',
        name: 'LegalArchive',
        component: () => import('@/views/legal/AuditArchiveView.vue'),
        meta: { title: '合同审计档案详情' },
      },
      {
        path: 'compliance',
        name: 'LegalCompliance',
        component: () => import('@/views/legal/ComplianceAuditView.vue'),
        meta: { title: '合规审计详情' },
      },
    ],
  },
  // ========== 风控审核员角色 ==========
  {
    path: '/risk',
    component: () => import('@/views/risk/RiskLayoutView.vue'),
    meta: { requiresAuth: true, role: 'riskReviewer' },
    redirect: '/risk/workbench',
    children: [
      {
        path: 'workbench',
        name: 'RiskWorkbench',
        component: () => import('@/views/risk/RiskReviewWorkbenchView.vue'),
        meta: { title: '复核工作台' },
      },
      {
        path: 'warning',
        name: 'RiskWarning',
        component: () => import('@/views/risk/RiskWarningView.vue'),
        meta: { title: '预警处置' },
      },
      {
        path: 'ledger',
        name: 'RiskLedger',
        component: () => import('@/views/risk/RiskAuditLedgerView.vue'),
        meta: { title: '审核台账' },
      },
      {
        path: 'overdue',
        name: 'RiskOverdue',
        component: () => import('@/views/risk/RiskOverdueView.vue'),
        meta: { title: '逾期清单' },
      },
      {
        path: 'report',
        name: 'RiskReport',
        component: () => import('@/views/risk/RiskReportView.vue'),
        meta: { title: '审核报告' },
      },
      {
        path: 'profile',
        name: 'RiskProfile',
        component: () => import('@/views/risk/RiskProfileView.vue'),
        meta: { title: '个人设置' },
      },
    ],
  },
  // ========== 管理员角色 ==========
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayoutView.vue'),
    meta: { requiresAuth: true, role: 'admin' },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/OperationsDashboardView.vue'),
        meta: { title: '运营看板' },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UserManagementView.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'clauses',
        name: 'AdminClauses',
        component: () => import('@/views/admin/StandardClausesView.vue'),
        meta: { title: '标准条款管理' },
      },
      {
        path: 'risk-rules',
        name: 'AdminRiskRules',
        component: () => import('@/views/admin/RiskRulesView.vue'),
        meta: { title: '风险规则管理' },
      },
      {
        path: 'audit-records',
        name: 'AdminAuditRecords',
        component: () => import('@/views/admin/FullAuditRecordsView.vue'),
        meta: { title: '全量审核记录' },
      },
      {
        path: 'warnings',
        name: 'AdminWarnings',
        component: () => import('@/views/admin/WarningLedgerView.vue'),
        meta: { title: '预警总台账' },
      },
      {
        path: 'reports',
        name: 'AdminReports',
        component: () => import('@/views/admin/ReportManagementView.vue'),
        meta: { title: '报告统一管理' },
      },
      {
        path: 'audit-log',
        name: 'AdminAuditLog',
        component: () => import('@/views/admin/AuditLogView.vue'),
        meta: { title: '操作审计日志' },
      },
      {
        path: 'profile',
        name: 'AdminProfile',
        component: () => import('@/views/user/ProfileView.vue'),
        meta: { title: '个人中心' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const roleHomeMap: Record<string, string> = {
  user: '/user/contracts',
  legalReviewer: '/legal/todo',
  riskReviewer: '/risk/workbench',
  admin: '/admin/dashboard',
}

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('accessToken')
  const requiredRole = to.meta.role as string | undefined

  // 需要认证但无 token → 去登录
  if (to.meta.requiresAuth && !token) {
    next({ name: 'Login' })
    return
  }

  // 已登录但访问登录页 → 跳角色首页
  if (to.name === 'Login' && token) {
    const stored = localStorage.getItem('userInfo')
    let home = '/user/contracts'
    if (stored) {
      try {
        const u = JSON.parse(stored)
        home = roleHomeMap[u.role] || home
      } catch { /* ignore */ }
    }
    next(home)
    return
  }

  // 角色守卫：如果路由声明了 role，检查当前用户角色是否匹配
  if (requiredRole && token) {
    const stored = localStorage.getItem('userInfo')
    if (stored) {
      try {
        const u = JSON.parse(stored)
        if (u.role !== requiredRole) {
          // 角色不匹配 → 跳该用户自己的首页
          next(roleHomeMap[u.role] || '/user/contracts')
          return
        }
      } catch { /* ignore */ }
    }
  }

  next()
})

export default router
