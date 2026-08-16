<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function backHome() {
  router.push('/')
}
</script>

<template>
  <a-result status="404" title="404" sub-title="Page not found">
    <template #extra>
      <a-button type="primary" @click="backHome">Back Home</a-button>
    </template>
  </a-result>
</template>
