export interface DashboardItem {
  title: string
  span: string
  component: string
}

export const dashboardList: DashboardItem[] = [
  { title: '资源总览', span: '16', component: 'SummaryCounter' },
  { title: '系统总览', span: '8', component: 'SystemCounter' },
  { title: '业务总览', span: '24', component: 'BusinessCounter' },
]
