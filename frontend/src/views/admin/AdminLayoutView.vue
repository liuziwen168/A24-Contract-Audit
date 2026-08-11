<template>
  <div class="admin-layout">
    <!-- 左侧边栏 -->
    <aside class="admin-sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg class="brand-icon" viewBox="0 0 32 32" width="32" height="32">
            <path d="M16 2L4 8v16l12 6 12-6V8L16 2z" fill="#1a6fc4" opacity="0.15"/>
            <path d="M16 6L8 10v12l8 4 8-4V10l-8-4z" fill="#1a6fc4" opacity="0.3"/>
            <text x="16" y="20" text-anchor="middle" fill="#1a6fc4" font-size="10" font-weight="700" font-style="italic">A</text>
          </svg>
          <div class="brand-text">
            <span class="brand-title">AILEX</span>
            <span class="brand-subtitle">风险管控系统</span>
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div
          v-for="item in menuItems"
          :key="item.path"
          class="nav-item"
          :class="{ active: isActive(item.path) }"
          @click="$router.push(item.path)"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          <span class="nav-label">{{ item.label }}</span>
        </div>
      </nav>

      <div class="sidebar-footer">
        <div class="footer-item" @click="$router.push('/admin/profile')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <span class="nav-label">个人中心</span>
        </div>
        <div class="footer-item" @click="$router.push('/admin/help')">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span class="nav-label">帮助中心</span>
        </div>
        <div class="footer-item" @click="handleLogout">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          <span class="nav-label">退出登录</span>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="admin-main">
      <!-- 顶部栏 -->
      <header class="admin-header">
        <div class="header-left">
          <span class="header-title">AILEX 风险管控系统</span>
        </div>
        <div class="header-right">
          <span class="header-icon">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
          </span>
          <span class="header-icon">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </span>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()

const menuItems = [
  {
    path: '/admin/dashboard',
    label: '运营看板',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
  },
  {
    path: '/admin/users',
    label: '用户管理',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>',
  },
  {
    path: '/admin/clauses',
    label: '标准条款管理',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
  },
  {
    path: '/admin/risk-rules',
    label: '风险规则管理',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/></svg>',
  },
  {
    path: '/admin/audit-records',
    label: '全量审核记录',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  },
  {
    path: '/admin/warnings',
    label: '预警总台账',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  },
  {
    path: '/admin/reports',
    label: '报告统一管理',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
  },
  {
    path: '/admin/audit-log',
    label: '操作审计日志',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
  },
]

function isActive(path: string) {
  return route.path.startsWith(path)
}

function handleLogout() {
  userStore.logout()
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  background: #f0eef8;
}

/* ========== 左侧边栏 ========== */
.admin-sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e8e6f0;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-brand {
  padding: 20px 16px;
  border-bottom: 1px solid #f0eef8;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-icon {
  flex-shrink: 0;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 18px;
  font-weight: 800;
  color: #1a1a2e;
  line-height: 1.2;
  letter-spacing: 1px;
}

.brand-subtitle {
  font-size: 11px;
  color: #909399;
  line-height: 1.2;
}

.sidebar-nav {
  flex: 1;
  padding: 8px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: #4a4a6a;
  font-size: 14px;
  border-left: 3px solid transparent;
  margin: 2px 0;
}

.nav-item:hover {
  background: #f5f3ff;
}

.nav-item.active {
  background: #e8f0fe;
  color: #1a6fc4;
  border-left-color: #1a6fc4;
  font-weight: 500;
}

.nav-icon {
  display: flex;
  align-items: center;
  color: inherit;
  flex-shrink: 0;
}

.nav-label {
  font-size: 14px;
}

.sidebar-footer {
  border-top: 1px solid #f0eef8;
  padding: 8px 0;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  color: #606266;
  font-size: 14px;
  transition: color 0.2s;
}

.footer-item:hover {
  color: #1a6fc4;
}

/* ========== 右侧主区域 ========== */
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e6f0;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a6fc4;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  color: #606266;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.header-icon:hover {
  color: #1a6fc4;
}

.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
