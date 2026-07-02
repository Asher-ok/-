import api from './index'

const normalizeTaskId = (row) => row?.id ?? row?.task_id ?? row?.taskId ?? row?.taskID ?? null

const normalizeTaskRow = (row) => {
  if (!row || typeof row !== 'object') return row
  const id = normalizeTaskId(row)
  return id != null ? { ...row, id } : row
}

const getArrayFromResponse = (res) => {
  if (Array.isArray(res)) return res
  if (Array.isArray(res?.data)) return res.data
  if (Array.isArray(res?.items)) return res.items
  if (Array.isArray(res?.results)) return res.results
  return []
}

export const getTasks = (params = {}) => {
  return api.get('/houtai/tasks', { params }).then((res) => getArrayFromResponse(res).map(normalizeTaskRow))
}

export const getTask = (id) => {
  return api.get(`/houtai/tasks/${id}`).then(normalizeTaskRow)
}

export const createTask = (data) => {
  return api.post('/houtai/tasks', data)
}

export const updateTask = (id, data) => {
  return api.put(`/houtai/tasks/${id}`, data)
}

export const deleteTask = async (id, params = undefined) => {
  try {
    return await api.delete(`/houtai/tasks/${id}`, params ? { params } : undefined)
  } catch (error) {
    const status = error?.response?.status
    if (status !== 404 && status !== 405 && status !== 500) throw error

    try {
      const mergedParams = { task_id: id, ...(params || {}) }
      return await api.delete('/houtai/tasks', { params: mergedParams })
    } catch (error2) {
      const status2 = error2?.response?.status
      if (status2 !== 404 && status2 !== 405 && status2 !== 500) throw error2
      return api.post(`/houtai/tasks/${id}/delete`, params || {})
    }
  }
}

export const approveTask = (id) => {
  return api.post(`/houtai/tasks/${id}/approve`)
}

export const rejectTask = (id, rejectReason) => {
  return api.post(`/houtai/tasks/${id}/reject?reject_reason=${encodeURIComponent(rejectReason)}`)
}

export const cancelTask = (id, cancelReason) => {
  return api.post(`/houtai/tasks/${id}/cancel?cancel_reason=${encodeURIComponent(cancelReason)}`)
}

export const getTaskLocationTracks = (id) => {
  return api.get(`/houtai/tasks/${id}/location-tracks`)
}

export const updateTaskSignature = (id, signatureData) => {
  return api.put(`/houtai/tasks/${id}/signature`, { signature_data: signatureData })
}

export const deleteTaskSignature = (id) => {
  return api.delete(`/houtai/tasks/${id}/signature`)
}

export const uploadTaskPhotos = (id, files) => {
  const formData = new FormData()
  ;(files || []).forEach((file) => {
    formData.append('files', file)
  })
  return api.post(`/houtai/tasks/${id}/photos`, formData)
}

export const deleteTaskPhoto = (taskId, photoId) => {
  return api.delete(`/houtai/tasks/${taskId}/photos/${photoId}`)
}

export const getTaskServices = (taskId) => {
  return api.get(`/houtai/tasks/${taskId}/services`)
}

export const addTaskService = (taskId, data) => {
  return api.post(`/houtai/tasks/${taskId}/services`, data)
}

export const updateTaskService = (taskId, itemId, data) => {
  return api.put(`/houtai/tasks/${taskId}/services/${itemId}`, data)
}

export const deleteTaskService = async (taskId, itemId) => {
  try {
    return await api.delete(`/houtai/tasks/${taskId}/services/${itemId}`)
  } catch (error) {
    const status = error?.response?.status
    if (status !== 404 && status !== 405 && status !== 500) throw error
    return api.post(`/houtai/tasks/${taskId}/services/${itemId}/delete`)
  }
}

export const getCustomerServiceLevel1 = (customerId, params = {}) => {
  return api.get(`/houtai/tasks/customer/${customerId}/service-level1`, { params })
}

export const getCustomerServiceLevel2 = (customerId, level1Id, params = {}) => {
  return api.get(`/houtai/tasks/customer/${customerId}/service-level2`, { params: { level1_id: level1Id, ...params } })
}

export const getCustomerServiceLevel3 = (customerId, params = {}) => {
  return api.get(`/houtai/tasks/customer/${customerId}/service-level3`, { params })
}

export const getCustomerServiceCodes = (customerId, level3Id, params = {}) => {
  return api.get(`/houtai/tasks/customer/${customerId}/service-codes`, { params: { level3_id: level3Id, ...params } })
}
