// src/modules/cmdb/api/batch.ts
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
 * TODO: reintroduce the `xlsx`-based parser once the `xlsx` dependency is added
 * to the Vue 3 app. The legacy implementation used `FileReader.readAsBinaryString`
 * + `XLSX.read(...).Sheets[0]` + `XLSX.utils.sheet_to_json(sheet, { header: 1 })`.
 */
export function processFile(file: File): Promise<any[][]> {
  return new Promise((_resolve, reject) => {
    // TODO: implement XLSX parsing (xlsx dep missing).
    reject(new Error(`Excel parsing is not available yet (file: ${file?.name ?? 'unknown'})`))
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
