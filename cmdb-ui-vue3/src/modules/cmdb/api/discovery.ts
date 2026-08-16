import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch the HTTP discovery categories for a rule. */
export function getHttpCategories(name: string): Promise<any> {
  return request.get(`${urlPrefix}/adr/http/${name}/categories`)
}

/** Fetch the HTTP discovery attributes for a rule. */
export function getHttpAttributes(name: string, params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/adr/http/${name}/attributes`, { params })
}

/** Fetch the SNMP/component discovery attributes for a rule. */
export function getSnmpAttributes(type: string, name: string): Promise<any> {
  return request.get(`${urlPrefix}/adr/${type}/${name}/attributes`)
}

/** Fetch the HTTP attribute -> CI attribute mapping for a rule. */
export function getHttpAttrMapping(name: string, resource: string): Promise<any> {
  return request.get(`${urlPrefix}/adr/http/${name}/mapping`, { params: { resource } })
}
