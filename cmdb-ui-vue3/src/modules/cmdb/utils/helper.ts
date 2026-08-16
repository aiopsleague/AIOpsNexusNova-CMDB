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
