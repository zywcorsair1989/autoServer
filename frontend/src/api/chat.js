import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器处理认证失效
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default {
  async getConversations(skip = 0, limit = 20) {
    const response = await api.get('/chat/conversations', { params: { skip, limit } })
    return response.data
  },

  async createConversation(title) {
    const response = await api.post('/chat/conversations', { title })
    return response.data
  },

  async getConversation(id) {
    const response = await api.get(`/chat/conversations/${id}`)
    return response.data
  },

  async deleteConversation(id) {
    const response = await api.delete(`/chat/conversations/${id}`)
    return response.data
  },

  async getKnowledgeCollections(skip = 0, limit = 20) {
    const response = await api.get('/knowledge', { params: { skip, limit } })
    return response.data
  },

  async sendMessage(conversationId, message) {
    // 首先获取用户的知识库集
    const collectionsResponse = await api.get('/knowledge')
    const collections = collectionsResponse.data?.collections || []

    // 查找 "食尚订产品文档" 集合
    const shishangdingCollection = collections.find(col => col.name === '食尚订产品文档')

    const response = await api.post('/chat', {
      conversation_id: conversationId,
      message,
      use_knowledge: !!shishangdingCollection,  // 如果找到知识库集则启用 RAG
      collection_id: shishangdingCollection?.id  // 使用当前用户的知识库集 ID
    })
    return response.data
  },

  async streamMessage(conversationId, message, onChunk) {
    // 首先获取用户的知识库集
    const token = localStorage.getItem('token')
    const collectionsResponse = await fetch('/api/v1/knowledge', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    })
    const collections = await collectionsResponse.json()

    // 查找 "食尚订产品文档" 集合
    const shishangdingCollection = collections.collections?.find(col => col.name === '食尚订产品文档')

    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message,
        use_knowledge: !!shishangdingCollection,  // 如果找到知识库集则启用 RAG
        collection_id: shishangdingCollection?.id  // 使用当前用户的知识库集 ID
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            return
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              onChunk(parsed.content)
            }
          } catch (e) {
            // Ignore parse errors
          }
        }
      }
    }
  }
}