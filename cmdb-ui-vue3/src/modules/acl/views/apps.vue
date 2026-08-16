<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useI18n } from 'vue-i18n'
import { EditOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import { searchApp, deleteApp } from '@/modules/acl/api/app'
import AppForm from './module/appForm.vue'

interface AppItem {
  id: number
  name: string
  description?: string
}

const { t } = useI18n()

const apps = ref<AppItem[]>([])
const appFormRef = ref<{ open: (ele?: AppItem) => void }>()

function loadApps() {
  searchApp().then((res) => {
    const data = res as unknown as { apps: AppItem[] }
    apps.value = data.apps || []
  })
}

function handleCreateApp() {
  appFormRef.value?.open()
}

function handleEditApp(app: AppItem) {
  appFormRef.value?.open(app)
}

function handleDeleteApp(app: AppItem) {
  Modal.confirm({
    title: t('acl.danger'),
    content: t('acl.confirmDeleteApp'),
    onOk() {
      return deleteApp(app.id).then(() => {
        message.success(t('deleteSuccess'))
        loadApps()
      })
    },
  })
}

onMounted(loadApps)
</script>

<template>
  <div class="acl-apps">
    <a-row :gutter="[24, 24]">
      <a-col v-for="app in apps" :key="app.id" :xxl="4" :xl="6" :md="8" :sm="12" :xs="24">
        <a-card>
          <a-card-meta :title="app.name">
            <template #avatar>
              <a-avatar style="background-color: #5dc2f1">{{ app.name ? app.name.charAt(0).toUpperCase() : '' }}</a-avatar>
            </template>
            <template #description>
              <div :title="app.description || ''">{{ app.description || t('acl.none') }}</div>
            </template>
          </a-card-meta>
          <template #actions>
            <EditOutlined @click="handleEditApp(app)" />
            <DeleteOutlined @click="handleDeleteApp(app)" />
          </template>
        </a-card>
      </a-col>
      <a-col :xxl="4" :xl="6" :md="8" :sm="12" :xs="24">
        <div class="acl-apps-add" @click="handleCreateApp">
          <span class="acl-apps-add-icon">+</span>
        </div>
      </a-col>
    </a-row>
    <app-form ref="appFormRef" @refresh="loadApps" />
  </div>
</template>

<style scoped>
.acl-apps .ant-card-meta-description > div {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.acl-apps .acl-apps-add {
  width: 100%;
  height: 141px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  border: 1px #e8e8e8 solid;
  background-color: #fff;
}
.acl-apps .acl-apps-add-icon {
  font-size: 70px;
  display: block;
  text-align: center;
  color: #5dc2f1;
  cursor: pointer;
}
</style>
