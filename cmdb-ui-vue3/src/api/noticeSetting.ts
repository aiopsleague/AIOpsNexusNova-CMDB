import request from '@/utils/request'

/** Fetch the configured application bot list for notifications. */
export function getNoticeConfigAppBot(): Promise<any> {
  return request.get('/common-setting/v1/notice_config/app_bot')
}
