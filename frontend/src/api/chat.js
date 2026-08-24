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

  async sendMessage(conversationId, message) {
    const response = await api.post('/chat/message', {
      conversation_id: conversationId,
      message
    })
    return response.data
  },

  async streamMessage(conversationId, message, onChunk) {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message
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