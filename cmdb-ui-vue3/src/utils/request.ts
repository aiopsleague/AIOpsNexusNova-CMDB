// src/utils/request.ts
import axios, { type AxiosError } from 'axios'
import { message, notification } from 'ant-design-vue'
import i18n from '@/lang'

export const TOKEN_KEY = 'pro__Access-Token'

/** 从 localStorage 读取鉴权 token（与旧 vue-ls 的 pro__ 命名空间一致）。 */
export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/** 提取错误描述：优先服务端 message，否则回退到 fallbackKey 的 i18n 文案。 */
export function extractErrorMessage(error: unknown, fallbackKey: string): string {
  const data = (error as AxiosError)?.response?.data as { message?: string } | undefined
  return data?.message || i18n.global.t(fallbackKey)
}

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 6000,
  withCredentials: true,
})

// 请求拦截器：附加 Access-Token 与 Accept-Language
service.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers['Access-Token'] = token
  }
  config.headers['Accept-Language'] = localStorage.getItem('ops_locale') || 'zh'
  return config
})

// 响应拦截器：解包 response.data
service.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError) => {
    const status = error.response?.status
    if (status && /^5\d{2}$/.test(String(status))) {
      message.error(extractErrorMessage(error, 'requestServiceError'))
    } else if (status === 412) {
      notification.warning({
        key: 'rate-limit',
        message: 'WARNING',
        description: i18n.global.t('requestWait', { time: 5 }),
        duration: 5,
      })
    } else if (status === 401) {
      if (window.location.pathname !== '/user/login') {
        localStorage.removeItem(TOKEN_KEY)
        window.location.href = '/user/logout'
      }
    } else if ((error.config as { isShowMessage?: boolean })?.isShowMessage === false) {
      // 静默：调用方显式关闭错误提示
    } else {
      message.error(extractErrorMessage(error, 'requestError'))
    }
    return Promise.reject(error)
  }
)

export default service
