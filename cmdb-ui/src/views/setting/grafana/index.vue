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
        <template slot="statusTitle">
          {{ $t('cs.grafana.status') }}
          <a-icon type="reload" :style="{ marginLeft: '4px', cursor: 'pointer' }" @click="loadHealth" />
        </template>
        <template slot="status" slot-scope="text, record">
          <a-tooltip v-if="healthMap[record.id] && !healthMap[record.id].ok" :title="healthMap[record.id].error">
            <a-badge status="error" :text="$t('cs.grafana.unhealthy')" />
          </a-tooltip>
          <a-badge v-else-if="healthMap[record.id] && healthMap[record.id].ok" status="success" :text="$t('cs.grafana.healthy')" />
          <a-badge v-else status="default" :text="$t('cs.grafana.checking')" />
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleToggleEnable(record, checked)" />
        </template>
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
        <template slot="var_mapping" slot-scope="text, record">
          {{ (record.var_mapping || []).map((vm) => `${vm.grafana_var}←${vm.ci_attr}`).join(', ') || '-' }}
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
        <a-form-model-item :label="$t('cs.grafana.enable')" prop="enable">
          <a-switch :checked="connectionForm.enable !== 0" @change="(checked) => { connectionForm.enable = checked ? 1 : 0 }" />
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
          <a-select v-model="mappingForm.ci_type_id" show-search option-filter-prop="children" @change="handleCiTypeChange">
            <a-select-option v-for="t in ciTypes" :key="t.id" :value="t.id">
              {{ t.alias || t.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.connectionInstance')" prop="connection_id">
          <a-select v-model="mappingForm.connection_id" @change="handleMappingConnectionChange">
            <a-select-option v-for="c in connections" :key="c.id" :value="c.id">
              {{ c.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.namespace')" prop="namespace">
          <a-input v-model="mappingForm.namespace" placeholder="default" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.dashboardName')" prop="dashboard_name">
          <a-auto-complete
            v-model="mappingForm.dashboard_name"
            :data-source="dashboardOptions"
            :filter-option="filterDashboardOption"
            @select="handleDashboardSelect"
          />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.dashboardTitle')" prop="dashboard_title">
          <a-input v-model="mappingForm.dashboard_title" read-only />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.varMapping')">
          <div v-for="(vm, idx) in mappingForm.var_mapping" :key="idx" class="var-mapping-row">
            <a-auto-complete
              v-model="vm.grafana_var"
              :data-source="variableOptions"
              :placeholder="$t('cs.grafana.grafanaVar')"
              class="var-mapping-input"
              @change="(v) => handleVarChange(vm, v)"
            />
            <a-icon type="swap-right" class="var-mapping-arrow" />
            <a-select
              v-model="vm.ci_attr"
              show-search
              option-filter-prop="children"
              :placeholder="$t('cs.grafana.ciAttr')"
              class="var-mapping-input"
            >
              <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                {{ a.alias || a.name }}
              </a-select-option>
            </a-select>
            <a-icon type="minus-circle" class="var-mapping-delete" @click="mappingForm.var_mapping.splice(idx, 1)" />
          </div>
          <a-button type="dashed" size="small" icon="plus" @click="addVarMapping">
            {{ $t('cs.grafana.addVarMapping') }}
          </a-button>
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
  getGrafanaConnectionsHealth,
  getGrafanaDashboards,
  getGrafanaDashboardVariables,
  getGrafanaMappings,
  postGrafanaMapping,
  putGrafanaMapping,
  deleteGrafanaMapping,
} from '@/api/grafana'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'

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
      connectionForm: { id: null, name: '', url: '', api_key: '', remark: '', enable: 1 },
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, namespace: 'default', dashboard_name: '', dashboard_title: '', var_mapping: [] },
      healthMap: {},
      dashboards: [],
      variableOptions: [],
      ciAttrOptions: [],
      connectionColumns: [
        { title: this.$t('cs.grafana.name'), dataIndex: 'name' },
        { title: this.$t('cs.grafana.url'), dataIndex: 'url' },
        { title: this.$t('cs.grafana.remark'), dataIndex: 'remark' },
        { slots: { title: 'statusTitle' }, scopedSlots: { customRender: 'status' }, width: 110 },
        { title: this.$t('cs.grafana.enable'), scopedSlots: { customRender: 'enable' }, width: 80 },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 220 },
      ],
      mappingColumns: [
        { title: this.$t('cs.grafana.ciType'), scopedSlots: { customRender: 'ci_type' } },
        { title: this.$t('cs.grafana.connectionInstance'), scopedSlots: { customRender: 'connection' } },
        { title: this.$t('cs.grafana.namespace'), dataIndex: 'namespace', width: 100 },
        { title: this.$t('cs.grafana.dashboardTitle'), dataIndex: 'dashboard_title' },
        { title: this.$t('cs.grafana.dashboardName'), dataIndex: 'dashboard_name' },
        { title: this.$t('cs.grafana.varMapping'), scopedSlots: { customRender: 'var_mapping' } },
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
        dashboard_name: [{ required: true, message: this.$t('cs.grafana.dashboardNameRequired'), trigger: 'blur' }],
      }
    },
    dashboardOptions() {
      return this.dashboards.map((d) => ({ value: d.name, text: `${d.title} (${d.name})` }))
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
      this.loadHealth()
    },
    async loadHealth() {
      this.healthMap = {}
      try {
        const res = await getGrafanaConnectionsHealth()
        const map = {}
        ;(res.health || []).forEach((h) => { map[h.id] = h })
        this.healthMap = map
      } catch (e) {}
    },
    async handleToggleEnable(record, checked) {
      await putGrafanaConnection(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
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
        ? { id: record.id, name: record.name, url: record.url, api_key: '', remark: record.remark, enable: record.enable === undefined ? 1 : record.enable }
        : { id: null, name: '', url: '', api_key: '', remark: '', enable: 1 }
      this.connectionModalVisible = true
      this.$nextTick(() => this.$refs.connectionForm && this.$refs.connectionForm.clearValidate())
    },
    openMappingModal(record = null) {
      this.mappingForm = record
        ? {
            id: record.id,
            ci_type_id: record.ci_type_id,
            connection_id: record.connection_id,
            namespace: record.namespace || 'default',
            dashboard_name: record.dashboard_name,
            dashboard_title: record.dashboard_title,
            var_mapping: (record.var_mapping || []).map((vm) => ({ ...vm })),
          }
        : { id: null, ci_type_id: undefined, connection_id: undefined, namespace: 'default', dashboard_name: '', dashboard_title: '', var_mapping: [] }
      this.mappingModalVisible = true
      this.$nextTick(() => this.$refs.mappingForm && this.$refs.mappingForm.clearValidate())
      if (this.mappingForm.ci_type_id) this.handleCiTypeChange(this.mappingForm.ci_type_id)
      if (this.mappingForm.connection_id) this.handleMappingConnectionChange(this.mappingForm.connection_id)
      if (this.mappingForm.connection_id && this.mappingForm.dashboard_name) {
        this.loadVariables(this.mappingForm.connection_id, this.mappingForm.dashboard_name)
      }
    },
    async handleCiTypeChange(typeId) {
      try {
        const res = await getCITypeAttributesById(typeId)
        this.ciAttrOptions = res.attributes || []
      } catch (e) {
        this.ciAttrOptions = []
      }
    },
    async handleMappingConnectionChange(connectionId) {
      try {
        const res = await getGrafanaDashboards(connectionId, this.mappingForm.namespace || 'default')
        this.dashboards = res.dashboards || []
      } catch (e) {
        this.dashboards = []
        this.$message.warning(this.$t('cs.grafana.dashboardLoadFailed'))
      }
    },
    async loadVariables(connectionId, name) {
      try {
        const res = await getGrafanaDashboardVariables(connectionId, name)
        this.variableOptions = res.variables || []
      } catch (e) {
        this.variableOptions = []
      }
    },
    filterDashboardOption(input, option) {
      const text = (option.componentOptions.children[0].text || '').toLowerCase()
      return text.includes(input.toLowerCase())
    },
    handleDashboardSelect(value) {
      const d = this.dashboards.find((i) => i.name === value)
      this.mappingForm.dashboard_title = d ? d.title : ''
      this.loadVariables(this.mappingForm.connection_id, value)
    },
    handleVarChange(vm, value) {
      vm.grafana_var = value
      if (!vm.ci_attr && this.ciAttrOptions.some((a) => a.name === value)) {
        vm.ci_attr = value
      }
    },
    addVarMapping() {
      this.mappingForm.var_mapping.push({ grafana_var: undefined, ci_attr: undefined })
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
        const incomplete = this.mappingForm.var_mapping.some((vm) => !vm.grafana_var || !vm.ci_attr)
        if (incomplete) {
          this.$message.error(this.$t('cs.grafana.varMappingIncomplete'))
          return
        }
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
  .var-mapping-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
    .var-mapping-input {
      flex: 1;
    }
    .var-mapping-arrow,
    .var-mapping-delete {
      flex-shrink: 0;
    }
    .var-mapping-delete {
      cursor: pointer;
      color: #f5222d;
    }
  }
}
</style>
