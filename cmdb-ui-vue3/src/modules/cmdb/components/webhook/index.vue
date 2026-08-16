<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import Treeselect from 'vue3-treeselect'
import 'vue3-treeselect/dist/vue3-treeselect.css'
import { uuidv4 } from '@/utils/uuid'
import Parameters from './paramaters.vue'
import Body from './body.vue'
import Header from './header.vue'
import Authorization from './authorization.vue'

interface MethodOption {
  id: string
  label: string
}

const { t } = useI18n()

const methodList: MethodOption[] = [
  { id: 'GET', label: 'GET' },
  { id: 'POST', label: 'POST' },
  { id: 'PUT', label: 'PUT' },
  { id: 'DELETE', label: 'DELETE' },
]

const method = ref('GET')
const url = ref('')

// Internal sub-components are exposed via defineExpose with refs that are
// unwrapped at runtime (proxyRefs); typing them as `any` keeps this contract
// simple while the components remain fully functional.
const parametersRef = ref<any>()
const bodyRef = ref<any>()
const headerRef = ref<any>()
const authorizationRef = ref<any>()

function cloneDeep<T>(value: T): T {
  return JSON.parse(JSON.stringify(value))
}

function getParams() {
  const parameters: Record<string, string> = {}
  parametersRef.value?.parameters.forEach((item: any) => {
    parameters[item.key] = item.value
  })

  let body: any = bodyRef.value?.jsonData
  try {
    JSON.parse(body)
    body = JSON.parse(body)
  } catch {
    // keep body as a string when it is not valid JSON
  }

  const headers: Record<string, string> = {}
  headerRef.value?.headers.forEach((item: any) => {
    if (item.key) {
      headers[item.key] = item.value
    }
  })

  let authorization: Record<string, any> = {}
  const auth = authorizationRef.value
  const type = auth?.authorizationType
  if (type !== 'none') {
    if (type === 'OAuth2.0') {
      authorization = { ...auth?.OAuth2, type }
    } else {
      authorization = { ...(auth?.[type] ?? {}), type }
    }
  }

  return { method: method.value, url: url.value, parameters, body, headers, authorization }
}

function setParams(params?: {
  method?: string
  url?: string
  parameters?: Record<string, any>
  body?: any
  headers?: Record<string, any>
  authorization?: Record<string, any>
}) {
  const {
    method: m = 'GET',
    url: u = '',
    parameters = {},
    body = '',
    headers = {},
    authorization = {},
  } = params ?? {}

  method.value = m
  url.value = u

  parametersRef.value!.parameters =
    Object.keys(parameters).map((key) => ({
      id: uuidv4(),
      key,
      value: parameters[key],
    })) || []

  if (body && Object.prototype.toString.call(body) === '[object Object]') {
    bodyRef.value!.jsonData = JSON.stringify(body)
  } else {
    bodyRef.value!.jsonData = body
  }

  headerRef.value!.headers =
    Object.keys(headers).map((key) => ({
      id: uuidv4(),
      key,
      value: headers[key],
    })) || []

  const { type = 'none' } = authorization
  const auth = authorizationRef.value!
  auth.authorizationType = type
  if (type !== 'none') {
    const authData = cloneDeep(authorization)
    delete authData.type
    if (type === 'OAuth2.0') {
      Object.assign(auth.OAuth2, authData)
    } else {
      Object.assign(auth[type], authData)
    }
  }
}

defineExpose({ getParams, setParams })
</script>

<template>
  <div>
    <a-input-group compact>
      <Treeselect
        v-model="method"
        :disable-branch-nodes="true"
        class="custom-treeselect custom-treeselect-white"
        :style="{
          '--custom-height': '30px',
          lineHeight: '30px',
          display: 'inline-block',
          width: '100px',
        }"
        :multiple="false"
        :clearable="false"
        searchable
        :options="methodList"
        value-consists-of="LEAF_PRIORITY"
        :placeholder="t('cmdb.components.selectMethods')"
      />
      <a-input v-model:value="url" :style="{ display: 'inline-block', width: 'calc(100% - 100px)' }" />
    </a-input-group>
    <a-tabs>
      <a-tab-pane key="Parameters" tab="Parameters">
        <Parameters ref="parametersRef" />
      </a-tab-pane>
      <a-tab-pane key="Body" tab="Body" force-render>
        <Body ref="bodyRef" />
      </a-tab-pane>
      <a-tab-pane key="Headers" tab="Headers" force-render>
        <Header ref="headerRef" />
      </a-tab-pane>
      <a-tab-pane key="Authorization" tab="Authorization" force-render>
        <Authorization ref="authorizationRef" />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>
