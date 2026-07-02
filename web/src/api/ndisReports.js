import api from './index'

/**
 * 获取服务使用报告数据
 * @param {Object} params - { customer_id?, date_start?, date_end?, ndis_only? }
 */
export const getServiceUsageData = (params = {}) => {
  return api.get('/houtai/ndis-reports/service-usage/data', { params })
}

/**
 * 获取财务报告数据
 * @param {Object} params - { customer_id?, date_start?, date_end?, ndis_only? }
 */
export const getFinancialData = (params = {}) => {
  return api.get('/houtai/ndis-reports/financial/data', { params })
}

/**
 * 下载服务使用报告
 * @param {Object} params - { customer_id?, date_start?, date_end?, ndis_only? }
 */
export const downloadServiceUsageReport = (params = {}) => {
  return api.get('/houtai/ndis-reports/service-usage', {
    params,
    responseType: 'blob'
  })
}

/**
 * 下载财务报告
 * @param {Object} params - { customer_id?, date_start?, date_end?, ndis_only? }
 */
export const downloadFinancialReport = (params = {}) => {
  return api.get('/houtai/ndis-reports/financial', {
    params,
    responseType: 'blob'
  })
}
