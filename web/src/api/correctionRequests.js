import api from './index'

export function getCorrectionRequests(params) {
  return api.get('/houtai/correction-requests', { params })
}

export function approveCorrection(id) {
  return api.post(`/houtai/correction-requests/${id}/approve`)
}

export function rejectCorrection(id) {
  return api.post(`/houtai/correction-requests/${id}/reject`)
}
