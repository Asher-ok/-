import { createI18n } from 'vue-i18n'
import zh from './locales/zh'
import en from './locales/en'

const messages = {
  zh,
  en
}

// 语言优先级：localStorage > 浏览器语言(zh/en) > en
const browserLocale = typeof navigator !== 'undefined' && navigator.language ? navigator.language : 'en'
const normalizedBrowserLocale = browserLocale.toLowerCase().startsWith('zh') ? 'zh' : 'en'
const savedLocale = localStorage.getItem('locale') || normalizedBrowserLocale

const i18n = createI18n({
  legacy: false,
  locale: savedLocale,
  fallbackLocale: 'en',
  messages
})

export default i18n
