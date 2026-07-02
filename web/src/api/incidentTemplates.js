import api from './index'

export function getIncidentTemplates(params) {
  return api.get('/houtai/incident-templates', { params })
}

export function getIncidentTemplate(id) {
  return api.get(`/houtai/incident-templates/${id}`)
}

export function createIncidentTemplate(data) {
  return api.post('/houtai/incident-templates', data)
}

export function updateIncidentTemplate(id, data) {
  return api.put(`/houtai/incident-templates/${id}`, data)
}

export function deleteIncidentTemplate(id) {
  return api.delete(`/houtai/incident-templates/${id}`)
}
