import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  // 当前登录账号名，用于定位专属 token 键
  const username = ref(localStorage.getItem('current_user') || null)
  const token = ref(username.value ? localStorage.getItem(tokenKey(username.value)) : null)

  // 每个账号使用独立的 token 键，避免同一浏览器多账号互相覆盖
  function tokenKey(name) {
    return `token_${name}`
  }

  function setUser(userData) {
    user.value = userData
  }

  function setToken(tokenValue) {
    token.value = tokenValue
    if (username.value) {
      localStorage.setItem(tokenKey(username.value), tokenValue)
    }
  }

  // 登录时绑定账号名，并直接载入该账号已有的 token（若存在）
  function setActiveUser(name) {
    username.value = name
    localStorage.setItem('current_user', name)
    token.value = localStorage.getItem(tokenKey(name)) || null
  }

  function logout() {
    const name = username.value
    user.value = null
    token.value = null
    if (name) {
      localStorage.removeItem(tokenKey(name))
    }
    localStorage.removeItem('current_user')
  }

  return {
    user,
    token,
    username,
    setUser,
    setToken,
    setActiveUser,
    logout
  }
})