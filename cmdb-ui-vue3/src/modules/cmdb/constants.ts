// Shared CMDB constants (migrated from `@/modules/cmdb/utils/const.js` and
// `@/modules/cmdb/views/discovery/constants.js`).

/** Default attribute names that the backend injects into every CI. */
export const CI_DEFAULT_ATTR: Record<string, string> = {
  UPDATE_USER: '_updated_by',
  UPDATE_TIME: '_updated_at',
}

/** Auto-discovery rule category identifiers. */
export const DISCOVERY_CATEGORY_TYPE: Record<string, string> = {
  AGENT: 'agent',
  SNMP: 'snmp',
  HTTP: 'http',
  PLUGIN: 'plugin',
  COMPONENT: 'components',
  PRIVATE_CLOUD: 'private_cloud',
}

/** Private cloud provider names. */
export const PRIVATE_CLOUD_NAME: Record<string, string> = {
  VCenter: 'vcenter',
}
