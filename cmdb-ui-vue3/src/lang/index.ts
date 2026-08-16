// src/lang/index.ts
import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'

const saved = localStorage.getItem('ops_locale') || 'zh'

const i18n = createI18n({
  legacy: false,
  locale: saved,
  fallbackLocale: 'zh',
  messages: { zh, en },
  silentTranslationWarn: true,
})

export default i18n
