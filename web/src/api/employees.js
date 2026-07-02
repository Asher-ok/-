import api from './index'

export const getEmployees = () => {
  return api.get('/houtai/employees')
}

export const getEmployee = (id) => {
  return api.get(`/houtai/employees/${id}`)
}

export const createEmployee = (data) => {
  return api.post('/houtai/employees', data)
}

export const updateEmployee = (id, data) => {
  return api.put(`/houtai/employees/${id}`, data)
}

export const updateEmployeeAccountStatus = (id, accountStatus) => {
  return api.put(`/houtai/employees/${id}/account-status`, {
    account_status: accountStatus
  })
}

export const deleteEmployee = (id) => {
  return api.delete(`/houtai/employees/${id}`)
}

export const addQualification = (employeeId, data) => {
  return api.post(`/houtai/employees/${employeeId}/qualifications`, data)
}

export const deleteQualification = (employeeId, qualificationId) => {
  return api.delete(`/houtai/employees/${employeeId}/qualifications/${qualificationId}`)
}

export const addTrainingRecord = (employeeId, data) => {
  return api.post(`/houtai/employees/${employeeId}/training-records`, data)
}

export const getTrainingRecords = (employeeId) => {
  return api.get(`/houtai/employees/${employeeId}/training-records`)
}

export const updateTrainingRecord = (employeeId, recordId, data) => {
  return api.put(`/houtai/employees/${employeeId}/training-records/${recordId}`, data)
}

export const uploadTrainingRecord = (employeeId, formData) => {
  return api.post(`/houtai/employees/${employeeId}/training-records/upload`, formData, {
    // 不设置 Content-Type，让请求拦截器自动处理（浏览器会自动设置 multipart/form-data 和 boundary）
    timeout: 180000 // 文件上传使用180秒超时（VPN环境下可能需要更长时间）
  })
}

export const updateTrainingRecordWithFile = (employeeId, recordId, formData) => {
  return api.put(`/houtai/employees/${employeeId}/training-records/${recordId}/upload`, formData, {
    // 不设置 Content-Type，让请求拦截器自动处理（浏览器会自动设置 multipart/form-data 和 boundary）
    timeout: 180000 // 文件上传使用180秒超时（VPN环境下可能需要更长时间）
  })
}

export const deleteTrainingRecord = (employeeId, recordId) => {
  return api.delete(`/houtai/employees/${employeeId}/training-records/${recordId}`)
}

export const approveTrainingRecord = (employeeId, recordId) => {
  return api.put(`/houtai/employees/${employeeId}/training-records/${recordId}/approve`)
}

export const rejectTrainingRecord = (employeeId, recordId) => {
  return api.put(`/houtai/employees/${employeeId}/training-records/${recordId}/reject`)
}

// 培训记录到期提醒相关API
export const getExpiringTrainingRecords = (advanceDays) => {
  const params = advanceDays ? { advance_days: advanceDays } : {}
  return api.get('/houtai/employees/training-records/expiring', { params })
}

export const getExpiredTrainingRecords = () => {
  return api.get('/houtai/employees/training-records/expired')
}

export const getTrainingRecordReminderSettings = () => {
  return api.get('/houtai/employees/training-records/reminder-settings')
}

export const updateTrainingRecordReminderSettings = (days) => {
  return api.put('/houtai/employees/training-records/reminder-settings', { days })
}

// 员工文档相关API
export const getEmployeeDocuments = (employeeId, documentType = null) => {
  const params = documentType ? { document_type: documentType } : {}
  return api.get(`/houtai/employees/${employeeId}/documents`, { params })
}

export const uploadEmployeeDocument = (employeeId, documentType, formData) => {
  return api.post(`/houtai/employees/${employeeId}/documents/upload`, formData, {
    // 不设置 Content-Type，让请求拦截器自动处理（浏览器会自动设置 multipart/form-data 和 boundary）
    timeout: 120000 // 文件上传使用120秒超时
  })
}

export const previewEmployeeDocument = (employeeId, documentId, format = null) => {
  const params = format ? { format, _t: Date.now() } : { _t: Date.now() }
  return api.get(`/houtai/employees/${employeeId}/documents/${documentId}/preview`, {
    params,
    responseType: 'blob'
  })
}

export const downloadEmployeeDocument = (employeeId, documentId) => {
  return api.get(`/houtai/employees/${employeeId}/documents/${documentId}/download`, {
    responseType: 'blob'
  })
}

export const deleteEmployeeDocument = (employeeId, documentId) => {
  return api.delete(`/houtai/employees/${employeeId}/documents/${documentId}`)
}

// 批量上传员工文档
export const bulkUploadEmployeeDocument = (formData) => {
  return api.post('/houtai/employees/documents/bulk-upload', formData, {
    // 不设置 Content-Type，让请求拦截器自动处理（浏览器会自动设置 multipart/form-data 和 boundary）
    timeout: 180000 // 批量上传使用180秒超时（可能包含多个文件）
  })
}

// 生成员工合同
export const generateEmployeeContract = (employeeId, contractData) => {
  return api.post(`/houtai/employees/${employeeId}/contracts/generate`, contractData, {
    timeout: 120000 // 生成合同需要处理 Word 文档，设置120秒超时
  })
}

// 生成合同签约链接（发送到员工邮箱）
export const createEmployeeContractSignLink = (employeeId, contractId, language = null) => {
  const params = {}
  if (language) params.language = language
  const data = language ? { language } : null
  return api.post(`/houtai/employees/${employeeId}/contracts/${contractId}/create-sign-link`, data, { params })
}

// 提交合同签名（管理员）
export const signEmployeeContract = (employeeId, contractId, signatureData) => {
  return api.post(`/houtai/employees/${employeeId}/contracts/${contractId}/sign`, {
    signature_data: signatureData
  }, {
    timeout: 60000
  })
}

// 保存管理员合同签字坐标
export const saveEmployeeContractSignaturePosition = (employeeId, contractId, position) => {
  return api.post(`/houtai/employees/${employeeId}/contracts/${contractId}/signature-position`, {
    x: position.x,
    y: position.y,
    width: position.width,
    height: position.height,
    page: position.page ?? 0
  }, {
    timeout: 60000
  })
}

// 获取合同员工签名图片
export const getContractEmployeeSignature = (employeeId, contractId) => {
  return api.get(`/houtai/employees/${employeeId}/contracts/${contractId}/employee-signature/image`, {
    responseType: 'blob'
  })
}

// 获取合同管理员签名图片
export const getContractAdminSignature = (employeeId, contractId) => {
  return api.get(`/houtai/employees/${employeeId}/contracts/${contractId}/admin-signature/image`, {
    responseType: 'blob'
  })
}
