<script setup lang="ts">
import { ref } from 'vue'
import { EyeInvisibleOutlined, EyeOutlined } from '@ant-design/icons-vue'

withDefaults(
  defineProps<{
    password?: string
  }>(),
  {
    password: '',
  }
)

const isShow = ref(false)
const showPassword = '******'

function switchPassword() {
  isShow.value = !isShow.value
}
</script>

<template>
  <div>
    <span v-if="!isShow">{{ showPassword }}</span>
    <span v-else>{{ password }}</span>
    <a class="password-eye" @click="switchPassword">
      <EyeInvisibleOutlined v-if="isShow" />
      <EyeOutlined v-else />
    </a>
  </div>
</template>

<style lang="less" scoped>
.password-eye {
  margin-left: 10px;
}
</style>
