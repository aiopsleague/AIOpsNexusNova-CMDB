import i18n from '@/lang'

export interface DashboardCategory {
  label: string
}

export function dashboardCategory(): Record<number, DashboardCategory> {
  return {
    1: { label: i18n.global.t('cmdb.custom_dashboard.default') },
    2: { label: i18n.global.t('cmdb.custom_dashboard.relation') },
  }
}
