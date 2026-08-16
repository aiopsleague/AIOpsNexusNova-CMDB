// src/modules/cmdb/api/ipam.ts
import request from '@/utils/request'

const urlPrefix = '/v0.1'

export function getIPAMSubnet(): Promise<any> {
  return request.get(`${urlPrefix}/ipam/subnet`)
}

export function postIPAMSubnet(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ipam/subnet`, data)
}

export function getIPAMSubnetById(id: string | number): Promise<any> {
  return request.get(`${urlPrefix}/ipam/subnet/${id}`)
}

export function putIPAMSubnet(id: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ipam/subnet/${id}`, data)
}

export function deleteIPAMSubnet(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/ipam/subnet/${id}`)
}

export function moveIPAMSubnet(id: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ipam/subnet/${id}/move`, data)
}

export function postIPAMScope(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ipam/scope`, data)
}

export function putIPAMScope(id: string | number, data: Record<string, unknown>): Promise<any> {
  return request.put(`${urlPrefix}/ipam/scope/${id}`, data)
}

export function deleteIPAMScope(id: string | number): Promise<any> {
  return request.delete(`${urlPrefix}/ipam/scope/${id}`)
}

export function getIPAMAddress(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ipam/address`, { params })
}

export function getIPAMHosts(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ipam/subnet/hosts`, { params })
}

export function postIPAMAddress(data: Record<string, unknown>): Promise<any> {
  return request.post(`${urlPrefix}/ipam/address`, data)
}

export function getIPAMHistoryOperate(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ipam/history/operate`, { params })
}

export function getIPAMHistoryScan(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ipam/history/scan`, { params })
}

export function getIPAMStats(params?: Record<string, unknown>): Promise<any> {
  return request.get(`${urlPrefix}/ipam/stats`, { params })
}
