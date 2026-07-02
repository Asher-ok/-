// 应用配置
export default {
  // API配置
  apiBaseURL: import.meta.env.VITE_API_BASE_URL || 'http://176.97.68.115:8000',
  
  // 应用信息
  appName: '澳州项目管理后台',
  appVersion: '1.0.0',
  
  // 分页配置
  pagination: {
    pageSize: 10,
    pageSizes: [10, 20, 50, 100]
  },
  
  // 上传配置
  upload: {
    maxSize: 10 * 1024 * 1024, // 10MB
    accept: '.jpg,.jpeg,.png,.pdf,.doc,.docx'
  },
  
  // 日期格式
  dateFormat: 'YYYY-MM-DD',
  datetimeFormat: 'YYYY-MM-DD HH:mm:ss'
}
