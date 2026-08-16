// src/config/setting.ts
import { COLOR_PRIMARY } from '@/theme/tokens'

export interface AppSetting {
  primaryColor: string
  navTheme: 'dark' | 'light'
  themeMode: 'light' | 'dark' | 'system'
  layout: 'sidemenu' | 'topmenu'
  contentWidth: 'Fluid' | 'Fixed'
  fixedHeader: boolean
  fixSiderbar: boolean
  autoHideHeader: boolean
  colorWeak: boolean
  multiTab: boolean
}

const setting: AppSetting = {
  primaryColor: COLOR_PRIMARY,
  navTheme: 'dark',
  themeMode: 'system',
  layout: 'sidemenu',
  contentWidth: 'Fixed',
  fixedHeader: true,
  fixSiderbar: true,
  autoHideHeader: true,
  colorWeak: false,
  multiTab: false,
}

export default setting
