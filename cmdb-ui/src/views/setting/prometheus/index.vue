<template>
  <div class="ops-setting-prometheus">
    <a-card :title="$t('cs.prometheus.connection')" :bordered="false" class="prometheus-card">
      <a-button slot="extra" type="primary" @click="openConnectionModal()">
        {{ $t('cs.prometheus.addConnection') }}
      </a-button>
      <a-table
        :columns="connectionColumns"
        :data-source="connections"
        :pagination="false"
        rowKey="id"
        size="small"
      >
        <template slot="statusTitle">
          {{ $t('cs.prometheus.status') }}
          <a-icon type="reload" :style="{ marginLeft: '4px', cursor: 'pointer' }" @click="loadHealth" />
        </template>
        <template slot="status" slot-scope="text, record">
          <a-tooltip v-if="healthMap[record.id] && !healthMap[record.id].ok" :title="healthMap[record.id].error">
            <a-badge status="error" :text="$t('cs.prometheus.unhealthy')" />
          </a-tooltip>
          <a-badge v-else-if="healthMap[record.id] && healthMap[record.id].ok" status="success" :text="$t('cs.prometheus.healthy')" />
          <a-badge v-else status="default" :text="$t('cs.prometheus.checking')" />
        </template>
        <template slot="auth_type" slot-scope="text">
          <a-tag>{{ text || 'none' }}</a-tag>
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleToggleEnable(record, checked)" />
        </template>
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openConnectionModal(record)">{{ $t('cs.prometheus.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteConnection(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.prometheus.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <a-card :title="$t('cs.prometheus.mapping')" :bordered="false" class="prometheus-card">
      <a-button slot="extra" type="primary" @click="openMappingModal()">
        {{ $t('cs.prometheus.addMapping') }}
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
        <template slot="label_mapping" slot-scope="text, record">
          {{ (record.label_mapping || []).map((lm) => `${lm.prom_label}←${lm.value}`).join(', ') || '-' }}
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleMappingToggleEnable(record, checked)" />
        </template>
        <template slot="action" slot-scope="text, record">
          <a-space>
            <a @click="openMappingModal(record)">{{ $t('cs.prometheus.edit') }}</a>
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDeleteMapping(record)">
              <a :style="{ color: '#f5222d' }">{{ $t('cs.prometheus.delete') }}</a>
            </a-popconfirm>
          </a-space>
        </template>
      </a-table>
    </a-card>

    <!-- Connection Modal -->
    <a-modal
      :title="connectionForm.id ? $t('cs.prometheus.editConnection') : $t('cs.prometheus.addConnection')"
      :visible="connectionModalVisible"
      @cancel="connectionModalVisible = false"
    >
      <a-form-model ref="connectionForm" :model="connectionForm" :rules="connectionRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-model-item :label="$t('cs.prometheus.name')" prop="name">
          <a-input v-model="connectionForm.name" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.url')" prop="url">
          <a-input v-model="connectionForm.url" placeholder="http://prometheus:9090" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.authType')">
          <a-select v-model="connectionForm.auth_type">
            <a-select-option value="none">None</a-select-option>
            <a-select-option value="bearer">Bearer Token</a-select-option>
            <a-select-option value="basic">Basic Auth</a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item v-if="connectionForm.auth_type === 'bearer'" :label="$t('cs.prometheus.token')">
          <a-input-password v-model="connectionForm.auth_data.token" />
        </a-form-model-item>
        <template v-if="connectionForm.auth_type === 'basic'">
          <a-form-model-item :label="$t('cs.prometheus.username')">
            <a-input v-model="connectionForm.auth_data.username" />
          </a-form-model-item>
          <a-form-model-item :label="$t('cs.prometheus.password')">
            <a-input-password v-model="connectionForm.auth_data.password" />
          </a-form-model-item>
        </template>
        <a-form-model-item :label="$t('cs.prometheus.remark')">
          <a-input v-model="connectionForm.remark" />
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.enable')">
          <a-switch :checked="connectionForm.enable !== 0" @change="(checked) => { connectionForm.enable = checked ? 1 : 0 }" />
        </a-form-model-item>
      </a-form-model>
      <template slot="footer">
        <a-button :loading="testing" @click="handleTest">{{ $t('cs.prometheus.testConnect') }}</a-button>
        <a-button @click="connectionModalVisible = false">{{ $t('cancel') }}</a-button>
        <a-button type="primary" :loading="saving" @click="handleSaveConnection">{{ $t('save') }}</a-button>
      </template>
    </a-modal>

    <!-- Mapping Modal -->
    <a-modal
      :title="mappingForm.id ? $t('cs.prometheus.editMapping') : $t('cs.prometheus.addMapping')"
      :visible="mappingModalVisible"
      :confirm-loading="saving"
      width="900px"
      @ok="handleSaveMapping"
      @cancel="mappingModalVisible = false"
    >
      <a-form-model ref="mappingForm" :model="mappingForm" :rules="mappingRules" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
        <a-form-model-item :label="$t('cs.prometheus.ciType')" prop="ci_type_id">
          <a-select v-model="mappingForm.ci_type_id" show-search option-filter-prop="children" @change="handleCiTypeChange">
            <a-select-option v-for="t in ciTypes" :key="t.id" :value="t.id">
              {{ t.alias || t.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.connectionInstance')" prop="connection_id">
          <a-select v-model="mappingForm.connection_id">
            <a-select-option v-for="c in connections" :key="c.id" :value="c.id">
              {{ c.name }}
            </a-select-option>
          </a-select>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.labelMapping')">
          <a-table
            :columns="labelMappingColumns"
            :data-source="mappingForm.label_mapping"
            :pagination="false"
            size="small"
            rowKey="_key"
            style="margin-bottom: 8px"
          >
            <template slot="prom_label" slot-scope="text, record">
              <a-input v-model="record.prom_label" :placeholder="$t('cs.prometheus.promLabel')" style="width: 100%" />
            </template>
            <template slot="map_type" slot-scope="text, record">
              <a-select v-model="record.map_type" style="width: 100%">
                <a-select-option value="field">{{ $t('cs.prometheus.field') }}</a-select-option>
                <a-select-option value="fixed">{{ $t('cs.prometheus.fixed') }}</a-select-option>
              </a-select>
            </template>
            <template slot="target" slot-scope="text, record">
              <a-select
                v-if="record.map_type === 'field'"
                v-model="record.value"
                show-search
                option-filter-prop="children"
                :placeholder="$t('cs.prometheus.ciAttr')"
                style="width: 100%"
              >
                <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                  {{ a.alias || a.name }}({{ a.name }})
                </a-select-option>
              </a-select>
              <a-input
                v-else
                v-model="record.value"
                :placeholder="$t('cs.prometheus.fixedValue')"
                style="width: 100%"
              />
            </template>
            <template slot="action" slot-scope="text, record, index">
              <a-icon type="minus-circle" style="cursor: pointer; color: #f5222d; font-size: 16px;" @click="removeLabelMapping(index)" />
            </template>
          </a-table>
          <a-button type="dashed" size="small" icon="plus" @click="addLabelMapping">
            {{ $t('cs.prometheus.addLabelMapping') }}
          </a-button>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.prometheus.mappingEnable')">
          <a-switch :checked="mappingForm.enable !== 0" @change="(checked) => { mappingForm.enable = checked ? 1 : 0 }" />
        </a-form-model-item>
      </a-form-model>
    </a-modal>
  </div>
</template>

<script>
import {
  getPrometheusConnections,
  postPrometheusConnection,
  putPrometheusConnection,
  deletePrometheusConnection,
  testPrometheusConnection,
  getPrometheusConnectionsHealth,
  getPrometheusMappings,
  postPrometheusMapping,
  putPrometheusMapping,
  deletePrometheusMapping,
} from '@/api/prometheus'
import { getCITypes } from '@/modules/cmdb/api/CIType'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'

export default {
  name: 'SettingPrometheus',
  data() {
    return {
      connections: [],
      mappings: [],
      ciTypes: [],
      saving: false,
      testing: false,
      connectionModalVisible: false,
      mappingModalVisible: false,
      connectionForm: { id: null, name: '', url: '', auth_type: 'none', auth_data: {}, remark: '', enable: 1 },
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, label_mapping: [], enable: 1 },
      labelMappingKeyCounter: 0,
      healthMap: {},
      ciAttrOptions: [],
      connectionColumns: [],
      mappingColumns: [],
      labelMappingColumns: [],
    }
  },
  computed: {
    connectionRules() {
      return {
        name: [{ required: true, message: this.$t('cs.prometheus.nameRequired'), trigger: 'blur' }],
        url: [{ required: true, message: this.$t('cs.prometheus.urlRequired'), trigger: 'blur' }],
      }
    },
    mappingRules() {
      return {
        ci_type_id: [{ required: true, message: this.$t('cs.prometheus.ciTypeRequired'), trigger: 'change' }],
        connection_id: [{ required: true, message: this.$t('cs.prometheus.connectionRequired'), trigger: 'change' }],
      }
    },
  },
  created() {
    this.connectionColumns = [
      { title: this.$t('cs.prometheus.name'), dataIndex: 'name' },
      { title: this.$t('cs.prometheus.url'), dataIndex: 'url' },
      { title: this.$t('cs.prometheus.authType'), scopedSlots: { customRender: 'auth_type' }, width: 90 },
      { slots: { title: 'statusTitle' }, scopedSlots: { customRender: 'status' }, width: 110 },
      { title: this.$t('cs.prometheus.enable'), scopedSlots: { customRender: 'enable' }, width: 80 },
      { title: this.$t('cs.prometheus.remark'), dataIndex: 'remark' },
      { title: this.$t('cs.prometheus.operation'), scopedSlots: { customRender: 'action' }, width: 220 },
    ]
    this.mappingColumns = [
      { title: this.$t('cs.prometheus.ciType'), scopedSlots: { customRender: 'ci_type' } },
      { title: this.$t('cs.prometheus.connectionInstance'), scopedSlots: { customRender: 'connection' } },
      { title: this.$t('cs.prometheus.labelMapping'), scopedSlots: { customRender: 'label_mapping' } },
      { title: this.$t('cs.prometheus.mappingEnable'), scopedSlots: { customRender: 'enable' }, width: 80 },
      { title: this.$t('cs.prometheus.operation'), scopedSlots: { customRender: 'action' }, width: 160 },
    ]
    this.labelMappingColumns = [
      { title: this.$t('cs.prometheus.promLabel'), scopedSlots: { customRender: 'prom_label' } },
      { title: this.$t('cs.prometheus.mapType'), scopedSlots: { customRender: 'map_type' }, width: 100 },
      { title: this.$t('cs.prometheus.target'), scopedSlots: { customRender: 'target' } },
      { title: this.$t('cs.prometheus.operation'), scopedSlots: { customRender: 'action' }, width: 50 },
    ]
  },
  mounted() {
    this.loadAll()
  },
  methods: {
    async loadAll() {
      const [connRes, mapRes, typeRes] = await Promise.all([
        getPrometheusConnections(),
        getPrometheusMappings(),
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
        const res = await getPrometheusConnectionsHealth()
        const map = {}
        ;(res.health || []).forEach((h) => { map[h.id] = h })
        this.healthMap = map
      } catch (e) {}
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
      if (record) {
        this.connectionForm = {
          id: record.id, name: record.name, url: record.url,
          auth_type: record.auth_type || 'none',
          auth_data: { ...(record.auth_data || {}) },
          remark: record.remark, enable: record.enable === undefined ? 1 : record.enable,
        }
      } else {
        this.connectionForm = { id: null, name: '', url: '', auth_type: 'none', auth_data: {}, remark: '', enable: 1 }
      }
      this.connectionModalVisible = true
      this.$nextTick(() => this.$refs.connectionForm && this.$refs.connectionForm.clearValidate())
    },
    openMappingModal(record = null) {
      if (record) {
        const mapped = (record.label_mapping || []).map((lm, idx) => ({
          _key: idx + 1,
          prom_label: lm.prom_label,
          map_type: lm.map_type || 'field',
          value: lm.value || '',
        }))
        this.labelMappingKeyCounter = mapped.length
        this.mappingForm = {
          id: record.id,
          ci_type_id: record.ci_type_id,
          connection_id: record.connection_id,
          enable: record.enable === undefined ? 1 : record.enable,
          label_mapping: mapped,
        }
      } else {
        this.labelMappingKeyCounter = 0
        this.mappingForm = { id: null, ci_type_id: undefined, connection_id: undefined, label_mapping: [], enable: 1 }
      }
      this.mappingModalVisible = true
      this.$nextTick(() => this.$refs.mappingForm && this.$refs.mappingForm.clearValidate())
      if (this.mappingForm.ci_type_id) this.handleCiTypeChange(this.mappingForm.ci_type_id)
    },
    async handleCiTypeChange(typeId) {
      try {
        const res = await getCITypeAttributesById(typeId)
        this.ciAttrOptions = res.attributes || []
      } catch (e) {
        this.ciAttrOptions = []
      }
    },
    addLabelMapping() {
      this.mappingForm.label_mapping.push({
        _key: ++this.labelMappingKeyCounter,
        prom_label: undefined,
        map_type: 'field',
        value: '',
      })
    },
    removeLabelMapping(index) {
      this.mappingForm.label_mapping.splice(index, 1)
    },
    async handleToggleEnable(record, checked) {
      await putPrometheusConnection(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
    },
    async handleMappingToggleEnable(record, checked) {
      await putPrometheusMapping(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
    },
    handleSaveConnection() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.saving = true
        try {
          const { id, ...data } = this.connectionForm
          if (id) {
            await putPrometheusConnection(id, data)
          } else {
            await postPrometheusConnection(data)
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
        const labelMappings = this.mappingForm.label_mapping || []
        const incomplete = labelMappings.some((lm) => !lm.prom_label || !lm.value)
        if (incomplete) {
          this.$message.error(this.$t('cs.prometheus.labelMappingIncomplete'))
          return
        }
        this.saving = true
        try {
          const { id, ...data } = this.mappingForm
          if (id) {
            await putPrometheusMapping(id, data)
          } else {
            await postPrometheusMapping(data)
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
      await deletePrometheusConnection(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    async handleDeleteMapping(record) {
      await deletePrometheusMapping(record.id)
      this.$message.success(this.$t('deleteSuccess'))
      await this.loadAll()
    },
    handleTest() {
      this.$refs.connectionForm.validate(async (valid) => {
        if (!valid) return
        this.testing = true
        try {
          await testPrometheusConnection({
            url: this.connectionForm.url,
            auth_type: this.connectionForm.auth_type,
            auth_data: this.connectionForm.auth_data,
          })
          this.$message.success(this.$t('cs.prometheus.testSuccess'))
        } finally {
          this.testing = false
        }
      })
    },
  },
}
</script>

<style lang="less" scoped>
.ops-setting-prometheus {
  padding: 20px;
  background-color: #f5f7fa;
  height: calc(100vh - 64px);
  overflow: auto;
  .prometheus-card {
    margin-bottom: 16px;
  }
}
</style>
