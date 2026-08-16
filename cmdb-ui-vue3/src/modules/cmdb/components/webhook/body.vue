<script setup lang="ts">
import { ref } from 'vue'
import MonacoCodeEditor from '@/components/MonacoCodeEditor/index.vue'

const jsonData = ref('')

defineExpose({ jsonData })
</script>

<template>
  <div class="body-wrapper">
    <MonacoCodeEditor v-model:value="jsonData" language="json" :height="200" storage-key="cmdbWebhookBodyEditor" />
  </div>
</template>
