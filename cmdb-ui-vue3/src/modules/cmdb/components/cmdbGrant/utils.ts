export interface RowParams {
  row: Record<string, any>
}

export function getCurrentRowStyle(params: RowParams, addedRids: Array<{ rid: string | number }>): string {
  const idx = addedRids.findIndex((item) => item.rid === params.row.rid)
  return idx > -1 ? 'background-color:#E0E7FF!important' : ''
}

export function getCurrentRowClass(params: RowParams, addedRids: Array<{ rid: string | number }>): string {
  const idx = addedRids.findIndex((item) => item.rid === params.row.rid)
  return idx > -1 ? 'grant-table-row-focus' : ''
}
