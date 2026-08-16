<script setup lang="ts">
import { computed, type Component } from 'vue'
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
import { COLOR_PRIMARY } from '@/theme/tokens'

interface ValueTypeAttr {
  value_type?: string | number
  is_file?: boolean
  is_password?: boolean
  is_link?: boolean
  is_index?: boolean
  is_bool?: boolean
  is_reference?: boolean
}

const props = withDefaults(defineProps<{ attr?: ValueTypeAttr }>(), { attr: () => ({}) })

/**
 * Map a CI attribute's value_type (plus its flags) to a representative
 * Ant Design icon. Mirrors the legacy `ops-icon` iconfont selection logic.
 */
function getPropertyIcon(attr: ValueTypeAttr): Component | null {
  let valueType = String(attr.value_type ?? '')

  if (valueType === '2') {
    if (attr.is_file) {
      valueType = '12'
    } else if (attr.is_password) {
      valueType = '7'
    } else if (attr.is_link) {
      valueType = '8'
    } else if (!attr.is_index) {
      valueType = '9'
    }
  }

  if (valueType === '7' && attr.is_bool) {
    valueType = '10'
  }

  if (valueType === '0' && attr.is_reference) {
    valueType = '11'
  }

  switch (valueType) {
    case '0':
      return FieldNumberOutlined
    case '1':
      return NumberOutlined
    case '2':
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
      return LockOutlined
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

const icon = computed<Component | null>(() => getPropertyIcon(props.attr))
</script>

<template>
  <span class="value-type-icon">
    <component :is="icon" v-if="icon" />
  </span>
</template>

<style scoped>
.value-type-icon {
  color: v-bind(COLOR_PRIMARY);
}
</style>
