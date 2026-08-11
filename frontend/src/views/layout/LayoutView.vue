<template>
  <div class="app-layout">
    <header class="app-header">
      <div class="header-left">
        <div class="logo-area">
          <img class="logo-icon" src="/logo.png" alt="AILex" />
          <span class="logo-text">合同智能审核系统</span>
        </div>
      </div>
      <div class="header-right">
        <div class="header-icons">
          <el-badge :value="3" :max="99">
            <el-icon class="header-icon"><Bell /></el-icon>
          </el-badge>
          <el-icon class="header-icon"><QuestionFilled /></el-icon>
        </div>
        <div class="header-divider"></div>
        <div class="user-info">
          <span class="user-name">{{ userStore.userInfo?.username || '张经理' }}</span>
          <span class="user-role-label">{{ userStore.roleLabel || '合同经办人' }}</span>
        </div>
        <el-button class="logout-btn" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          退出
        </el-button>
      </div>
    </header>
    <div class="app-body">
      <aside class="app-sidebar">
        <el-menu :default-active="activeMenu" class="sidebar-menu" router>
          <el-menu-item index="/user/contracts">
            <el-icon><Document /></el-icon><span>合同管理</span>
          </el-menu-item>
          <el-menu-item index="/user/reviews">
            <el-icon><List /></el-icon><span>我的审核任务</span>
          </el-menu-item>
          <el-menu-item index="/user/warnings">
            <el-icon><Warning /></el-icon><span>风险预警中心</span>
          </el-menu-item>
          <el-menu-item index="/user/reports">
            <el-icon><Download /></el-icon><span>报告下载中心</span>
          </el-menu-item>
          <el-menu-item index="/user/profile">
            <el-icon><User /></el-icon><span>个人中心</span>
          </el-menu-item>
          <el-menu-item index="/user/ai-bot" class="ai-bot-item">
            <el-icon><Monitor /></el-icon><span>智能AI机器人</span>
          </el-menu-item>
        </el-menu>
        <div class="sidebar-footer">
          <div class="footer-avatar"><el-avatar :size="36" /></div>
          <div class="footer-info">
            <div class="footer-name">合同处理员</div>
            <div class="footer-role">高级权限</div>
          </div>
        </div>
      </aside>
      <main class="app-main"><router-view /></main>
    </div>
  </div>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Bell, QuestionFilled, SwitchButton, Document, List, Warning, Download, User, Monitor } from '@element-plus/icons-vue'
const route = useRoute()
const userStore = useUserStore()
const activeMenu = computed(() => route.path)
function handleLogout() { userStore.logout() }
</script>
<style scoped>
.app-layout { display: flex; flex-direction: column; height: 100vh; background: #f0f2f5; }
.app-header { display: flex; align-items: center; justify-content: space-between; height: 56px; background: #fff; border-bottom: 1px solid #e8e8e8; padding: 0 24px; flex-shrink: 0; z-index: 100; }
.header-left { display: flex; align-items: center; }
.logo-area { display: flex; align-items: center; gap: 10px; }
.logo-icon { height: 32px; width: auto; }
.logo-text { font-size: 18px; font-weight: 600; color: #1a6fc4; letter-spacing: 1px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.header-icons { display: flex; align-items: center; gap: 12px; }
.header-icon { font-size: 20px; color: #606266; cursor: pointer; }
.header-icon:hover { color: #1a6fc4; }
.header-divider { width: 1px; height: 24px; background: #e8e8e8; }
.user-info { display: flex; flex-direction: column; align-items: flex-end; line-height: 1.3; }
.user-name { font-size: 14px; font-weight: 500; color: #303133; }
.user-role-label { font-size: 12px; color: #909399; }
.logout-btn { display: flex; align-items: center; gap: 4px; font-size: 14px; color: #606266; border: 1px solid #dcdfe6; background: #fff; }
.logout-btn:hover { color: #1a6fc4; border-color: #1a6fc4; }
.app-body { display: flex; flex: 1; overflow: hidden; }
.app-sidebar { width: 200px; background: #fff; border-right: 1px solid #e8e8e8; display: flex; flex-direction: column; flex-shrink: 0; }
.sidebar-menu { border-right: none; flex: 1; }
.sidebar-menu :deep(.el-menu-item) { height: 48px; line-height: 48px; font-size: 14px; color: #303133; }
.sidebar-menu :deep(.el-menu-item:hover) { background: #f5f7fa; }
.sidebar-menu :deep(.el-menu-item.is-active) { background: #1a6fc4; color: #fff; }
.sidebar-menu :deep(.el-menu-item.is-active .el-icon) { color: #fff; }
.ai-bot-item { background: #f0f4ff; }
.ai-bot-item :deep(.el-icon) { color: #1a6fc4; }
.sidebar-footer { display: flex; align-items: center; gap: 10px; padding: 16px; border-top: 1px solid #e8e8e8; }
.footer-avatar :deep(.el-avatar) { background: #c0c4cc; }
.footer-name { font-size: 13px; font-weight: 500; color: #303133; }
.footer-role { font-size: 12px; color: #909399; }
.app-main { flex: 1; overflow-y: auto; padding: 20px 24px; }
</style>
