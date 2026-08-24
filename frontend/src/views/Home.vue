<template>
  <div class="home-container">
    <nav class="navbar">
      <h2>食尚订AI客服</h2>
      <div class="nav-links">
        <router-link to="/chat">聊天</router-link>
        <router-link to="/knowledge">知识库</router-link>
        <button @click="logout" class="logout-btn">退出登录</button>
      </div>
    </nav>

    <div class="welcome-section">
      <h1>欢迎使用食尚订AI客服</h1>
      <p>一个强大的AI驱动的问答系统，具备知识库管理功能</p>

      <div class="feature-cards">
        <div class="card">
          <h3>智能聊天</h3>
          <p>与AI进行智能对话，由您的知识库提供支持</p>
          <router-link to="/chat" class="card-link">开始聊天</router-link>
        </div>

        <div class="card">
          <h3>知识库</h3>
          <p>上传和管理文档以构建您的知识库</p>
          <router-link to="/knowledge" class="card-link">管理知识库</router-link>
        </div>

        <div class="card">
          <h3>RAG技术</h3>
          <p>先进的检索增强生成技术，提供准确的答案</p>
          <router-link to="/chat" class="card-link">立即体验</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store'

export default {
  name: 'Home',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()

    const logout = () => {
      userStore.logout()
      router.push('/login')
    }

    return {
      logout
    }
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.navbar h2 {
  color: #667eea;
  margin: 0;
}

.nav-links {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.nav-links a {
  text-decoration: none;
  color: #666;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  transition: all 0.3s;
}

.nav-links a:hover {
  background: #f0f0f0;
  color: #667eea;
}

.logout-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  cursor: pointer;
  transition: background 0.3s;
}

.logout-btn:hover {
  background: #c0392b;
}

.welcome-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 4rem 2rem;
  text-align: center;
}

.welcome-section h1 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 1rem;
}

.welcome-section p {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 3rem;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.card {
  background: white;
  padding: 2rem;
  border-radius: 10px;
  box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.card:hover {
  transform: translateY(-5px);
}

.card h3 {
  font-size: 1.5rem;
  margin-bottom: 1rem;
  color: #333;
}

.card p {
  color: #666;
  margin-bottom: 1.5rem;
}

.card-link {
  display: inline-block;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 5px;
  transition: transform 0.2s;
}

.card-link:hover {
  transform: translateY(-2px);
}
</style>