import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// Request interceptor to add token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
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