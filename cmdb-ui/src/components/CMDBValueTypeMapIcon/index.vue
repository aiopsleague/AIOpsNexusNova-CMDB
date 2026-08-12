<template>
  <span class="value-type-icon">
    <ops-icon :type="getPropertyIcon(attr)" />
  </span>
</template>

<script>
export default {
  name: 'ValueTypeIcon',
  props: {
    attr: {
      type: Object,
      default: () => {},
    },
  },
  methods: {
    getPropertyIcon(attr) {
      let valueType = attr.value_type

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

      if (
        valueType === '7' &&
        attr.is_bool
      ) {
        valueType = '10'
      }

      if (
        valueType === '0' &&
        attr.is_reference
      ) {
        valueType = '11'
      }

      switch (valueType) {
        case '0':
          return 'icon-xianxing-shishu'
        case '1':
          return 'icon-xianxing-fudianshu'
        case '2':
          return 'icon-xianxing-wenben'
        case '3':
          return 'icon-xianxing-datetime'
        case '4':
          return 'icon-xianxing-date'
        case '5':
          return 'icon-xianxing-time'
        case '6':
          return 'icon-xianxing-json'
        case '7':
          return 'icon-xianxing-password'
        case '8':
          return 'icon-xianxing-link'
        case '9':
          return 'itsm-textarea'
        case '10':
          return 'icon-xianxing-queren'
        case '11':
          return 'icon-xianxing-yilianjie'
        case '12':
          return 'file'
        default:
          return ''
      }
    },
  },
}
</script>

<style scoped lang="less">
.value-type-icon {
  // single-color value-type icons inherit currentColor; light mode defaults to
  // the light theme primary blue (@primary-color); dark theme overrides to the
  // liquid-glass accent in src/style/themes/dark-overrides.less.
  color: @primary-color;
}
</style>
