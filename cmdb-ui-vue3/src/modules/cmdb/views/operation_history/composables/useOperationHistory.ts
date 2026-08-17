// src/modules/cmdb/views/operation_history/composables/useOperationHistory.ts
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { PAGINATION_CONFIG } from '../constants'

/** Shared helpers for the operation-history table views (migrated from commonMixin). */
export function useOperationHistory() {
  const { t } = useI18n()

  function handleError(error: any, action = 'operation') {
    if (import.meta.env.DEV) {
      console.error(`[OperationHistory] ${action} failed:`, error)
    }
    message.error(error?.message || t('cmdb.history.operationFailed'))
  }

  function applyFilter(
    queryParams: Record<string, any>,
    getTable: (params: Record<string, any>) => void,
    updates: Record<string, any> = {}
  ) {
    Object.assign(queryParams, {
      page: 1,
      page_size: PAGINATION_CONFIG.DEFAULT_PAGE_SIZE,
      ...updates,
    })
    getTable(queryParams)
  }

  function createMergeRowMethod(fields: string[], groupFields: string[] = ['created_at']) {
    return ({ row, _rowIndex, column, visibleData }: any) => {
      const cellValue = row[column.field]

      if (!cellValue || !fields.includes(column.field)) {
        return
      }

      const prevRow = visibleData[_rowIndex - 1]
      let nextRow = visibleData[_rowIndex + 1]

      const checkGroupMatch = (compareRow: any) =>
        groupFields.every((field) => compareRow[field] === row[field])

      if (prevRow && prevRow[column.field] === cellValue && checkGroupMatch(prevRow)) {
        return { rowspan: 0, colspan: 0 }
      }

      let countRowspan = 1
      while (nextRow && nextRow[column.field] === cellValue && checkGroupMatch(nextRow)) {
        nextRow = visibleData[++countRowspan + _rowIndex]
      }

      if (countRowspan > 1) {
        return { rowspan: countRowspan, colspan: 1 }
      }
    }
  }

  return { handleError, applyFilter, createMergeRowMethod }
}
