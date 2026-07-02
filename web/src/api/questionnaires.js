import api from './index'

const normalizeString = (value) => {
  if (value == null) return ''
  return String(value).trim()
}

const normalizeI18nText = (value) => {
  if (!value || typeof value !== 'object') return null
  const zh = normalizeString(value.zh || value['zh-CN'] || value.cn)
  const en = normalizeString(value.en || value['en-US'])
  if (!zh && !en) return null
  return { zh: zh || '', en: en || '' }
}

const pickPrimaryText = (i18nValue, fallback) => {
  const normalized = normalizeI18nText(i18nValue)
  if (normalized) return normalized.zh || normalized.en || normalizeString(fallback)
  return normalizeString(fallback)
}

const normalizeMaybeId = (id) => {
  if (id == null) return undefined
  if (typeof id === 'number' && Number.isFinite(id)) return id
  if (typeof id === 'string') {
    const v = id.trim()
    if (!v) return undefined
    if (/^opt\d+$/i.test(v)) return undefined
    if (/^\d+$/.test(v)) return Number(v)
    return v
  }
  return undefined
}

const normalizeOptionObject = (option, index) => {
  if (option == null) return null

  if (typeof option === 'string' || typeof option === 'number') {
    const v = normalizeString(option)
    if (!v) return null
    return { label: v, value: v, text: v, order_index: String(index + 1) }
  }

  if (typeof option !== 'object') return null

  const textI18n = normalizeI18nText(
    option.text_i18n || {
      zh: option.text_zh || option.label_zh,
      en: option.text_en || option.label_en
    }
  )
  const textCandidate = pickPrimaryText(textI18n, option.text ?? option.label ?? option.name ?? option.title ?? option.value ?? '')
  const label = normalizeString(option.label ?? textCandidate)
  const text = normalizeString(option.text ?? textCandidate)
  const value = normalizeString(option.value ?? option.label ?? textCandidate)
  if (!label || !value) return null

  const orderIndex = option.order_index != null && String(option.order_index).trim() !== '' ? String(option.order_index) : String(index + 1)
  const id = normalizeMaybeId(option.id)
  return {
    ...(id !== undefined ? { id } : {}),
    label,
    value,
    text,
    ...(textI18n ? { text_i18n: textI18n } : {}),
    order_index: orderIndex
  }
}

const isChoiceQuestionType = (type) => type === 'single_choice' || type === 'multiple_choice'

const normalizeQuestionnairePayload = (raw) => {
  const questions = Array.isArray(raw?.questions) ? raw.questions : []
  const customerType = raw?.customer_type
  const titleI18n = normalizeI18nText(raw?.title_i18n)
  const descriptionI18n = normalizeI18nText(raw?.description_i18n)
  const title = pickPrimaryText(titleI18n, raw?.title ?? '')
  const description = pickPrimaryText(descriptionI18n, raw?.description ?? '')
  const base = {
    title,
    description,
    is_active: raw?.is_active !== false
  }

  const payload = {
    ...base,
    ...(titleI18n ? { title_i18n: titleI18n } : {}),
    ...(descriptionI18n ? { description_i18n: descriptionI18n } : {}),
    ...(customerType != null ? { customer_type: customerType } : {})
  }

  if (!Array.isArray(raw?.questions)) return payload

  return {
    ...payload,
    questions: questions
      .map((q, index) => {
        const type = q?.type ?? 'single_choice'
        const rawOptions = Array.isArray(q?.options) ? q.options : []
        const options = isChoiceQuestionType(type)
          ? rawOptions.map((opt, optIndex) => normalizeOptionObject(opt, optIndex)).filter(Boolean)
          : []

        const id = normalizeMaybeId(q?.id)
        const titleI18n = normalizeI18nText(q?.title_i18n)
        const title = pickPrimaryText(titleI18n, q?.title ?? '')
        return {
          ...(id !== undefined ? { id } : {}),
          title,
          ...(titleI18n ? { title_i18n: titleI18n } : {}),
          type,
          required: !!q?.required,
          options,
          order_index: q?.order_index != null && String(q.order_index).trim() !== '' ? String(q.order_index) : String(index + 1)
        }
      })
      .filter((q) => {
        if (normalizeString(q.title)) return true
        const titleI18n = normalizeI18nText(q.title_i18n)
        return !!(titleI18n && (titleI18n.zh || titleI18n.en))
      })
  }
}

export const getQuestionnaires = () => {
  return api.get('/houtai/questionnaires')
}

export const getQuestionnaire = (id) => {
  return api.get(`/houtai/questionnaires/${id}`)
}

export const createQuestionnaire = (data) => {
  return api.post('/houtai/questionnaires', normalizeQuestionnairePayload(data))
}

export const updateQuestionnaire = (id, data) => {
  return api.put(`/houtai/questionnaires/${id}`, normalizeQuestionnairePayload(data))
}

export const deleteQuestionnaire = (id) => {
  return api.delete(`/houtai/questionnaires/${id}`)
}

export const addQuestion = (questionnaireId, data) => {
  return api.post(`/houtai/questionnaires/${questionnaireId}/questions`, data)
}

export const updateQuestion = (questionnaireId, questionId, data) => {
  return api.put(`/houtai/questionnaires/${questionnaireId}/questions/${questionId}`, data)
}

export const deleteQuestion = (questionnaireId, questionId) => {
  return api.delete(`/houtai/questionnaires/${questionnaireId}/questions/${questionId}`)
}

export const getQuestionnaireResponses = () => {
  return api.get('/houtai/questionnaires/responses')
}

export const getQuestionnaireResponse = (id) => {
  return api.get(`/houtai/questionnaires/responses/${id}`)
}

export const exportQuestionnaireResponse = (id) => {
  return api.get(`/houtai/questionnaires/responses/${id}/export`, {
    responseType: 'blob'
  })
}

export const deleteQuestionnaireResponse = (id) => {
  return api.delete(`/houtai/questionnaires/responses/${id}`)
}
