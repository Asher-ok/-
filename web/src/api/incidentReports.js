import api from './index'

export function getIncidentReports(params) {
  return api.get('/houtai/incident-reports', { params })
}

export function createIncidentReport(data) {
  return api.post('/houtai/incident-reports', data)
}

export function updateIncidentReport(id, data) {
  return api.put(`/houtai/incident-reports/${id}`, data)
}

export function deleteIncidentReport(id) {
  return api.delete(`/houtai/incident-reports/${id}`)
}

export function getIncidentReportSubmissions(params) {
  return api.get('/houtai/incident-reports/submissions', { params })
}

export function getIncidentReportSubmission(id) {
  return api.get(`/houtai/incident-reports/submissions/${id}`)
}
