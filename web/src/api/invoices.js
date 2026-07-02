import api from './index'

export const getInvoices = (customerId, status) => {
  const params = {}
  if (customerId) params.customer_id = customerId
  if (status) params.status = status
  return api.get('/houtai/invoices', { params })
}

export const getTasksForInvoice = (params = {}) => {
  return api.get('/houtai/invoices/tasks', { params })
}

export const getInvoiceTaskDetail = (taskId) => {
  return api.get(`/houtai/invoices/tasks/${taskId}`)
}

export const generateInvoiceForTask = (taskId, data = {}) => {
  return api.post(`/houtai/invoices/tasks/${taskId}/generate`, data)
}

export const getInvoice = (id) => {
  return api.get(`/houtai/invoices/${id}`)
}

export const generateInvoice = (data) => {
  return api.post('/houtai/invoices/generate', data)
}

export const updateInvoice = (id, data) => {
  return api.put(`/houtai/invoices/${id}`, data)
}

export const previewInvoice = (id) => {
  return api.get(`/houtai/invoices/${id}/preview`, {
    params: { _t: Date.now() },
    responseType: 'blob'
  })
}

export const sendInvoice = (id, language = null) => {
  const params = {}
  if (language) params.language = language
  return api.post(`/houtai/invoices/${id}/send`, null, { params })
}

// 已废弃：PDF生成功能 - 现在统一使用Excel格式
// export const generateInvoicePdf = (id) => {
//   return api.post(`/api/houtai/invoices/${id}/generate-pdf`)
// }

export const updateInvoiceStatus = (id, status) => {
  return api.put(`/houtai/invoices/${id}/status?new_status=${status}`)
}

export const deleteInvoice = (id) => {
  return api.delete(`/houtai/invoices/${id}`)
}

export const getServiceLevel1 = (params = {}) => {
  return api.get('/houtai/invoices/service-level1', { params })
}

export const getServiceLevel2 = (level1Id, params = {}) => {
  return api.get('/houtai/invoices/service-level2', { params: { level1_id: level1Id, ...params } })
}

export const getServiceLevel3 = (params = {}) => {
  return api.get('/houtai/invoices/service-level3', { params })
}

export const getServiceCodes = (level3Id, params = {}) => {
  return api.get('/houtai/invoices/service-codes', { params: { level3_id: level3Id, ...params } })
}

export const batchSendUnsentInvoices = (customerId = null, language = null) => {
  const data = {}
  if (customerId) data.customer_id = customerId
  if (language) data.language = language
  return api.post('/houtai/invoices/batch/send-unsent', data)
}

export const batchGenerateUninvoiced = (payload = {}) => {
  return api.post('/houtai/invoices/batch/generate-uninvoiced', payload)
}

export const getUninvoicedTasksDetail = (params = {}) => {
  return api.get('/houtai/invoices/tasks-uninvoiced-detail', { params }).catch((err) => {
    if (err?.response?.status !== 404) throw err
    return api.get('/houtai/invoices/batch/tasks-uninvoiced-detail', { params }).catch((err2) => {
      if (err2?.response?.status !== 404) throw err2
      return api.get('/houtai/invoices/tasks/detail', { params })
    })
  })
}

export const batchGenerateByTask = (payload = {}) => {
  return api.post('/houtai/invoices/tasks/generate-all', payload).catch((err) => {
    if (err?.response?.status !== 404) throw err
    return api.post('/houtai/invoices/generate-all', payload).catch((err2) => {
      if (err2?.response?.status !== 404) throw err2
      return api.post('/houtai/invoices/batch/generate-by-task', payload)
    })
  })
}

export const createServiceLevel1 = (data) => {
  return api.post('/houtai/invoices/service-level1', data)
}

export const updateServiceLevel1 = (level1Id, data) => {
  return api.put(`/houtai/invoices/service-level1/${level1Id}`, data)
}

export const deleteServiceLevel1 = (level1Id) => {
  return api.delete(`/houtai/invoices/service-level1/${level1Id}`)
}

export const createServiceLevel2 = (data) => {
  return api.post('/houtai/invoices/service-level2', data)
}

export const updateServiceLevel2 = (level2Id, data) => {
  return api.put(`/houtai/invoices/service-level2/${level2Id}`, data)
}

export const deleteServiceLevel2 = (level2Id) => {
  return api.delete(`/houtai/invoices/service-level2/${level2Id}`)
}

export const createServiceLevel3 = (data) => {
  return api.post('/houtai/invoices/service-level3', data)
}

export const updateServiceLevel3 = (level3Id, data) => {
  return api.put(`/houtai/invoices/service-level3/${level3Id}`, data)
}

export const deleteServiceLevel3 = (level3Id) => {
  return api.delete(`/houtai/invoices/service-level3/${level3Id}`)
}

export const createServiceCode = (data) => {
  return api.post('/houtai/invoices/service-codes', data)
}

export const updateServiceCode = (codeId, data) => {
  return api.put(`/houtai/invoices/service-codes/${codeId}`, data)
}

export const deleteServiceCode = (codeId) => {
  return api.delete(`/houtai/invoices/service-codes/${codeId}`)
}
