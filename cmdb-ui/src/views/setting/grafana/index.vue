<template>
  <div class="ops-setting-grafana">
    <a-card :title="$t('cs.grafana.connection')" :bordered="false" class="grafana-card">
      <a-button slot="extra" type="primary" @click="openConnectionModal()">
        {{ $t('cs.grafana.addConnection') }}
      </a-button>
      <a-table
        :columns="connectionColumns"
        :data-source="connections"
        :pagination="false"
        rowKey="id"
        size="small"
      >
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openConnectionModal(record)">{{ $t('cs.grafana.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteConnection(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.grafana.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-card :title="$t('cs.grafana.mapping')" :bordered="false" class="grafana-card">
      <a-button slot="extra" type="primary" @click="openMappingModal()">
        {{ $t('cs.grafana.addMapping') }}
      </a-button>
      <a-table
        :columns="mappingColumns"
        :data-source="mappings"
        :pagination="false"
        rowKey="id"
        size="small"
      >
        <template slot="ci_type" slot-scope="text, record">
          {{ ciTypeName(record.ci_type_id) }}
        </template>
        <template slot="connection" slot-scope="text, record">
          {{ connectionName(record.connection_id) }}
        </template>
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openMappingModal(record)">{{ $t('cs.grafana.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteMapping(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.grafana.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-modal
      :title="connectionForm.id ? $t('cs.grafana.editConnection') : $t('cs.grafana.addConnection')"
      :visible="connectionModalVisible"
      @cancel="connectionModalVisible = false"
    >
      <a-form-model ref="connectionForm" :model="connectionForm" :rules="connectionRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.grafana.name')" prop="name">
          <a-input v-model="connectionForm.name" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.url')" prop="url">
          <a-input v-model="connectionForm.url" placeholder="https://grafana.example.com" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.apiKey')" prop="api_key">
          <a-input-password v-model="connectionForm.api_key" :placeholder="connectionForm.id ? $t('cs.grafana.apiKeyKeepTip') : ''" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.remark')" prop="remark">
          <a-input v-model="connectionForm.remark" />
        </a-form-model-item>
      </a-form-model>
      <template slot="footer">
        <a-button :loading="testing" @click="handleTest">{{ $t('cs.grafana.testConnect') }}</a-button>
        <a-button @click="connectionModalVisible = false">{{ $t('cancel') }}</a-button>
        <a-button type="primary" :loading="saving" @click="handleSaveConnection">{{ $t('save') }}</a-button>
      </template>
    </a-modal>

    <a-modal
      :title="mappingForm.id ? $t('cs.grafana.editMapping') : $t('cs.grafana.addMapping')"
      :visible="mappingModalVisible"
      :confirm-loading="saving"
      @ok="handleSaveMapping"
      @cancel="mappingModalVisible = false"
    >
      <a-form-model ref="mappingForm" :model="mappingForm" :rules="mappingRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.grafana.ciType')" prop="ci_type_id">
          <a-select v-model="mappingForm.ci_type_id" show-search option-filter-prop="children">
            <a-select-option v-for="t in ciTypes" :key="t.id" :value="t.id">
              {{ t.alias || t.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.connectionInstance')" prop="connection_id">
          <a-select v-model="mappingForm.connection_id">
            <a-select-option v-for="c in connections" :key="c.id" :value="c.id">
              {{ c.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.dashboardUid')" prop="dashboard_uid">
          <a-input v-model="mappingForm.dashboard_uid" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.varName')" prop="var_name">
          <a-input v-model="mappingForm.var_name" placeholder="ci_name" />
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  getGrafanaConnections,
  postGrafanaConnection,
  putGrafanaConnection,
  deleteGrafanaConnection,
  testGrafanaConnection,
  getGrafanaMappings,
  postGrafanaMapping,
  putGrafanaMapping,
  deleteGrafanaMapping,
} from '@/api/grafana'
import { getCITypes } from '@/modules/cmdb/api/CIType'

export default {
  name: 'SettingGrafana',
  data() {
    return {
      connections: [],
      mappings: [],
      ciTypes: [],
      saving: false,
      testing: false,
      connectionModalVisible: false,
      mappingModalVisible: false,
      connectionForm: { id: null, name: '', url: '', api_key: '', remark: '' },
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, dashboard_uid: '', var_name: 'ci_name' },
      connectionColumns: [
        { title: this.$t('cs.grafana.name'), dataIndex: 'name' },
        { title: this.$t('cs.grafana.url'), dataIndex: 'url' },
        { title: this.$t('cs.grafana.remark'), dataIndex: 'remark' },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 220 },
      ],
      mappingColumns: [
        { title: this.$t('cs.grafana.ciType'), scopedSlots: { customRender: 'ci_type' } },
        { title: this.$t('cs.grafana.connectionInstance'), scopedSlots: { customRender: 'connection' } },
        { title: this.$t('cs.grafana.dashboardUid'), dataIndex: 'dashboard_uid' },
        { title: this.$t('cs.grafana.varName'), dataIndex: 'var_name' },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 160 },
      ],
    }
  },
  computed: {
    connectionRules() {
      return {
        name: [{ required: true, message: this.$t('cs.grafana.nameRequired'), trigger: 'blur' }],
        url: [{ required: true, message: this.$t('cs.grafana.urlRequired'), trigger: 'blur' }],
        api_key: [{ required: !this.connectionForm.id, message: this.$t('cs.grafana.apiKeyRequired'), trigger: 'blur' }],
      }
    },
    mappingRules() {
      return {
        ci_type_id: [{ required: true, message: this.$t('cs.grafana.ciTypeRequired'), trigger: 'change' }],
        connection_id: [{ required: true, message: this.$t('cs.grafana.connectionRequired'), trigger: 'change' }],
      }
    },
  },
  mounted() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      const [connRes, mapRes, typeRes] = await Promise.all([
        getGrafanaConnections(),
        getGrafanaMappings(),
        getCITypes(),
      ])
      this.connections = connRes.connections || []
      this.mappings = mapRes.mappings || []
      this.ciTypes = typeRes.ci_types || []
    },
    ciTypeName(id) {
      const t = this.ciTypes.find((i) => i.id === id)
      return t ? t.alias || t.name : id
    },
    connectionName(id) {
      const c = this.connections.find((i) => i.id === id)
      return c ? c.name : id
    },
    openConnectionModal(record = null) {
      this.connectionForm = record
        ? { id: record.id, name: record.name, url: record.url, api_key: '', remark: record.remark }
        : { id: null, name: '', url: '', api_key: '', remark: '' }
      this.connectionModalVisible = true
      this.$nextTick(() => this.$refs.connectionForm && this.$refs.connectionForm.clearValidate())
    },
    openMappingModal(record = null) {
      this.mappingForm = record
        ? { id: record.id, ci_type_id: record.ci_type_id, connection_id: record.connection_id, dashboard_uid: record.dashboard_uid, var_name: record.var_name }
        : { id: null, ci_type_id: undefined, connection_id: undefined, dashboard_uid: '', var_name: 'ci_name' }
      this.mappingModalVisible = true
      this.$nextTick(() => this.$refs.mappingForm && this.$refs.mappingForm.clearValidate())
    },
    handleSaveConnection() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          const { id, ...data } = this.connectionForm
          if (id) {
            await putGrafanaConnection(id, data)
          } else {
            await postGrafanaConnection(data)
          }
          this.$message.success(this.$t('saveSuccess'))
          this.connectionModalVisible = false
          await this.loadAll()
        } finally {
          this.saving = false
        }
      })
    },
    handleSaveMapping() {
      this.$refs.mappingForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          const { id, ...data } = this.mappingForm
          if (id) {
            await putGrafanaMapping(id, data)
          } else {
            await postGrafanaMapping(data)
          }
          this.$message.success(this.$t('saveSuccess'))
          this.mappingModalVisible = false
          await this.loadAll()
        } finally {
          this.saving = false
        }
      })
    },
    async handleDeleteConnection(record) {
      await deleteGrafanaConnection(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    async handleDeleteMapping(record) {
      await deleteGrafanaMapping(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    handleTest() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.testing = true
        try {
          await testGrafanaConnection({ url: this.connectionForm.url, api_key: this.connectionForm.api_key })
          this.$message.success(this.$t('cs.grafana.testSuccess'))
        } finally {
          this.testing = false
        }
      })
    },
  },
}
</script>

<style lang="less" scoped>
.ops-setting-grafana {
  padding: 20px;
  background-color: #f5f7fa;
  height: calc(100vh - 64px);
  overflow: auto;
  .grafana-card {
    margin-bottom: 16px;
  }
}
</style>
