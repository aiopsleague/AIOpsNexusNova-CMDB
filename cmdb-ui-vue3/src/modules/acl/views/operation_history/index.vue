<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import PermissionTable from './modules/permissionTable.vue'
import ResourceHistoryTable from './modules/resourceHistoryTable.vue'
import ResourceTypeHistoryTable from './modules/resourceTypeHistoryTable.vue'
import RoleHistoryTable from './modules/roleHistoryTable.vue'
import TriggerHistoryTable from './modules/triggerHistoryTable.vue'

const { t } = useI18n()
</script>

<template>
  <div class="acl-operation-history">
    <a-tabs default-active-key="1">
      <a-tab-pane key="1" :tab="t('acl.permissionChange')">
        <PermissionTable />
      </a-tab-pane>
      <a-tab-pane key="2" :tab="t('acl.roleChange')">
        <RoleHistoryTable />
      </a-tab-pane>
      <a-tab-pane key="3" :tab="t('acl.resourceChange')">
        <ResourceHistoryTable />
      </a-tab-pane>
      <a-tab-pane key="4" :tab="t('acl.resourceTypeChange')">
        <ResourceTypeHistoryTable />
      </a-tab-pane>
      <a-tab-pane key="5" :tab="t('acl.triggerChange')">
        <TriggerHistoryTable />
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<style scoped>
.acl-operation-history {
  border-radius: 4px;
  height: calc(100vh - 64px);
  margin-bottom: -24px;
  padding: 24px;
  background-color: #fff;
}
</style>
