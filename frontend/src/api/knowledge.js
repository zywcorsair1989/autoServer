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
  async getCollections() {
    // 后端路由是 GET /knowledge（返回 {collections: [...], total}）
    const response = await api.get('/knowledge')
    return response.data
  },

  async createCollection(name, description) {
    const response = await api.post('/knowledge/collections', { name, description })
    return response.data
  },

  async deleteCollection(id) {
    const response = await api.delete(`/knowledge/collections/${id}`)
    return response.data
  },

  async uploadDocument(collectionId, file) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('collection_id', collectionId)

    const token = localStorage.getItem('token')
    const response = await axios.post('/api/v1/documents/upload', formData, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  },

  async getDocuments(collectionId = null) {
    const url = collectionId
      ? `/documents/?collection_id=${collectionId}`
      : '/documents/'
    const response = await api.get(url)
    return response.data
  },

  async deleteDocument(id) {
    const response = await api.delete(`/documents/${id}`)
    return response.data
  },

  async query(collectionId, query, topK = 5) {
    const response = await api.post('/knowledge/query', {
      collection_id: collectionId,
      query,
      top_k: topK
    })
    return response.data
  }
}