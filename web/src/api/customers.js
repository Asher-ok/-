import api from './index'

export const getCustomers = (params) => {
  return api.get('/houtai/customers', { params }).then((res) => {
    if (Array.isArray(res)) return res
    return res?.items || res?.data || res?.rows || []
  })
}

export const getCustomer = (id) => {
  return api.get(`/houtai/customers/${id}`)
}

export const createCustomer = (data) => {
  return api.post('/houtai/customers', data)
}

export const updateCustomer = (id, data) => {
  return api.put(`/houtai/customers/${id}`, data)
}

export const deleteCustomer = (id) => {
  return api.delete(`/houtai/customers/${id}`)
}

export const uploadCustomerAttachment = (customerId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/houtai/customers/${customerId}/attachments`, formData, {
    // 不设置 Content-Type，让请求拦截器自动处理（浏览器会自动设置 multipart/form-data 和 boundary）
    timeout: 80000 // 文件上传使用180秒超时（VPN环境下可能需要更长时间）
  })
}

export const getCustomerAttachment = (customerId, attachmentIndex) => {
  return api.get(
    `/houtai/customers/${customerId}/attachments/${attachmentIndex}/download`,
    { responseType: 'blob' }
  )
}

export const uploadNdisPlan = (customerId, file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post(`/houtai/customers/${customerId}/ndis-plan`, formData, {
    timeout: 80000
  })
}

export const downloadNdisPlan = (customerId) => {
  return api.get(
    `/houtai/customers/${customerId}/ndis-plan/download`,
    { responseType: 'blob' }
  )
}

export const approveArchive = (customerId) => {
  return api.post(`/houtai/customers/${customerId}/archive/approve`)
}

export const startArchiveReview = (customerId) => {
  return api.post(`/houtai/customers/${customerId}/archive/start-review`)
}

// 上传客户合同（与员工文档上传一致）：/documents/upload
// 创建或更新 service_agreement 草稿，支持 pdf/doc/docx
export const uploadCustomerContract = (customerId, { file = null, templateId = null } = {}) => {
  const formData = new FormData()
  formData.append('document_type', 'service_agreement')
  if (templateId) formData.append('template_id', templateId)
  if (file) formData.append('file', file)
  return api
    .post(`/houtai/customers/${customerId}/documents/upload`, formData, { timeout: 120000 })
    .catch(async (err) => {
      // 兼容保留的专用接口（仅PDF）
      if (err?.response?.status === 404) {
        if (!file) throw err
        const fallbackForm = new FormData()
        fallbackForm.append('file', file)
        return api.post(`/houtai/customers/${customerId}/contract/upload`, fallbackForm, { timeout: 120000 })
      }
      throw err
    })
}

// 发送客户合同签署链接到客户邮箱
export const sendCustomerContract = (customerId, email, language = null) => {
  const params = {}
  if (language) params.language = language
  const data = { customer_email: email }
  if (language) data.language = language
  return api.post(`/houtai/customers/${customerId}/contract/send`, data, { params })
}

// 查看客户已签署合同（PDF）
export const viewCustomerContract = (customerId) => {
  return api.get(`/houtai/customers/${customerId}/contract/view`, { params: { _t: Date.now() }, responseType: 'blob' })
}

// 审核拒绝
export const rejectArchive = (customerId) => {
  return api.post(`/houtai/customers/${customerId}/archive/reject`)
}

// 删除客户合同
export const deleteCustomerContract = (customerId) => {
  return api.delete(`/houtai/customers/${customerId}/contract`)
}

export const getInvoiceServiceLevels = async () => {
  const urls = [
    '/houtai/invoices/service-level1',
    '/houtai/invoices/service-levels',
    '/houtai/invoices/service-level-catalog',
    '/houtai/invoices/service-catalog',
    '/houtai/invoice-service-levels',
    '/houtai/invoice-service-catalog'
  ]
  let lastErr = null
  for (const url of urls) {
    try {
      return await api.get(url)
    } catch (err) {
      lastErr = err
      if (err?.response?.status === 404) continue
      throw err
    }
  }
  throw lastErr
}
