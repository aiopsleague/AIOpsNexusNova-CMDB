<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ApartmentOutlined, InfoCircleOutlined, TeamOutlined, UserOutlined } from '@ant-design/icons-vue'
import UserFilterComp from './userFilterComp/index.vue'
import { BUILT_IN_TYPE, DISPLAY_VALUE_SELECT } from './constants'

const { t } = useI18n()

const formRef = ref()
const userFilterRef = ref<InstanceType<typeof UserFilterComp>>()

const activeKey = ref<string>(BUILT_IN_TYPE.DEPARTMENT)

const formModel = reactive<Record<string, any>>({
  cascade_display: false,
  display_value: 'nickname',
  user_group_key: undefined,
})

const rules = {
  display_value: [{ required: true, message: t('cmdb.ciType.displayValueSelectTip') }],
  user_group_key: [{ required: true, message: t('cmdb.ciType.userGroupSelectTip') }],
}

const formLayout = {
  labelCol: { span: 5 },
  wrapperCol: { span: 16 },
}

const tabList = [
  { key: BUILT_IN_TYPE.DEPARTMENT, title: 'cmdb.ciType.department', icon: ApartmentOutlined },
  { key: BUILT_IN_TYPE.USER, title: 'cmdb.ciType.user', icon: UserOutlined },
  { key: BUILT_IN_TYPE.USER_GROUP, title: 'cmdb.ciType.userGroup', icon: TeamOutlined },
]

// The user group list is intentionally empty in the legacy implementation (no
// source was ever wired up to populate it).
const userGroupList = ref<any[]>([])

function setData(data?: { builtin_type?: string; cascade_display?: boolean; display_value?: string; user_group_key?: string; filter_rule_list?: any[] }) {
  activeKey.value = data?.builtin_type || BUILT_IN_TYPE.DEPARTMENT

  nextTick(() => {
    formModel.cascade_display = data?.cascade_display ?? false
    formModel.display_value = data?.display_value ?? undefined
    formModel.user_group_key = data?.user_group_key ?? undefined
    userFilterRef.value?.setRuleList(data?.filter_rule_list || [])
  })
}

async function getData(): Promise<any> {
  const params: Record<string, any> = {}
  try {
    const values = await formRef.value?.validate()
    Object.assign(params, values, { builtin_type: activeKey.value })
    if (activeKey.value === BUILT_IN_TYPE.USER) {
      params.filter_rule_list = userFilterRef.value?.getRuleList() || []
    }
  } catch {
    params.isError = true
  }
  return params
}

function clickTab(key: string) {
  activeKey.value = key
}

defineExpose({ setData, getData })
</script>

<template>
  <div class="builtin">
    <div class="builtin-tab">
      <div
        v-for="item in tabList"
        :key="item.key"
        :class="['builtin-tab-item', activeKey === item.key ? 'builtin-tab-item_active' : '']"
        @click="clickTab(item.key)"
      >
        <component :is="item.icon" class="builtin-tab-item-icon" />
        <span class="builtin-tab-item-title">{{ t(item.title) }}</span>
      </div>
    </div>

    <div v-if="activeKey === BUILT_IN_TYPE.DEPARTMENT" class="builtin-department">
      <InfoCircleOutlined class="builtin-department-icon" />
      <span class="builtin-department-tip">{{ t('cmdb.ciType.departmentTip') }}</span>
    </div>

    <a-form
      ref="formRef"
      :model="formModel"
      :rules="rules"
      :label-col="formLayout.labelCol"
      :wrapper-col="formLayout.wrapperCol"
    >
      <div v-show="activeKey === BUILT_IN_TYPE.USER" class="builtin-user">
        <a-form-item :label="t('cmdb.ciType.filterUsers')">
          <UserFilterComp ref="userFilterRef" />
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.departmentCascadeDisplay')">
          <a-switch v-model:checked="formModel.cascade_display" />
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.displayValue')">
          <a-select
            v-model:value="formModel.display_value"
            class="builtin-select"
            show-search
            option-filter-prop="title"
            :placeholder="t('cmdb.ciType.displayValueSelectTip')"
          >
            <a-select-option
              v-for="item in DISPLAY_VALUE_SELECT"
              :key="item.value"
              :value="item.value"
              :title="t(item.label)"
            >
              {{ t(item.label) }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </div>

      <div v-if="activeKey === BUILT_IN_TYPE.USER_GROUP" class="builtin-usergroup">
        <a-form-item :label="t('cmdb.ciType.userGroup')">
          <a-select
            v-model:value="formModel.user_group_key"
            class="builtin-select"
            show-search
            option-filter-prop="title"
            :placeholder="t('cmdb.ciType.userGroupSelectTip')"
          >
            <a-select-option
              v-for="item in userGroupList"
              :key="item.group_id"
              :value="item.group_id"
              :title="item.group_name"
            >
              {{ item.group_name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item :label="t('cmdb.ciType.displayValue')">
          <a-select
            v-model:value="formModel.display_value"
            class="builtin-select"
            show-search
            option-filter-prop="title"
            :placeholder="t('cmdb.ciType.displayValueSelectTip')"
          >
            <a-select-option
              v-for="item in DISPLAY_VALUE_SELECT"
              :key="item.value"
              :value="item.value"
              :title="t(item.label)"
            >
              {{ t(item.label) }}
            </a-select-option>
          </a-select>
        </a-form-item>
      </div>
    </a-form>
  </div>
</template>

<style lang="less" scoped>
.builtin {
  width: 100%;

  &-tab {
    padding: 4px 80px 20px;
    display: flex;
    align-items: center;
    gap: 60px;

    &-item {
      display: flex;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      border: solid 1px #e4e7ed;
      border-radius: 2px;
      padding: 0 20px;
      min-width: 72px;
      height: 64px;
      cursor: pointer;

      &-icon {
        font-size: 20px;
        color: #a5a9bc;
      }

      &-title {
        font-size: 14px;
        font-weight: 400;
        line-height: 14px;
        margin-top: 4px;
      }

      &_active {
        border-color: #b1c9ff;

        .builtin-tab-item-icon {
          color: #7f97fa;
        }

        .builtin-tab-item-title {
          color: #2f54eb;
        }
      }
    }
  }

  &-department {
    display: flex;
    align-items: center;
    margin-left: 60px;

    &-icon {
      font-size: 12px;
      color: #a5a9bc;
    }

    &-tip {
      color: #4e5969;
      font-size: 14px;
      font-weight: 400;
      margin-left: 4px;
    }
  }

  &-select {
    width: 240px;
  }
}
</style>
