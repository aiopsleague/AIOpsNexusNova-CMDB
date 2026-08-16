<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import emptyImg from '@/assets/data_empty.png'

const { t } = useI18n()

const authorizationType = ref('none')
const BasicAuth = reactive({
  username: '',
  password: '',
})
const Bearer = reactive({
  token: '',
})
const APIKey = reactive({
  key: '',
  value: '',
})
const OAuth2 = reactive({
  client_id: '',
  client_secret: '',
  authorization_base_url: '',
  token_url: '',
  redirect_url: '',
  scope: '',
})

defineExpose({ authorizationType, BasicAuth, Bearer, APIKey, OAuth2 })
</script>

<template>
  <div class="authorization-wrapper">
    <div class="authorization-header">
      <a-space>
        <span>Authorization Type</span>
        <a-select v-model:value="authorizationType" size="small" style="width: 200px" :show-search="true">
          <a-select-option value="none">None</a-select-option>
          <a-select-option value="BasicAuth">Basic Auth</a-select-option>
          <a-select-option value="Bearer">Bearer</a-select-option>
          <a-select-option value="APIKey">APIKey</a-select-option>
          <a-select-option value="OAuth2.0">OAuth2.0</a-select-option>
        </a-select>
      </a-space>
    </div>
    <div style="margin-top: 10px">
      <table v-if="authorizationType === 'BasicAuth'">
        <tr>
          <td><a-input v-model:value="BasicAuth.username" class="authorization-input" :placeholder="t('cmdb.ciType.username')" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="BasicAuth.password" class="authorization-input" :placeholder="t('cmdb.ciType.password')" /></td>
        </tr>
      </table>

      <table v-else-if="authorizationType === 'Bearer'">
        <tr>
          <td><a-input v-model:value="Bearer.token" class="authorization-input" placeholder="token" /></td>
        </tr>
      </table>

      <table v-else-if="authorizationType === 'APIKey'">
        <tr>
          <td><a-input v-model:value="APIKey.key" class="authorization-input" placeholder="key" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="APIKey.value" class="authorization-input" placeholder="value" /></td>
        </tr>
      </table>

      <table v-else-if="authorizationType === 'OAuth2.0'">
        <tr>
          <td><a-input v-model:value="OAuth2.client_id" class="authorization-input" placeholder="client_id" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="OAuth2.client_secret" class="authorization-input" placeholder="client_secret" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="OAuth2.authorization_base_url" class="authorization-input" placeholder="authorization_base_url" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="OAuth2.token_url" class="authorization-input" placeholder="token_url" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="OAuth2.redirect_url" class="authorization-input" placeholder="redirect_url" /></td>
        </tr>
        <tr>
          <td><a-input v-model:value="OAuth2.scope" class="authorization-input" placeholder="scope" /></td>
        </tr>
      </table>

      <a-empty v-else :image-style="{ height: '60px' }">
        <template #image><img :src="emptyImg" /></template>
        <template #description>{{ t('cmdb.components.noAuthRequest') }}</template>
      </a-empty>
    </div>
  </div>
</template>

<style scoped>
.authorization-wrapper table {
  width: 100%;
  border-collapse: collapse;
}
.authorization-wrapper table,
.authorization-wrapper td,
.authorization-wrapper th {
  border: 1px solid #f3f4f6;
}
.authorization-input {
  border: 1px solid transparent;
}
.authorization-input:focus {
  box-shadow: none;
  border-color: #2f54eb;
}
.authorization-input:hover {
  border-color: #2f54eb;
}
</style>
