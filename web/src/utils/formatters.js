// 格式化工具函数

/**
 * 格式化日期
 */
export const formatDate = (date, format = 'YYYY-MM-DD') => {
  if (!date) return '-'
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hour)
    .replace('mm', minute)
    .replace('ss', second)
}

export const formatDateTimeToMinute = (value) => {
  if (!value) return '-'
  if (value === '-') return '-'

  if (typeof value === 'string') {
    const m = value.match(/(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/)
    if (m) return `${m[1]} ${m[2]}`
    const md = value.match(/^\d{4}-\d{2}-\d{2}$/)
    if (md) return md[0]
    const normalized = value.includes('T') ? value : value.replace(' ', 'T')
    const d = new Date(normalized)
    if (!Number.isNaN(d.getTime())) return formatDate(d, 'YYYY-MM-DD HH:mm')
    return value
  }

  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return '-'
  return formatDate(d, 'YYYY-MM-DD HH:mm')
}

/**
 * 格式化金额
 */
export const formatCurrency = (amount, currency = 'AUD') => {
  if (amount === null || amount === undefined) return '-'
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: currency
  }).format(amount)
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

/**
 * 截断文本
 */
export const truncateText = (text, length = 50) => {
  if (!text) return '-'
  if (text.length <= length) return text
  return text.substring(0, length) + '...'
}
