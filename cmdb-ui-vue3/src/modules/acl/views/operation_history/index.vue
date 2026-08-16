<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <div style="padding: 24px">{{ t('acl.history') }} — Operation History</div>
</template>
