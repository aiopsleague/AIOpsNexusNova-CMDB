<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RightOutlined, LeftOutlined } from '@ant-design/icons-vue'
import { searchRole } from '@/modules/acl/api/role'

const props = withDefaults(
  defineProps<{
    height?: number
    app_id: string
  }>(),
  {
    height: 260,
  }
)

const { t } = useI18n()

const isUserRole = ref(false)
const allRoles = ref<any[]>([])
const rightData = ref<any[]>([])
const selectedLeft = ref<any[]>([])
const selectedRight = ref<any[]>([])
const searchValue = ref('')

const filterAllRoles = computed(() => {
  if (searchValue.value) {
    return allRoles.value.filter((item) =>
      item.name.toLowerCase().includes(searchValue.value.toLowerCase())
    )
  }
  return allRoles.value
})

function loadRoles() {
  searchRole({ page_size: 9999, app_id: props.app_id, user_role: Number(isUserRole.value) }).then(
    (res: any) => {
      allRoles.value = res.roles
    }
  )
}

function handleRight() {
  rightData.value = [...new Set([...selectedLeft.value, ...rightData.value])]
  selectedLeft.value = []
  selectedRight.value = []
}

function handleLeft() {
  selectedRight.value.forEach((id) => {
    const idx = rightData.value.findIndex((item) => item === id)
    if (idx > -1) {
      rightData.value.splice(idx, 1)
    }
  })
  selectedRight.value = []
}

function handleSelectedLeft(id: any) {
  const idx = selectedLeft.value.findIndex((item) => item === id)
  if (idx > -1) {
    selectedLeft.value.splice(idx, 1)
  } else {
    selectedLeft.value.push(id)
  }
}

function handleSelectedRight(id: any) {
  const idx = selectedRight.value.findIndex((item) => item === id)
  if (idx > -1) {
    selectedRight.value.splice(idx, 1)
  } else {
    selectedRight.value.push(id)
  }
}

function getLabel(id: any) {
  const found = allRoles.value.find((item) => item.id === id)
  return found?.name
}

function getValues() {
  return rightData.value.map((right) => {
    const found = allRoles.value.find((item) => item.id === right)
    return {
      id: right,
      name: found?.name ?? right,
    }
  })
}

onMounted(loadRoles)

defineExpose({ getValues })
</script>

<template>
  <div class="role-transfer" :style="{ height: `${height}px` }">
    <a-switch
      v-model:checked="isUserRole"
      class="role-transfer-switch"
      :checked-children="t('user')"
      :un-checked-children="t('visual')"
      @change="loadRoles"
    />
    <div class="role-transfer-left">
      <a-input v-model:value="searchValue" :placeholder="t('placeholderSearch')" />
      <div v-for="item in filterAllRoles" :key="item.id" @click="handleSelectedLeft(item.id)">
        <a-checkbox :checked="selectedLeft.includes(item.id)" />
        <div :title="item.name" class="role-transfer-left-role">{{ item.name }}</div>
      </div>
    </div>
    <div class="role-transfer-operation">
      <div class="operation-right" @click="handleRight"><RightOutlined /></div>
      <br />
      <div class="operation-left" @click="handleLeft"><LeftOutlined /></div>
    </div>
    <div class="role-transfer-right">
      <div
        v-for="right in rightData"
        :key="right"
        :class="{
          'role-transfer-right-item': true,
          'role-transfer-right-selected': selectedRight.includes(right),
        }"
        @click="handleSelectedRight(right)"
      >
        {{ getLabel(right) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.role-transfer {
  display: flex;
  justify-content: space-between;
  position: relative;
}
.role-transfer-switch {
  position: absolute;
  top: -30px;
  left: 0;
}
.role-transfer-left,
.role-transfer-right {
  width: 40%;
  background-color: #f9fbff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  overflow: auto;
}
.role-transfer-left {
  padding: 12px;
}
.role-transfer-left > div {
  display: flex;
  align-items: center;
  height: 30px;
}
.role-transfer-left-role {
  display: inline-block;
  margin-left: 12px;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  width: calc(100% - 30px);
  cursor: pointer;
}
.role-transfer-right {
  padding-top: 12px;
  overflow: auto;
}
.role-transfer-right-item {
  cursor: pointer;
  padding: 2px 12px;
  margin: 2px 0;
}
.role-transfer-right-selected {
  background-color: #f0f5ff;
}
.role-transfer-operation {
  width: 10%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.operation-left,
.operation-right {
  width: 20px;
  height: 20px;
  border-radius: 2px;
  background-color: #f0f5ff;
  color: #2f54eb;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}
.operation-left:hover,
.operation-right:hover {
  background-color: #2f54eb;
  color: #fff;
}
</style>
