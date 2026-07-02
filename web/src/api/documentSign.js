import api from './index'

const normalizeLangParam = (lang) => {
  if (!lang) return null
  const raw = String(lang).trim().toLowerCase()
  if (!raw) return null
  if (raw === 'zh' || raw === 'zh-cn' || raw.startsWith('zh')) return 'zh'
  if (raw === 'en' || raw === 'en-us' || raw === 'en-gb' || raw.startsWith('en')) return 'en'
  return null
}

const withLangParams = (lang) => {
  const normalized = normalizeLangParam(lang)
  return normalized ? { lang: normalized } : undefined
}

export function getSignDocumentInfo(token, lang = null) {
  return api.get(`/public/documents/sign/${token}`, { params: withLangParams(lang) })
}

export function submitDocumentSignature(token, payload, lang = null) {
  return api.post(`/public/documents/sign/${token}`, payload, { params: withLangParams(lang) })
}

export function confirmDocumentSignature(token, lang = null) {
  return api.post(`/public/documents/sign/${token}/confirm`, null, { params: withLangParams(lang) })
}

export function discardDocumentSignature(token, lang = null) {
  return api.post(`/public/documents/sign/${token}/discard`, null, { params: withLangParams(lang) })
}
