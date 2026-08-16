import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Fetch all auto-discovery rules. */
export function getDiscovery(): Promise<any> {
  return request.get(`${urlPrefix}/adr`)
}

/** Delete an auto-discovery rule. */
export function deleteDiscovery(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/adr/${id}`)
}

/** Fetch the auto-discovery rules bound to a CI type. */
export function getCITypeDiscovery(typeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adt/ci_types/${typeId}`)
}

/** Bind a new auto-discovery rule to a CI type. */
export function postCITypeDiscovery(typeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/adt/ci_types/${typeId}`, data)
}

/** Update a CI type auto-discovery binding. */
export function putCITypeDiscovery(adtId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/adt/${adtId}`, data)
}

/** Delete a CI type auto-discovery binding. */
export function deleteCITypeDiscovery(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/adt/${id}`)
}

/** Fetch the sync histories of a CI type auto-discovery binding. */
export function getAdtSyncHistories(adtId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adt/${adtId}/sync/histories`, { params: { page_size: 9999 } })
}

/** Trigger a test run of a CI type auto-discovery binding. */
export function postAdtTest(adtId: string | number): Promise<any> {
  return request.post(`${urlPrefix}/adt/${adtId}/test`)
}

/** Fetch the result of an auto-discovery test run. */
export function getAdtTestResult(execId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adt/test/${execId}/result`)
}

/** Fetch the ADT attributes of a CI type. */
export function getCITypeAttributes(typeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adt/ci_types/${typeId}/attributes`)
}

/** Fetch the ADT relations of a CI type. */
export function getCITypeRelations(typeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adt/ci_types/${typeId}/relations`)
}

/** Persist the ADT relations of a CI type. */
export function postCITypeRelations(typeId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/adt/ci_types/${typeId}/relations`, data)
}

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

/** Fetch the HTTP accounts configured for an auto-discovery rule. */
export function getHTTPAccounts(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/adr/accounts`, { params })
}

/** Save the HTTP accounts configured for an auto-discovery rule. */
export function postHTTPAccounts(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/adr/accounts`, data)
}

/** Create an auto-discovery rule. */
export function postDiscovery(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/adr`, data)
}

/** Update an auto-discovery rule. */
export function putDiscovery(id: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/adr/${id}`, data)
}

/** Fetch the CI type groups (with nested ci_types) of the discovery pool. */
export function getADCCiTypes(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/adc/ci_types`, { params })
}

/** Fetch the attributes of a discovery-pool CI type. */
export function getADCCiTypesAttrs(typeId: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adc/ci_types/${typeId}/attributes`)
}

/** Accept a discovery-pool record into the CMDB. */
export function updateADCAccept(adcId: string | number): Promise<any> {
  return request.put(`${urlPrefix}/adc/${adcId}/accept`)
}

/** Fetch discovery-pool records. */
export function getAdc(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/adc`, { params })
}

/** Fetch a single discovery-pool record. */
export function getAdcById(id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/adc/${id}`)
}

/** Delete a discovery-pool record. */
export function deleteAdc(adcId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/adc/${adcId}`)
}

/** Fetch discovery-pool statistics. */
export function getAdcCounter(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/adc/counter`, { params })
}

/** Fetch discovery execution histories. */
export function getAdcExecHistories(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/adc/exec/histories`, { params })
}

/** Delete the discovery execution histories of a CI type. */
export function deleteAdcExecHistories(typeId: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/adc/exec/histories/${typeId}`)
}
