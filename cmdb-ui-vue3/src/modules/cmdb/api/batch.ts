// src/modules/cmdb/api/batch.ts
import * as XLSX from 'xlsx'
import request from '@/utils/request'

const urlPrefix = '/v0.1'

/** Batch upload CIs of a given CI type (existing entries replaced). */
export function uploadData(ciId: string | number, data: Record<string, unknown>): Promise<any> {
  return request.post(
    `${urlPrefix}/ci`,
    { ...data, ci_type: ciId, exist_policy: 'replace' },
    { isShowMessage: false } as any
  )
}

/**
 * Parse an uploaded Excel file into a two-dimensional array of rows.
 *
 * The legacy implementation used `FileReader.readAsBinaryString` +
 * `XLSX.read(...).Sheets[0]` + `XLSX.utils.sheet_to_json(sheet, { header: 1 })`.
 * The `readAsArrayBuffer` variant is used here as the modern, non-deprecated
 * equivalent.
 */
export function processFile(file: File): Promise<any[][]> {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.readAsArrayBuffer(file)
    reader.onload = (e) => {
      const data = e.target?.result as ArrayBuffer
      const workbook = XLSX.read(data, { type: 'array' })
      const sheet = workbook.Sheets[workbook.SheetNames[0]]
      const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 }) as any[][]
      resolve(rows)
    }
  })
}

/** Whether any element in the given array is truthy. */
export function any(ArrayList: unknown[]): boolean {
  for (let i = 0; i < ArrayList.length; i++) {
    if (ArrayList[i]) {
      return true
    }
  }
  return false
}

/** Drop the trailing rows of a two-dimensional array that are entirely empty. */
export function filterNull(twoDimArray: any[][]): any[][] {
  const newArray: any[][] = []
  for (let i = 0; i < twoDimArray.length; i++) {
    if (any(twoDimArray[i])) {
      newArray.push(twoDimArray[i])
    }
  }
  return newArray
}
