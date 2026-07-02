// 统一常量配置

// 任务状态
export const TASK_STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  REJECTED: 'rejected'
}

export const TASK_STATUS_TEXT = {
  [TASK_STATUS.PENDING]: '待领取',
  [TASK_STATUS.IN_PROGRESS]: '进行中',
  [TASK_STATUS.COMPLETED]: '已完成',
  [TASK_STATUS.REJECTED]: '审核未通过'
}

export const TASK_STATUS_TYPE = {
  [TASK_STATUS.PENDING]: 'info',
  [TASK_STATUS.IN_PROGRESS]: 'warning',
  [TASK_STATUS.COMPLETED]: 'success',
  [TASK_STATUS.REJECTED]: 'danger'
}

// 发票状态
export const INVOICE_STATUS = {
  DRAFT: 'draft',
  SENT: 'sent',
  PAID: 'paid'
}

export const INVOICE_STATUS_TEXT = {
  [INVOICE_STATUS.DRAFT]: '草稿',
  [INVOICE_STATUS.SENT]: '已发送',
  [INVOICE_STATUS.PAID]: '已支付'
}

export const INVOICE_STATUS_TYPE = {
  [INVOICE_STATUS.DRAFT]: 'info',
  [INVOICE_STATUS.SENT]: 'warning',
  [INVOICE_STATUS.PAID]: 'success'
}

// 问题类型
export const QUESTION_TYPE = {
  SINGLE_CHOICE: 'single_choice',
  MULTIPLE_CHOICE: 'multiple_choice',
  TEXT: 'text',
  NUMBER: 'number',
  DATE: 'date'
}

export const QUESTION_TYPE_TEXT = {
  [QUESTION_TYPE.SINGLE_CHOICE]: '单选',
  [QUESTION_TYPE.MULTIPLE_CHOICE]: '多选',
  [QUESTION_TYPE.TEXT]: '文本',
  [QUESTION_TYPE.NUMBER]: '数字',
  [QUESTION_TYPE.DATE]: '日期'
}

// API基础URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://176.97.68.115:8000'

// 分页配置
export const PAGINATION = {
  PAGE_SIZE: 10,
  PAGE_SIZES: [10, 20, 50, 100]
}

// 日期格式
export const DATE_FORMAT = 'YYYY-MM-DD'
export const DATETIME_FORMAT = 'YYYY-MM-DD HH:mm:ss'
