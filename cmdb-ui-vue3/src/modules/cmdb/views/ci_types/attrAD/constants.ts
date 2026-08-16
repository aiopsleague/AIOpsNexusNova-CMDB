/** Tab keys for the custom / existing-config switch inside cloud AD forms. */
export const TAB_KEY = {
  CUSTOM: 'custom',
  CONFIG: 'config',
} as const

/** The custom / existing-config tab list rendered by CloudTab. */
export const tabList = [
  {
    key: TAB_KEY.CUSTOM,
    text: 'cmdb.ad.tabCustom',
  },
  {
    key: TAB_KEY.CONFIG,
    text: 'cmdb.ad.tabConfig',
  },
] as const
