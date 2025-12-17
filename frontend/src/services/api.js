/**
 * API服务
 */
import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('API错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 上传邮件
 */
export async function uploadEmail(file, emailText) {
  const formData = new FormData()
  if (file) {
    formData.append('email_file', file)
  }
  if (emailText) {
    formData.append('email_text', emailText)
  }
  
  return api.post('/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

/**
 * 执行检测
 */
export async function detectEmail(jobId) {
  return api.post(`/detect/${jobId}`)
}

/**
 * 获取检测结果
 */
export async function getDetectionResult(jobId) {
  return api.get(`/detect/${jobId}`)
}

/**
 * 获取所有检测历史
 */
export async function getAllResults(limit = 100, offset = 0) {
  return api.get('/results/', {
    params: { limit, offset }
  })
}

/**
 * 获取单个检测结果详情
 */
export async function getResult(jobId) {
  return api.get(`/results/${jobId}`)
}

export default api

