<template>
  <div class="risk-layout">
    <!-- 左侧边栏 -->
    <aside class="risk-sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <img src="/logo.png" alt="AILex" class="brand-logo-img" />
          <div class="brand-text">
            <span class="brand-title">AILEX</span>
            <span class="brand-subtitle">风险管控系统</span>
            <span class="brand-role">风控审核员</span>
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
        <div class="footer-user">
          <div class="footer-avatar">
            <svg viewBox="0 0 40 40" width="36" height="36"><circle cx="20" cy="20" r="20" fill="#1a6fc4"/><text x="20" y="25" text-anchor="middle" fill="#fff" font-size="14" font-weight="600">R</text></svg>
          </div>
          <div class="footer-user-info">
            <div class="footer-username">riskReviewer</div>
            <div class="footer-role">风控专员</div>
          </div>
        </div>
        <div class="footer-item" @click="$router.push('/risk/help')">
          <span class="nav-icon">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </span>
          <span class="nav-label">帮助中心</span>
        </div>
        <div class="footer-item" @click="handleLogout">
          <span class="nav-icon">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </span>
          <span class="nav-label">退出登录</span>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="risk-main">
      <!-- 顶部栏 -->
      <header class="risk-header">
        <div class="header-left">
          <img src="/logo.png" alt="AILex" class="header-logo" />
          <span class="header-title">AILEX 风险管控系统</span>
        </div>
        <div class="header-right">
          <span class="header-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
          </span>
          <span class="header-icon">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 015.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          </span>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="risk-content">
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
    path: '/risk/workbench',
    label: '复核工作台',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
  },
  {
    path: '/risk/warning',
    label: '预警处置',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
  },
  {
    path: '/risk/ledger',
    label: '审核台账',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
  },
  {
    path: '/risk/overdue',
    label: '逾期清单',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
  },
  {
    path: '/risk/report',
    label: '审核报告',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  },
  {
    path: '/risk/profile',
    label: '个人设置',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>',
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
.risk-layout {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
}

/* ========== 左侧边栏 ========== */
.risk-sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-brand {
  padding: 20px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo-img {
  height: 32px;
  width: auto;
}

.brand-text {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  color: #1a6fc4;
  font-style: italic;
  line-height: 1.2;
}

.brand-subtitle {
  font-size: 13px;
  font-weight: 600;
  color: #1a6fc4;
  line-height: 1.2;
}

.brand-role {
  font-size: 11px;
  color: #909399;
  line-height: 1.2;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.2s;
  color: #303133;
  font-size: 14px;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: #f5f7fa;
}

.nav-item.active {
  background: #ecf5ff;
  color: #1a6fc4;
  border-left-color: #1a6fc4;
  font-weight: 500;
}

.nav-icon {
  display: flex;
  align-items: center;
  color: inherit;
}

.nav-label {
  font-size: 14px;
}

.sidebar-footer {
  border-top: 1px solid #f0f0f0;
  padding: 12px 0;
}

.footer-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 8px;
}

.footer-avatar {
  flex-shrink: 0;
}

.footer-user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.footer-username {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.footer-role {
  font-size: 11px;
  color: #909399;
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
.risk-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.risk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-logo {
  height: 28px;
  width: auto;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: #1a6fc4;
  letter-spacing: 1px;
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

.risk-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
