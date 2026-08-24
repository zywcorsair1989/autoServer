<template>
  <div class="home-container">
    <nav class="navbar">
      <h2>RAG Q&A System</h2>
      <div class="nav-links">
        <router-link to="/chat">Chat</router-link>
        <router-link to="/knowledge">Knowledge</router-link>
        <button @click="logout" class="logout-btn">Logout</button>
      </div>
    </nav>

    <div class="welcome-section">
      <h1>Welcome to RAG Intelligent Q&A System</h1>
      <p>A powerful AI-powered question answering system with knowledge base management</p>

      <div class="feature-cards">
        <div class="card">
          <h3>Smart Chat</h3>
          <p>Have intelligent conversations with AI powered by your knowledge base</p>
          <router-link to="/chat" class="card-link">Start Chatting</router-link>
        </div>

        <div class="card">
          <h3>Knowledge Base</h3>
          <p>Upload and manage documents to build your knowledge base</p>
          <router-link to="/knowledge" class="card-link">Manage Knowledge</router-link>
        </div>

        <div class="card">
          <h3>RAG Technology</h3>
          <p>Advanced retrieval-augmented generation for accurate answers</p>
          <router-link to="/chat" class="card-link">Try It Now</router-link>
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