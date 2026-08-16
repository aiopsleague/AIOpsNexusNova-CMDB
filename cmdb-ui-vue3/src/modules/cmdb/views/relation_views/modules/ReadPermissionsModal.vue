<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { CaretDownOutlined, CaretUpOutlined } from '@ant-design/icons-vue'
import { ciTypeFilterPermissions } from '@/modules/cmdb/api/CIType'
import { searchRole } from '@/modules/acl/api/role'
import dataEmptyImg from '@/assets/data_empty.png'

const { t } = useI18n()

const visible = ref(false)
const filerPerimissions = ref<Record<string, any>>({})
const readCIIdFilterPermissions = ref<Array<{ name: string; rid: string }>>([])
const showAllReadCIIdFilterPermissions = ref(false)
const allRoles = ref<any[]>([])

async function loadRoles() {
  const res: any = await searchRole({ page_size: 9999, app_id: 'cmdb', is_all: true })
  allRoles.value = res.roles
}

async function open(treeKey: string) {
  visible.value = true
  const _splitTreeKey = treeKey.split('@^@').filter((item) => !!item)
  const _treeKey = _splitTreeKey.slice(_splitTreeKey.length - 1, _splitTreeKey.length)[0].split('%')

  const typeId = _treeKey[1]
  const _treeKeyPath = _splitTreeKey.map((item) => item.split('%')[0]).join(',')
  await ciTypeFilterPermissions(typeId).then((res) => {
    filerPerimissions.value = res
  })
  const nextReadCIIdFilterPermissions: Array<{ name: string; rid: string }> = []
  Object.entries(filerPerimissions.value).forEach(([k, v]) => {
    const { id_filter } = v
    if (id_filter && Object.keys(id_filter).includes(_treeKeyPath)) {
      const _find = allRoles.value.find((item) => item.id === Number(k))
      nextReadCIIdFilterPermissions.push({ name: _find?.name ?? k, rid: k })
    }
  })
  readCIIdFilterPermissions.value = nextReadCIIdFilterPermissions
}

function handleCancel() {
  showAllReadCIIdFilterPermissions.value = false
  visible.value = false
}

onMounted(() => {
  loadRoles()
})

defineExpose({ open })
</script>

<template>
  <a-modal
    width="600px"
    :body-style="{ paddingTop: 0 }"
    :open="visible"
    :footer="null"
    :title="t('view')"
    @cancel="handleCancel"
  >
    <div>
      <template v-if="readCIIdFilterPermissions && readCIIdFilterPermissions.length">
        <p>
          <strong>{{ t('cmdb.serviceTree.idAuthorizationPolicy') }}</strong>
          <a
            v-if="readCIIdFilterPermissions.length > 10"
            @click="showAllReadCIIdFilterPermissions = !showAllReadCIIdFilterPermissions"
          >
            <CaretDownOutlined v-if="showAllReadCIIdFilterPermissions" />
            <CaretUpOutlined v-else />
          </a>
        </p>
        <a-tag
          v-for="item in showAllReadCIIdFilterPermissions
            ? readCIIdFilterPermissions
            : readCIIdFilterPermissions.slice(0, 10)"
          :key="item.name"
          color="blue"
          :style="{ marginBottom: '5px' }"
        >
          {{ item.name }}
        </a-tag>
        <a-tag
          v-if="readCIIdFilterPermissions.length > 10 && !showAllReadCIIdFilterPermissions"
          :style="{ marginBottom: '5px' }"
        >
          +{{ readCIIdFilterPermissions.length - 10 }}
        </a-tag>
      </template>
      <a-empty v-else>
        <template #image>
          <img :src="dataEmptyImg" />
        </template>
        <template #description>
          <span>{{ t('noData') }}</span>
        </template>
      </a-empty>
    </div>
  </a-modal>
</template>

<style></style>
