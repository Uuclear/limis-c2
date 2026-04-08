import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'
import { setToken, setRefreshToken, clearTokens, getToken } from '@/utils/auth'

export const useUserStore = defineStore('user', () => {
  const userInfo = ref(null)
  const permissions = ref([])
  const roles = ref([])

  async function login(username, password) {
    const data = await loginApi({ username, password })
    setToken(data.access_token)
    setRefreshToken(data.refresh_token)
    await fetchUserInfo()
  }

  async function fetchUserInfo() {
    const data = await getMe()
    userInfo.value = data
    roles.value = data.roles.map((r) => r.name)
    permissions.value = data.permissions
  }

  function logout() {
    userInfo.value = null
    permissions.value = []
    roles.value = []
    clearTokens()
  }

  function isLoggedIn() {
    return !!getToken()
  }

  function hasPermission(perm) {
    if (roles.value.includes('admin')) return true
    return permissions.value.includes(perm)
  }

  function hasRole(...requiredRoles) {
    return requiredRoles.some((r) => roles.value.includes(r))
  }

  return {
    userInfo, permissions, roles,
    login, fetchUserInfo, logout, isLoggedIn, hasPermission, hasRole,
  }
})
