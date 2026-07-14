 import { defineStore } from 'pinia'
 import { ref, computed } from 'vue'
 import type { User, Role } from '@/types'
 import { login as loginApi, getCurrentUser } from '@/api/auth'

 export const useAuthStore = defineStore('auth', () => {
   const user = ref<User | null>(null)
   const token = ref<string | null>(localStorage.getItem('accessToken'))

   const isLoggedIn = computed(() => !!token.value)
   const role = computed<Role | null>(() => user.value?.role ?? null)
   const username = computed(() => user.value?.username ?? '')
   const userId = computed(() => user.value?.id ?? -1)

   const isAdmin = computed(() => role.value === 'admin')
   const isLegalReviewer = computed(() => role.value === 'legalReviewer')
   const isRiskReviewer = computed(() => role.value === 'riskReviewer')
   const isRegularUser = computed(() => role.value === 'user')
   const isReviewer = computed(() => isLegalReviewer.value || isRiskReviewer.value)

   async function login(username: string, password: string) {
     const res = await loginApi({ username, password })
     const data = res.data
     token.value = data.accessToken
     user.value = data.user
     localStorage.setItem('accessToken', data.accessToken)
     return data
   }

   async function fetchCurrentUser() {
     try {
       const res = await getCurrentUser()
       user.value = res.data
     } catch {
       clearUser()
     }
   }

   function clearUser() {
     user.value = null
     token.value = null
     localStorage.removeItem('accessToken')
   }

   function logout() {
     clearUser()
   }

   return {
     user, token, isLoggedIn, role, username, userId,
     isAdmin, isLegalReviewer, isRiskReviewer, isRegularUser, isReviewer,
     login, fetchCurrentUser, clearUser, logout,
   }
 })
