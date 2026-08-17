<script setup lang="ts">
import { computed, type Component } from 'vue'
import {
  AppstoreOutlined,
  KeyOutlined,
  SearchOutlined,
  SolutionOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'

/**
 * Legacy `ops-icon` replacement.
 *
 * The custom iconfont (SVG-symbol mode, loaded from `/iconfont/iconfont.js` and
 * `/iconfont-extend/iconfont.js`) only contains `ops-*` / `veops-*` / `cmdb-*`
 * glyphs. A handful of route `meta.icon` values are plain Ant Design icon names
 * (used by the ACL module), so those are resolved to their
 * `@ant-design/icons-vue` counterparts here; everything else is rendered as an
 * iconfont `<use>` reference.
 */
const ANTD_ICON_MAP: Record<string, Component> = {
  appstore: AppstoreOutlined,
  key: KeyOutlined,
  search: SearchOutlined,
  solution: SolutionOutlined,
  team: TeamOutlined,
  user: UserOutlined,
}

const props = withDefaults(defineProps<{ type?: string }>(), { type: '' })

const antdIcon = computed<Component | null>(() => ANTD_ICON_MAP[props.type] ?? null)
</script>

<template>
  <component :is="antdIcon" v-if="antdIcon" />
  <svg v-else-if="type" class="ops-icon" aria-hidden="true">
    <use :href="`#${type}`" />
  </svg>
</template>

<style scoped>
.ops-icon {
  display: inline-block;
  width: 1em;
  height: 1em;
  fill: currentColor;
  vertical-align: -0.125em;
}
</style>
