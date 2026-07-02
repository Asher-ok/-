import api from './index'

export function getLeaveRequests(params) {
  return api.get('/houtai/leave-requests', { params })
}

export function approveLeave(id) {
  return api.post(`/houtai/leave-requests/${id}/approve`)
}

export function rejectLeave(id, reason) {
  return api.post(`/houtai/leave-requests/${id}/reject`, { reason })
}
