import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 读取当前账号的专属 token 键
function currentToken() {
  const name = localStorage.getItem('current_user')
  return name ? localStorage.getItem(`token_${name}`) : null
}

// 请求拦截器添加令牌
api.interceptors.request.use(config => {
  const token = currentToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器处理错误
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      const name = localStorage.getItem('current_user')
      if (name) localStorage.removeItem(`token_${name}`)
      localStorage.removeItem('current_user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default {
  async register(username, email, password) {
    const response = await api.post('/auth/register', { username, email, password })
    return response.data
  },

  async login(username, password) {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await api.post('/auth/login', params, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data
  },

  async getMe() {
    const response = await api.get('/auth/me')
    return response.data
  }
}