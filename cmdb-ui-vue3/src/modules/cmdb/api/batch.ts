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

// NOTE: The legacy `processFile` / `writeCsv` / `writeExcel` / `any` /
// `filterNull` helpers (XLSX + json2csv file processing) are deferred until
// those dependencies are added to the Vue 3 app.
