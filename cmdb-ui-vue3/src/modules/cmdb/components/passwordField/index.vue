<script setup lang="ts">
/* eslint-disable vue/prop-name-casing */
import { computed, ref } from 'vue'
import { EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons-vue'
import { getAttrPassword } from '@/modules/cmdb/api/CITypeAttr'
import { useCmdbStore } from '@/modules/cmdb/store'

/**
 * Masked password attribute field. Shows `******` by default and reveals the
 * real value after fetching it from the backend once the eye icon is clicked.
 */
const props = withDefaults(
  defineProps<{
    ci_id?: number
    attr_id?: number
  }>(),
  {
    ci_id: 0,
    attr_id: 0,
  }
)

const cmdbStore = useCmdbStore()

const isTableLoading = computed(() => cmdbStore.isTableLoading)
const isShow = ref(false)
const password = ref('')
const showPassword = '******'

function getPassword() {
  if (isShow.value) {
    isShow.value = false
  } else {
    getAttrPassword(props.ci_id, props.attr_id).then((res) => {
      password.value = res.value
      isShow.value = true
    })
  }
}
</script>

<template>
  <div>
    <span v-if="!isShow && !isTableLoading">{{ showPassword }}</span>
    <span v-else>{{ password }}</span>
    <a :style="{ marginLeft: '10px' }" @click="getPassword">
      <EyeInvisibleOutlined v-if="isShow" />
      <EyeOutlined v-else />
    </a>
  </div>
</template>

<style></style>
