import api from './index'

export function getTaskRecord(params) {
  return api.get('/houtai/task-records', { params })
}

export function getTaskRecordSubmissions(params) {
  return api.get('/houtai/task-records/submissions', { params })
}

export function getTaskRecordSubmission(id) {
  return api.get(`/houtai/task-records/submissions/${id}`)
}

export function deleteTaskRecordSubmission(id) {
  return api.delete(`/houtai/task-records/submissions/${id}`)
}
