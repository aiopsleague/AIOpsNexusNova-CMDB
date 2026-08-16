import type { Component } from 'vue'
import {
  CalendarOutlined,
  CheckOutlined,
  ClockCircleOutlined,
  CodeOutlined,
  EditOutlined,
  FieldNumberOutlined,
  FieldTimeOutlined,
  FileOutlined,
  FontSizeOutlined,
  LinkOutlined,
  LockOutlined,
  NumberOutlined,
} from '@ant-design/icons-vue'
import i18n from '@/lang'
import { CI_DEFAULT_ATTR } from '@/modules/cmdb/constants'

/** Human-readable labels for each CI attribute value type key. */
export function valueTypeMap(): Record<string, string> {
  return {
    '0': i18n.global.t('cmdb.ciType.int'),
    '1': i18n.global.t('cmdb.ciType.float'),
    '2': i18n.global.t('cmdb.ciType.shortText'),
    '3': i18n.global.t('cmdb.ciType.datetime'),
    '4': i18n.global.t('cmdb.ciType.date'),
    '5': i18n.global.t('cmdb.ciType.time'),
    '6': 'JSON',
    '7': i18n.global.t('cmdb.ciType.password'),
    '8': i18n.global.t('cmdb.ciType.link'),
    '9': i18n.global.t('cmdb.ciType.longText'),
    '10': i18n.global.t('cmdb.ciType.bool'),
    '11': i18n.global.t('cmdb.ciType.reference'),
    '12': i18n.global.t('cmdb.ciType.file'),
  }
}

/** Compute the effective value_type key from an attribute's flags. */
export function getPropertyType(attr: Record<string, any>): string {
  if (attr.is_password) return '7'
  if (attr.is_link) return '8'
  if (attr.is_file) return '12'

  switch (attr.value_type) {
    case '0':
      return attr.is_reference ? '11' : '0'
    case '2':
      return attr.is_index ? '2' : '9'
    case '7':
      return attr.is_bool ? '10' : '7'
    default:
      return attr?.value_type ?? ''
  }
}

/** Map a CI attribute to a representative Ant Design icon. */
export function getPropertyIcon(attr: Record<string, any>): Component | null {
  const valueType = String(attr.value_type ?? '')
  switch (valueType) {
    case '0':
      return attr.is_reference ? LinkOutlined : FieldNumberOutlined
    case '1':
      return NumberOutlined
    case '2':
      if (attr.is_file) return FileOutlined
      if (attr.is_password) return LockOutlined
      if (attr.is_link) return LinkOutlined
      if (attr.is_index === false) return EditOutlined
      return FontSizeOutlined
    case '3':
      return FieldTimeOutlined
    case '4':
      return CalendarOutlined
    case '5':
      return ClockCircleOutlined
    case '6':
      return CodeOutlined
    case '7':
      return attr.is_bool ? CheckOutlined : LockOutlined
    case '8':
      return LinkOutlined
    case '9':
      return EditOutlined
    case '10':
      return CheckOutlined
    case '11':
      return LinkOutlined
    case '12':
      return FileOutlined
    default:
      return null
  }
}

/** Minimal deep clone for plain JSON data (drop-in for lodash.cloneDeep). */
export function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

/** Minimal lodash.orderBy drop-in for a single ascending/descending key. */
function orderBy<T>(list: T[], key: string, order: 'asc' | 'desc'): T[] {
  const result = [...list]
  result.sort((a, b) => {
    const av = (a as Record<string, any>)?.[key]
    const bv = (b as Record<string, any>)?.[key]
    if (av === bv) return 0
    const cmp = av < bv ? -1 : 1
    return order === 'desc' ? -cmp : cmp
  })
  return result
}

function sum(arr: number[]): number {
  return arr.reduce((prev, curr) => prev + curr, 0)
}

/** Approximate rendered width of a value (used for table column auto-sizing). */
function strLength(fData: unknown): number {
  if (!fData) return 0
  let value = fData
  if (Array.isArray(value)) {
    value = value.join(' ')
  }
  const str = String(value)
  let intLength = 0
  for (let i = 0; i < str.length; i++) {
    if (str.charCodeAt(i) < 0 || str.charCodeAt(i) > 255) {
      intLength += 2
    } else {
      intLength += 1
    }
  }
  return Math.floor(intLength * 7)
}

/**
 * Build the vxe-table column config for the CI instance list, including per-attribute
 * inline edit renderers and column widths.
 */
export function getCITableColumns(data: any[], attrList: any[], width = 1600): any[] {
  const _attrList = orderBy(attrList, 'is_fixed', 'desc')
  const columns: any[] = []
  for (const attr of _attrList) {
    const editRender: Record<string, any> = {
      name: 'input',
      enabled: !attr.is_computed && !attr.sys_computed,
    }
    switch (attr.value_type) {
      case '0':
        editRender['props'] = { type: 'float' }
        break
      case '1':
        editRender['props'] = { type: 'float' }
        break
      case '2':
        if (attr.is_file) {
          editRender.enabled = false
          // File fields are managed via the CiFileField dialog — inline editing not applicable
        } else {
          editRender['attrs'] = { type: 'text' }
        }
        break
      case '3':
        editRender['props'] = { type: 'datetime' }
        break
      case '4':
        editRender['props'] = { type: 'date' }
        break
      case '5':
        editRender['props'] = { type: 'time' }
        break
      case '6':
        editRender['props'] = { type: 'text' }
        break
      default:
        editRender['props'] = { type: 'text' }
        break
    }

    if (attr.is_choice) {
      editRender.name = '$select'
      editRender.options = attr.choice_value
        ? attr.choice_value.map((item: any) => ({ label: item, value: item }))
        : []
      delete editRender.props
    }

    let title = attr.alias || attr.name
    let sortable = !!attr.is_sortable
    let attr_id = attr.id

    if ([CI_DEFAULT_ATTR.UPDATE_TIME, CI_DEFAULT_ATTR.UPDATE_USER].includes(attr.name)) {
      editRender.enabled = false
      attr_id = attr.name

      switch (attr.name) {
        case CI_DEFAULT_ATTR.UPDATE_USER:
          title = i18n.global.t('cmdb.components.updater')
          break
        case CI_DEFAULT_ATTR.UPDATE_TIME:
          title = i18n.global.t('cmdb.components.updateTime')
          sortable = true
          break
        default:
          break
      }
    }

    columns.push({
      attr_id,
      editRender,
      title,
      field: attr.name,
      value_type: attr.value_type,
      sortable,
      filters: attr.is_choice ? attr.choice_value : null,
      choice_builtin: null,
      width: Math.min(Math.max(100, ...data.map((item) => strLength(item[attr.name]))), 350),
      is_link: attr.is_link,
      is_password: attr.is_password,
      is_list: attr.is_list,
      is_file: attr.is_file,
      is_choice: attr.is_choice,
      is_fixed: attr.is_fixed,
      is_bool: attr.is_bool,
      is_reference: attr.is_reference,
      is_index: attr.is_index,
      reference_type_id: attr.reference_type_id,
    })
  }

  const totalWidth = sum(columns.map((col) => col.width))
  if (totalWidth < width) {
    columns.forEach((item) => {
      delete item.width
    })
  }
  return columns
}
