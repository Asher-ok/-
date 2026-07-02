import api from './index'

export function getTaskRecordTemplates(params) {
  return api.get('/houtai/task-record-templates', { params })
}

export function getTaskRecordTemplate(id) {
  return api.get(`/houtai/task-record-templates/${id}`)
}

export function createTaskRecordTemplate(data) {
  return api.post('/houtai/task-record-templates', data)
}

export function updateTaskRecordTemplate(id, data) {
  return api.put(`/houtai/task-record-templates/${id}`, data)
}

export function deleteTaskRecordTemplate(id) {
  return api.delete(`/houtai/task-record-templates/${id}`)
}
