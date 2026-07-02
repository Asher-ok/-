import api from './index'

const DOCUMENT_TYPES = [
  { value: 'easy_read', labelKey: 'customerDoc.easyRead' },
  { value: 'intake_form', labelKey: 'customerDoc.intakeForm' },
  { value: 'consent_form', labelKey: 'customerDoc.consentForm' },
  { value: 'handbook', labelKey: 'customerDoc.handbook' },
  { value: 'service_agreement', labelKey: 'customerDoc.serviceAgreement' },
  { value: 'support_plan', labelKey: 'customerDoc.supportPlan' },
  { value: 'emergency_plan', labelKey: 'customerDoc.emergencyPlan' },
  { value: 'home_safety', labelKey: 'customerDoc.homeSafety' },
  { value: 'risk_assessment', labelKey: 'customerDoc.riskAssessment' },
  { value: 'feedback', labelKey: 'customerDoc.feedback' },
  { value: 'review_form', labelKey: 'customerDoc.reviewForm' },
  { value: 'exit_form', labelKey: 'customerDoc.exitForm' }
]

export function getDocumentTypes() {
  return DOCUMENT_TYPES
}

export function getCustomerDocuments(customerId) {
  return api.get(`/houtai/customers/${customerId}/documents`)
}

export function createCustomerDocument(customerId, data) {
  return api.post(`/houtai/customers/${customerId}/documents`, data)
}

export function getCustomerDocument(customerId, docId) {
  return api.get(`/houtai/customers/${customerId}/documents/${docId}`)
}

export function updateCustomerDocument(customerId, docId, data) {
  return api.put(`/houtai/customers/${customerId}/documents/${docId}`, data)
}

export function deleteCustomerDocument(customerId, docId) {
  return api.delete(`/houtai/customers/${customerId}/documents/${docId}`)
}

export function uploadDocumentFile(customerId, docId, file) {
  const formData = new FormData()
  formData.append('file', file)
  // 不设置 Content-Type，由请求拦截器处理（自动带 multipart boundary）
  return api.post(
    `/houtai/customers/${customerId}/documents/${docId}/upload`,
    formData,
    { timeout: 60000 }
  )
}

export function downloadDocument(customerId, docId) {
  return api.get(
    `/houtai/customers/${customerId}/documents/${docId}/download`,
    { responseType: 'blob' }
  )
}

export function createSignLink(customerId, docId) {
  return api.post(`/houtai/customers/${customerId}/documents/${docId}/create-sign-link`)
}

export function previewDocument(customerId, docId, format = 'pdf') {
  return api.get(`/houtai/customers/${customerId}/documents/${docId}/preview`, {
    params: { format, _t: Date.now() },
    responseType: 'blob'
  })
}

export function syncReviewToRisk(customerId, docId) {
  return api.post(`/houtai/customers/${customerId}/documents/${docId}/sync-to-risk`)
}
