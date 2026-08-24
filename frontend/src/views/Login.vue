<template>
  <div class="login-container">
    <div class="login-box">
      <h1>食尚订AI客服</h1>

      <div class="tabs">
        <button :class="{ active: isLogin }" @click="isLogin = true">登录</button>
        <button :class="{ active: !isLogin }" @click="isLogin = false">注册</button>
      </div>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>用户名</label>
          <input v-model="username" type="text" required />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label>邮箱</label>
          <input v-model="email" type="email" required />
        </div>

        <div class="form-group">
          <label>密码</label>
          <input v-model="password" type="password" required />
        </div>

        <button type="submit" class="submit-btn">
          {{ isLogin ? '登录' : '注册' }}
        </button>

        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'
import authApi from '@/api/auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()

    const isLogin = ref(true)
    const username = ref('')
    const email = ref('')
    const password = ref('')
    const error = ref('')

    const handleSubmit = async () => {
      try {
        error.value = ''

        if (isLogin.value) {
          const response = await authApi.login(username.value, password.value)
          userStore.setToken(response.access_token)
          userStore.setUser(response.user)
          router.push('/home')
        } else {
          await authApi.register(username.value, email.value, password.value)
          const response = await authApi.login(username.value, password.value)
          userStore.setToken(response.access_token)
          userStore.setUser(response.user)
          router.push('/home')
        }
      } catch (err) {
        error.value = err.response?.data?.detail || '发生错误'
      }
    }

    return {
      isLogin,
      username,
      email,
      password,
      error,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 400px;
}

h1 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: #333;
  font-size: 1.5rem;
}

.tabs {
  display: flex;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid #eee;
}

.tabs button {
  flex: 1;
  padding: 0.75rem;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 1rem;
  color: #666;
  transition: all 0.3s;
}

.tabs button.active {
  color: #667eea;
  border-bottom: 2px solid #667eea;
  margin-bottom: -2px;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #333;
  font-weight: 500;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 1rem;
}

input:focus {
  outline: none;
  border-color: #667eea;
}

.submit-btn {
  width: 100%;
  padding: 0.75rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 5px;
  font-size: 1rem;
  cursor: pointer;
  transition: transform 0.2s;
}

.submit-btn:hover {
  transform: translateY(-2px);
}

.error {
  color: #e74c3c;
  margin-top: 1rem;
  text-align: center;
}
</style>