import api from './index'

export const exportTaskMaterials = (taskId) => {
  return api.get(`/houtai/export/task/${taskId}/materials`, {
    responseType: 'blob'
  })
}
