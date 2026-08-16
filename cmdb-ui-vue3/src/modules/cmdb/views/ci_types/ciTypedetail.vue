<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, nextTick, ref } from 'vue'
import { message } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { TableOutlined } from '@ant-design/icons-vue'
import AttributesTable from './attributesTable.vue'
import GrantComp from '../../components/cmdbGrant/grantComp.vue'

const ACTIVE_KEY_STORAGE_KEY = 'ops_model_config_tab_key'

const props = withDefaults(
  defineProps<{
    CITypeId?: number | null
    CITypeName?: string
    preferenceData?: Record<string, any>
  }>(),
  { CITypeId: null, CITypeName: '', preferenceData: () => ({}) }
)

const { t } = useI18n()

const activeKey = ref(localStorage.getItem(ACTIVE_KEY_STORAGE_KEY) || '1')

const attributesTableRef = ref<{ getCITypeGroupData: () => void }>()

const windowHeight = computed(() => window.innerHeight)

function changeTab(key: string) {
  activeKey.value = key
  localStorage.setItem(ACTIVE_KEY_STORAGE_KEY, key)
  nextTick(() => {
    switch (key) {
      case '1':
        attributesTableRef.value?.getCITypeGroupData()
        break
      case '5':
        // TODO: wire up <TriggerTable> once migrated.
        break
      default:
        break
    }
  })
}

function jumpResourceView() {
  const isSub = props.preferenceData?.type_ids?.includes(props.CITypeId)

  if (!isSub) {
    message.error(t('cmdb.ciType.resourceViewTip'))
    return
  }
  localStorage.setItem('ops_ci_typeid', String(props.CITypeId))
  window.open('/cmdb/instances/types', '_blank')
}
</script>

<template>
<!-- eslint-disable vue/attribute-hyphenation -->
  <a-card :bordered="false" :body-style="{ padding: '0' }">
    <a-tabs v-model:active-key="activeKey" class="ops-tab" @change="changeTab">
      <a-tab-pane key="1" :tab="t('cmdb.ciType.attributes')">
        <AttributesTable ref="attributesTableRef" :CITypeId="CITypeId" :CITypeName="CITypeName" />
      </a-tab-pane>
      <a-tab-pane key="2" :tab="t('cmdb.ciType.relation')">
        <!-- TODO: wire up <RelationTable> once migrated -->
        <div v-if="activeKey === '2'" />
      </a-tab-pane>
      <a-tab-pane key="3" :tab="t('cmdb.ciType.autoDiscoveryTab')">
        <!-- TODO: wire up <ADTab> once migrated -->
        <div v-if="activeKey === '3'" />
      </a-tab-pane>
      <a-tab-pane key="5" :tab="t('cmdb.ciType.trigger')">
        <!-- TODO: wire up <TriggerTable> once migrated -->
        <div />
      </a-tab-pane>
      <a-tab-pane key="oneterm">
        <template #tab>
          <div class="oneterm-sync-tab-title">
            <span>{{ t('cmdb.ciType.onetermSyncTab') }}</span>
            <span class="oneterm-sync-tab-title-pro">Pro</span>
          </div>
        </template>
        <!-- TODO: wire up <OnetermSyncTab> once migrated -->
        <div v-if="activeKey === 'oneterm'" />
      </a-tab-pane>
      <a-tab-pane key="6" :tab="t('cmdb.ciType.grant')">
        <div
          v-if="activeKey === '6'"
          class="grant-config-wrap"
          :style="{ maxHeight: `${windowHeight - 150}px` }"
        >
          <GrantComp :CITypeId="CITypeId" resource-type="CIType" :resource-type-name="CITypeName" />
          <div class="citype-detail-title">{{ t('cmdb.components.relationGrant') }}</div>
          <!-- TODO: wire up <RelationTable isInGrantComp> once migrated -->
        </div>
      </a-tab-pane>

      <template #rightExtra>
        <a-button type="primary" ghost size="small" class="ops-button-ghost ops-tab-button" @click="jumpResourceView">
          <template #icon><TableOutlined /></template>
          {{ t('cmdb.menu.ciTable') }}
        </a-button>
      </template>
    </a-tabs>
  </a-card>
</template>

<style lang="less" scoped>
.citype-detail-title {
  border-left: 4px solid @primary-color;
  padding-left: 10px;
  margin-left: 20px;
  margin-bottom: 10px;
}
.grant-config-wrap {
  overflow: auto;
}

.ops-tab.ant-tabs {
  :deep(.ant-tabs-nav) {
    .ant-tabs-tab:hover {
      color: @primary-color;
    }
  }

  .oneterm-sync-tab-title {
    display: flex;
    align-items: center;
    column-gap: 4px;

    &-pro {
      background-color: #e1efff;
      color: #2f54eb;
      font-size: 12px;
      font-weight: 400;
      padding: 0 3px;
    }
  }

  .ops-tab-button {
    margin: 0px 12px;
  }
}
</style>
