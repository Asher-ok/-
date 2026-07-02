import { defineStore } from 'pinia'
import i18n from '@/i18n'

const detectDefaultLocale = () => {
  const lang = typeof navigator !== 'undefined' ? navigator.language || '' : ''
  return lang.toLowerCase().startsWith('zh') ? 'zh' : 'en'
}

export const useI18nStore = defineStore('i18n', {
  state: () => ({
    locale: localStorage.getItem('locale') || detectDefaultLocale()
  }),
  
  actions: {
    setLocale(locale) {
      this.locale = locale
      localStorage.setItem('locale', locale)
      // 更新 i18n 实例的语言
      i18n.global.locale.value = locale
    }
  }
})
