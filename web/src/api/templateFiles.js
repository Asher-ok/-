import api from './index'

export const getTemplateFiles = () => {
  return api.get('/houtai/template-files')
}

export const createTemplateFile = (templateName, file) => {
  const formData = new FormData()
  formData.append('template_name', templateName)
  formData.append('file', file)
  return api.post('/houtai/template-files', formData)
}

export const updateTemplateFile = (id, { templateName, file } = {}) => {
  const formData = new FormData()
  if (templateName != null) formData.append('template_name', templateName)
  if (file) formData.append('file', file)
  return api.put(`/houtai/template-files/${id}`, formData)
}

export const deleteTemplateFile = (id) => {
  return api.delete(`/houtai/template-files/${id}`)
}

export const getTemplateFilePlaceholders = (id) => {
  return api.get(`/houtai/template-files/${id}/placeholders`)
}

export const previewTemplateFile = (id, format = 'pdf') => {
  const params = format ? { format, _t: Date.now() } : { _t: Date.now() }
  return api.get(`/houtai/template-files/${id}/preview`, { params, responseType: 'blob' })
}

export const downloadTemplateFile = (id) => {
  return api.get(`/houtai/template-files/${id}/download`, { responseType: 'blob' })
}
