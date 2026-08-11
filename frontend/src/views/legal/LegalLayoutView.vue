<template>
  <div class="legal-layout">
    <!-- 左侧边栏 -->
    <aside class="legal-sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <img src="/logo.png" alt="AILex" class="brand-logo-img" />
          <div class="brand-text">
            <span class="brand-title">AILex</span>
            <span class="brand-role">法务审计员角色</span>
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
        <div class="footer-item" @click="$router.push('/legal/help')">
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
    <div class="legal-main">
      <!-- 顶部栏 -->
      <header class="legal-header">
        <div class="header-search">
          <svg class="search-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input type="text" placeholder="搜索合同、风险模式..." class="search-input" />
        </div>
        <div class="header-right">
          <div class="header-icons">
            <span class="header-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
            </span>
            <span class="header-icon">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z"/></svg>
            </span>
          </div>
          <div class="header-divider"></div>
          <div class="user-profile">
            <div class="user-info-text">
              <span class="user-name">张律师</span>
              <span class="user-role">法务审计员</span>
            </div>
            <div class="user-avatar">
              <svg viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="20" r="20" fill="#1a6fc4"/><text x="20" y="25" text-anchor="middle" fill="#fff" font-size="16" font-weight="600">张</text></svg>
            </div>
          </div>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="legal-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const menuItems = [
  {
    path: '/legal/todo',
    label: '法务待办列表',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
  },
  {
    path: '/legal/compliance',
    label: '合规审计',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
  },
  {
    path: '/legal/cases',
    label: '案件管理',
    icon: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v16"/></svg>',
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
.legal-layout {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
}

/* ========== 左侧边栏 ========== */
.legal-sidebar {
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
.legal-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.legal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  padding: 0 24px;
  flex-shrink: 0;
}

.header-search {
  display: flex;
  align-items: center;
  background: #f5f7fa;
  border-radius: 6px;
  padding: 8px 14px;
  width: 320px;
  gap: 8px;
}

.search-icon {
  color: #909399;
  flex-shrink: 0;
}

.search-input {
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: #303133;
  width: 100%;
}

.search-input::placeholder {
  color: #c0c4cc;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icons {
  display: flex;
  align-items: center;
  gap: 12px;
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

.header-divider {
  width: 1px;
  height: 24px;
  background: #e8e8e8;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.user-info-text {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.3;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
}

.user-role {
  font-size: 12px;
  color: #909399;
}

.user-avatar {
  border-radius: 50%;
  overflow: hidden;
}

.legal-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
