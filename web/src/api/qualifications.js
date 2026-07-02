import api from './index'

export const getExpiringQualifications = (days = 30) => {
  return api.get('/houtai/qualifications/expiring', { params: { days } })
}

export const getExpiredQualifications = () => {
  return api.get('/houtai/qualifications/expired')
}

export const uploadQualification = (formData) => {
  return api.post('/houtai/qualifications/upload', formData, {
    // 不设置 Content-Type，让请求拦截器自动处理（浏览器会自动设置 multipart/form-data 和 boundary）
    timeout: 120000 // 文件上传使用120秒超时
  })
}

export const getAllQualifications = (params) => {
  return api.get('/houtai/qualifications', { params })
}

export const updateQualification = (qualificationId, data) => {
  return api.put(`/houtai/qualifications/${qualificationId}`, data)
}

export const deleteQualification = (qualificationId) => {
  return api.delete(`/houtai/qualifications/${qualificationId}`)
}

export const getQualificationCertificate = (qualificationId) => {
  return api.get(`/houtai/qualifications/${qualificationId}/certificate`, {
    responseType: 'blob'
  })
}

export const getExpiringSetting = () => {
  return api.get('/houtai/qualifications/expiring-settings')
}

export const updateExpiringSetting = (days) => {
  return api.put('/houtai/qualifications/expiring-settings', { days })
}
