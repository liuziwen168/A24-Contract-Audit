import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo, Role } from '@/types'
import { loginApi, getCurrentUserApi, logoutApi } from '@/api/auth'
import { ElMessage } from 'element-plus'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref<UserInfo | null>(null)
  const accessToken = ref<string>(localStorage.getItem('accessToken') || '')

  // 角色默认首页
  const roleHomeMap: Record<Role, string> = {
    user: '/user/contracts',
    legalReviewer: '/legal/todo',
    riskReviewer: '/risk/workbench',
    admin: '/admin/dashboard',
  }

  // 角色中文名
  const roleLabelMap: Record<Role, string> = {
    user: '普通用户',
    legalReviewer: '法务审核员',
    riskReviewer: '风控审核员',
    admin: '管理员',
  }

  const roleLabel = computed(() => {
    if (!userInfo.value) return ''
    return roleLabelMap[userInfo.value.role] || ''
  })

  const isLoggedIn = computed(() => !!accessToken.value && !!userInfo.value)

  // 初始化用户信息（从 localStorage 恢复）
  function initFromStorage() {
    const stored = localStorage.getItem('userInfo')
    const token = localStorage.getItem('accessToken')
    if (stored && token) {
      try {
        userInfo.value = JSON.parse(stored)
        accessToken.value = token
      } catch {
        clearAuth()
      }
    }
  }

  // 获取当前角色的首页路径
  function getHomePath(): string {
    if (userInfo.value) {
      return roleHomeMap[userInfo.value.role] || '/user/contracts'
    }
    // fallback：从 localStorage 解析
    const stored = localStorage.getItem('userInfo')
    if (stored) {
      try {
        const u = JSON.parse(stored) as UserInfo
        return roleHomeMap[u.role] || '/user/contracts'
      } catch { /* ignore */ }
    }
    return '/user/contracts'
  }

  // 登录
  async function login(username: string, password: string) {
    const res = await loginApi({ username, password })
    const data = res.data
    accessToken.value = data.accessToken
    userInfo.value = data.user
    localStorage.setItem('accessToken', data.accessToken)
    localStorage.setItem('userInfo', JSON.stringify(data.user))
    ElMessage.success('登录成功')
    router.push(getHomePath())
  }

  // 刷新用户信息
  async function fetchUserInfo() {
    try {
      const res = await getCurrentUserApi()
      userInfo.value = res.data
      localStorage.setItem('userInfo', JSON.stringify(res.data))
    } catch {
      clearAuth()
    }
  }

  // 退出登录
  function logout() {
    logoutApi()
    userInfo.value = null
    accessToken.value = ''
    router.push('/login')
    ElMessage.success('已退出登录')
  }

  function clearAuth() {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('userInfo')
    userInfo.value = null
    accessToken.value = ''
  }

  return {
    userInfo,
    accessToken,
    roleLabel,
    isLoggedIn,
    initFromStorage,
    login,
    fetchUserInfo,
    logout,
  }
})
