import api from './index'

export const getUpdateSummary = () => {
  return api.get('/houtai/updates/summary')
}

export const markUpdatesRead = (entityType, entityId = null) => {
  return api.post('/houtai/updates/mark-read', {
    entity_type: entityType,
    entity_id: entityId
  })
}

