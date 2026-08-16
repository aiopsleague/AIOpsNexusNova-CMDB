<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, inject, type Component } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import {
  CheckSquareOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  PlusOutlined,
  RedoOutlined,
  SearchOutlined,
  SortAscendingOutlined,
  SyncOutlined,
  ThunderboltOutlined,
  UnorderedListOutlined,
} from '@ant-design/icons-vue'
import ValueTypeIcon from '@/components/CMDBValueTypeMapIcon/index.vue'
import { deleteCITypeAttributesById, deleteAttributesById, calcComputedAttribute } from '@/modules/cmdb/api/CITypeAttr'
import { updateCIType } from '@/modules/cmdb/api/CIType'
import { getPropertyType, valueTypeMap } from '../../utils/helper'

interface AttributeProperty {
  id?: number
  name?: string
  alias?: string
  inherited?: boolean
  inherited_from?: string
  value_type?: string
  is_required?: boolean
  default_show?: boolean
  is_unique?: boolean
  is_choice?: boolean
  is_sortable?: boolean
  is_index?: boolean
  is_dynamic?: boolean
  is_computed?: boolean
  is_password?: boolean
  is_list?: boolean
  is_reference?: boolean
  is_bool?: boolean
  choice_value?: unknown[]
  [key: string]: any
}

const props = withDefaults(
  defineProps<{
    property?: AttributeProperty
    CITypeId?: number | null
    isStore?: boolean
    attributes?: AttributeProperty[]
    isAdd?: boolean
  }>(),
  { property: () => ({}), CITypeId: null, isStore: false, attributes: () => [], isAdd: false }
)

const emit = defineEmits<{ (e: 'add'): void; (e: 'edit'): void; (e: 'ok'): void }>()

const { t } = useI18n()

const unique = inject<() => string | undefined>('unique', () => undefined)
const showId = inject<() => number | undefined>('show_id', () => undefined)

const isUnique = computed(() => {
  const uniqueVal = unique()
  if (uniqueVal) return props.property?.name === uniqueVal
  return false
})

const isShowId = computed(() => {
  const show = showId()
  if (show) return props.property?.id === show
  return false
})

const valueTypeMapLabels = computed(() => valueTypeMap())

const inherited = computed(() => props.property?.inherited || false)

const typeClass = computed(() => {
  if (props.isAdd) return ''
  const type = getPropertyType(props.property || {})
  return type ? `attribute-card-type-${type}` : ''
})

interface PropertyItem {
  label: string
  property: keyof AttributeProperty
  icon: Component
}

const propertyList = computed<PropertyItem[]>(() => [
  { label: t('cmdb.ciType.isUnique'), property: 'is_unique', icon: CheckSquareOutlined },
  { label: t('cmdb.ciType.isChoice'), property: 'is_choice', icon: UnorderedListOutlined },
  { label: t('cmdb.ciType.defaultShow'), property: 'default_show', icon: EyeOutlined },
  { label: t('cmdb.ciType.isSortable'), property: 'is_sortable', icon: SortAscendingOutlined },
  { label: t('cmdb.ciType.isIndex'), property: 'is_index', icon: SearchOutlined },
  { label: t('cmdb.ciType.isDynamic'), property: 'is_dynamic', icon: SyncOutlined },
])

const activePropertyList = computed(() => propertyList.value.filter((p) => !!props.property?.[p.property]))

function handleEdit() {
  emit('edit')
}

function handleDelete() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmDelete', { name: `${props.property?.alias || props.property?.name}` }),
    onOk() {
      if (props.isStore) {
        deleteAttributesById(props.property?.id as number).then(() => {
          message.success(t('deleteSuccess'))
          emit('ok')
        })
      } else {
        deleteCITypeAttributesById(props.CITypeId as number, {
          attr_id: [props.property?.id],
        }).then(() => {
          message.success(t('deleteSuccess'))
          emit('ok')
        })
      }
    },
  })
}

// TODO: wire up <TriggerForm> once migrated.
function openTrigger() {
  // this.$refs.triggerForm.open(this.property, this.attributes)
}

function handleCalcComputed() {
  Modal.confirm({
    title: t('warning'),
    content: t('cmdb.ciType.confirmcomputeForAllCITips'),
    onOk() {
      calcComputedAttribute(props.property?.id as number).then(() => {
        message.success(t('cmdb.ciType.computeSuccess'))
      })
    },
  })
}

function setAsShow() {
  updateCIType(props.CITypeId as number, {
    show_id: isShowId.value ? null : props.property?.id,
  }).then(() => {
    emit('ok')
  })
}
</script>

<template>
  <div
    :class="['attribute-card', { 'attribute-card-add': isAdd, 'attribute-card-inherited': inherited }, typeClass]"
    @click="
      () => {
        if (isAdd) {
          emit('add')
        }
      }
    "
  >
    <div v-if="isUnique" class="attribute-card-uniqueKey">{{ t('cmdb.ciType.uniqueKey') }}</div>
    <div v-if="isShowId" class="attribute-card-uniqueKey">{{ t('cmdb.ciType.show') }}</div>
    <template v-if="!isAdd">
      <a-tooltip :title="inherited ? t('cmdb.ciType.inheritFrom', { name: property.inherited_from }) : ''">
        <div class="attribute-card-content">
          <div :class="{ 'attribute-card-value-type-icon': true, handle: !inherited }">
            <ValueTypeIcon :attr="property" />
          </div>
          <div :class="{ 'attribute-card-content-inner': true, 'attribute-card-name-required': property.is_required }">
            <div :class="{ 'attribute-card-name': true, 'attribute-card-name-default-show': property.default_show }">
              {{ property.alias || property.name }}
            </div>
            <div class="attribute-card_value-type">{{ valueTypeMapLabels[getPropertyType(property)] }}</div>
          </div>
          <div
            v-if="(property.value_type === '3' || property.value_type === '4') && !isStore"
            class="attribute-card-trigger"
            :style="{ top: isShowId ? '18px' : '' }"
          >
            <a @click="openTrigger"><ThunderboltOutlined /></a>
          </div>
        </div>
      </a-tooltip>

      <div class="attribute-card-footer">
        <a-popover
          trigger="click"
          :arrow-point-at-center="true"
          placement="bottom"
          overlay-class-name="attribute-card-footer-popover"
        >
          <template #content>
            <h3 :style="{ textAlign: 'center', paddingTop: '0.5em' }">
              <span>{{ property.alias }}({{ property.name }})</span>
            </h3>
            <a-descriptions layout="horizontal" bordered size="small" :column="2">
              <a-descriptions-item v-for="item in propertyList" :key="item.property" :label="item.label">
                <component
                  :is="item.icon"
                  :class="['attribute-card-footer-icon', property[item.property] ? 'attribute-card-footer-icon-mark' : '']"
                />
              </a-descriptions-item>
              <a-descriptions-item label=""></a-descriptions-item>
            </a-descriptions>
          </template>
          <a-space :style="{ cursor: 'pointer' }">
            <component
              :is="item.icon"
              v-for="item in activePropertyList"
              :key="item.property"
              class="attribute-card-footer-icon attribute-card-footer-icon-mark"
            />
          </a-space>
        </a-popover>

        <a-space class="attribute-card-operation">
          <a v-if="!isStore && !inherited"><EditOutlined @click="handleEdit" /></a>
          <a-tooltip
            v-if="
              !isStore &&
                !isUnique &&
                !['6'].includes(property.value_type as string) &&
                !property.is_password &&
                !property.is_list &&
                !property.is_reference &&
                !property.is_bool &&
                !(Array.isArray(property.choice_value) ? property.choice_value.length > 0 : false)
            "
            :title="t(isShowId ? 'cmdb.ciType.cancelSetAsShow' : 'cmdb.ciType.setAsShow')"
          >
            <a><EyeOutlined @click="setAsShow" /></a>
          </a-tooltip>
          <a-tooltip v-if="!isStore && property.is_computed" :title="t('cmdb.ciType.computeForAllCITips')">
            <a><RedoOutlined @click="handleCalcComputed" /></a>
          </a-tooltip>
          <a v-if="!isUnique && !inherited" style="color: red"><DeleteOutlined @click="handleDelete" /></a>
        </a-space>
      </div>
      <!-- TODO: wire up <TriggerForm> once migrated -->
    </template>
    <template v-else>
      <a><PlusOutlined /></a>
      <div>{{ t('cmdb.ciType.addAttribute') }}</div>
    </template>
  </div>
</template>

<style lang="less" scoped>
.attribute-card {
  width: 172px;
  height: 75px;
  background-color: @primary-color_6;
  border-radius: 2px;
  position: relative;
  margin-bottom: 16px;
  transition: all 0.3s;
  &:hover {
    box-shadow: 0 4px 12px @primary-color_8;
    .attribute-card-operation {
      visibility: visible !important;
    }
  }
  .attribute-card-content {
    height: 50px;
    display: inline-flex;
    align-items: center;
    padding: 8px;
    width: 100%;
    .attribute-card-value-type-icon {
      width: 32px;
      height: 32px;
      font-size: 16px;
      background: var(--ops-value-type-icon-bg, #ffffff) !important;
      box-shadow: 0px 1px 2px rgba(47, 84, 235, 0.2);
      border-radius: 2px;
      text-align: center;
      line-height: 32px;
    }
    .handle {
      cursor: move;
    }
    .attribute-card-content-inner {
      padding-left: 12px;
      font-weight: 400;
      font-size: 12px;
      width: 120px;
      position: relative;
      .attribute-card-name {
        width: 100%;
        color: rgba(0, 0, 0, 0.8);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .attribute-card-name-default-show {
        color: @primary-color;
      }
      .attribute-card_value-type {
        font-size: 10px;
        color: rgba(0, 0, 0, 0.35);
      }
    }
    .attribute-card-name-required::before {
      content: '*';
      width: 5px;
      color: red;
      position: absolute;
      left: 3px;
    }
    .attribute-card-trigger {
      position: absolute;
      right: 8px;
      top: 8px;
    }
  }
  .attribute-card-footer {
    width: 172px;
    height: 30px;
    padding: 0 8px;
    position: absolute;
    bottom: 0;
    left: 0;
    background: @primary-color_5;
    border-radius: 0px 0px 2px 2px;
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    border-top: 1px solid @primary-color_3;
    .attribute-card-operation {
      visibility: hidden;
    }
  }
  .attribute-card-uniqueKey {
    position: absolute;
    right: -12px;
    top: 0;
    color: #fff;
    background-color: @func-color_2;
    font-size: 10px;
    z-index: 1;
    border-radius: 0 0 0 4px;
    min-width: 55px;
    padding: 2px 0 2px 5px;
  }
}

.attribute-card-footer-icon {
  font-size: 10px;

  &-mark {
    color: @primary-color_2;
  }
}

.attribute-card-inherited {
  background: @primary-color_7;
  .attribute-card-footer {
    background: @text-color_7;
  }
}

.attribute-card-add {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  position: relative;
  background-color: inherit !important;
  &:hover {
    box-shadow: none !important;
    background-color: @primary-color_6 !important;
  }
  &:after {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    left: 0;
    z-index: 1;
    background: linear-gradient(90deg, @text-color_5 50%, transparent 0) repeat-x,
      linear-gradient(90deg, @text-color_5 50%, transparent 0) repeat-x,
      linear-gradient(0deg, @text-color_5 50%, transparent 0) repeat-y,
      linear-gradient(0deg, @text-color_5 50%, transparent 0) repeat-y;
    background-size: 15px 1px, 15px 1px, 1px 15px, 1px 15px;
    background-position: 0 0, 0 100%, 0 0, 100% 0;
  }
  div {
    color: @text-color_4;
    font-size: 12px;
  }
}
</style>
<style lang="less">
.attribute-card-footer-popover {
  .ant-popover-inner-content {
    padding: 0;
  }
  .ant-descriptions-bordered .ant-descriptions-item-label {
    background-color: #f8faff;
  }
}
</style>
