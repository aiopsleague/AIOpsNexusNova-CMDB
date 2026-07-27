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
          {{ (record.var_mapping || []).map((vm) => `${vm.grafana_var}←${vm.value || '-'}`).join(', ') || '-' }}
        </template>
        <template slot="filter_rules" slot-scope="text, record">
          <span v-if="record.filter_rules && record.filter_rules.rules && record.filter_rules.rules.length">
            {{ record.filter_rules.rules.map((r) => `${r.field} ${r.operator} ${Array.isArray(r.value) ? '(' + r.value.join(',') + ')' : r.value}`).join(' ' + (record.filter_rules.logic || 'and') + ' ') }}
          </span>
          <span v-else>-</span>
        </template>
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleMappingToggleEnable(record, checked)" />
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
      width="900px"
      @ok="handleSaveMapping"
      @cancel="mappingModalVisible = false"
    >
      <a-form-model ref="mappingForm" :model="mappingForm" :rules="mappingRules" :label-col="{ span: 4 }" :wrapper-col="{ span: 18 }">
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
        <a-form-model-item :label="$t('cs.grafana.filterRules')">
          <a-collapse :bordered="false" :activeKey="filterRulesActiveKey">
            <a-collapse-panel key="filter_rules_panel" :showArrow="true">
              <template slot="header">
                <span style="font-size: 13px; color: rgba(0,0,0,0.65)">
                  {{ filterRulesList.length ? $t('cs.grafana.filterSummary', { count: filterRulesList.length }) : $t('cs.grafana.filterRulesOptional') }}
                </span>
              </template>
              <div v-if="filterRulesList.length" style="margin-bottom: 8px;">
                <span style="font-size: 12px; color: rgba(0,0,0,0.65); margin-right: 8px;">{{ $t('cs.grafana.filterLogic') }}:</span>
                <a-radio-group v-model="filterRulesLogic" size="small" buttonStyle="solid">
                  <a-radio-button value="and">{{ $t('cs.grafana.filterLogicAnd') }}</a-radio-button>
                  <a-radio-button value="or">{{ $t('cs.grafana.filterLogicOr') }}</a-radio-button>
                </a-radio-group>
              </div>
              <div
                v-for="(rule, index) in filterRulesList"
                :key="index"
                style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;"
              >
                <a-select
                  v-model="rule.field"
                  show-search
                  option-filter-prop="children"
                  :placeholder="$t('cs.grafana.filterField')"
                  style="flex: 2;"
                  size="small"
                >
                  <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                    {{ a.alias || a.name }}({{ a.name }})
                  </a-select-option>
                </a-select>
                <a-select
                  v-model="rule.operator"
                  style="flex: 1; min-width: 100px;"
                  size="small"
                >
                  <a-select-option v-for="op in filterRuleOperators" :key="op.value" :value="op.value">
                    {{ op.label }}
                  </a-select-option>
                </a-select>
                <a-select
                  v-if="rule.operator === 'in' || rule.operator === 'not_in'"
                  v-model="rule.value"
                  mode="tags"
                  :placeholder="$t('cs.grafana.filterValue')"
                  style="flex: 3; min-width: 140px;"
                  size="small"
                  :openOnFocus="false"
                />
                <a-input
                  v-else
                  v-model="rule.value"
                  :placeholder="$t('cs.grafana.filterValue')"
                  style="flex: 3; min-width: 100px;"
                  size="small"
                />
                <a-icon
                  type="minus-circle"
                  style="cursor: pointer; color: #f5222d; font-size: 14px; flex-shrink: 0;"
                  @click="removeFilterRule(index)"
                />
              </div>
              <a-button type="dashed" size="small" icon="plus" @click="addFilterRule">
                {{ $t('cs.grafana.filterAddCondition') }}
              </a-button>
            </a-collapse-panel>
          </a-collapse>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.varMapping')">
          <a-table
            :columns="varMappingColumns"
            :data-source="mappingForm.var_mapping"
            :pagination="false"
            size="small"
            rowKey="_key"
            :scroll="{ y: 240 }"
            style="margin-bottom: 8px"
          >
            <template slot="grafana_var" slot-scope="text, record">
              <a-auto-complete
                v-model="record.grafana_var"
                :data-source="variableOptions"
                :placeholder="$t('cs.grafana.grafanaVar')"
                style="width: 100%"
                @change="(v) => handleVarChange(record, v)"
              />
            </template>
            <template slot="map_type" slot-scope="text, record">
              <a-select v-model="record.map_type" style="width: 100%" @change="() => handleMappingTypeChange(record)">
                <a-select-option value="fixed">{{ $t('cs.grafana.fixed') }}</a-select-option>
                <a-select-option value="field">{{ $t('cs.grafana.field') }}</a-select-option>
              </a-select>
            </template>
            <template slot="target" slot-scope="text, record">
              <a-select
                v-if="record.map_type === 'field'"
                v-model="record.value"
                show-search
                option-filter-prop="children"
                :placeholder="$t('cs.grafana.ciAttr')"
                style="width: 100%"
              >
                <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                  {{ a.alias || a.name }}({{ a.name }})
                </a-select-option>
              </a-select>
              <a-input
                v-else
                v-model="record.value"
                :placeholder="$t('cs.grafana.targetPlaceholder')"
                style="width: 100%"
              />
            </template>
            <template slot="var_type" slot-scope="text, record">
              <a-select v-model="record.var_type" style="width: 100%" size="small">
                <a-select-option value="normal">{{ $t('cs.grafana.varTypeNormal') }}</a-select-option>
                <a-select-option value="native">{{ $t('cs.grafana.varTypeNative') }}</a-select-option>
              </a-select>
            </template>
            <template slot="remark" slot-scope="text, record">
              <a-input v-model="record.remark" :placeholder="$t('cs.grafana.remark')" style="width: 100%" />
            </template>
            <template slot="action" slot-scope="text, record, index">
              <a-icon type="minus-circle" style="cursor: pointer; color: #f5222d; font-size: 16px;" @click="removeVarMapping(index)" />
            </template>
          </a-table>
          <a-button type="dashed" size="small" icon="plus" @click="addVarMapping">
            {{ $t('cs.grafana.addVarMapping') }}
          </a-button>
        </a-form-model-item>
        <a-form-model-item :label="$t('cs.grafana.mappingEnable')">
          <a-switch :checked="mappingForm.enable !== 0" @change="(checked) => { mappingForm.enable = checked ? 1 : 0 }" />
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
      mappingForm: { id: null, ci_type_id: undefined, connection_id: undefined, namespace: 'default', dashboard_name: '', dashboard_title: '', var_mapping: [], enable: 1 },
      varMappingKeyCounter: 0,
      filterRulesLogic: 'and',
      filterRulesList: [],
      filterRulesActiveKey: '',
      healthMap: {},
      dashboards: [],
      variableOptions: [],
      ciAttrOptions: [],
      connectionColumns: [
        { title: this.$t('cs.grafana.name'), dataIndex: 'name' },
        { title: this.$t('cs.grafana.url'), dataIndex: 'url' },
        { slots: { title: 'statusTitle' }, scopedSlots: { customRender: 'status' }, width: 110 },
        { title: this.$t('cs.grafana.enable'), scopedSlots: { customRender: 'enable' }, width: 80 },
        { title: this.$t('cs.grafana.remark'), dataIndex: 'remark' },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 220 },
      ],
      mappingColumns: [
        { title: this.$t('cs.grafana.ciType'), scopedSlots: { customRender: 'ci_type' } },
        { title: this.$t('cs.grafana.connectionInstance'), scopedSlots: { customRender: 'connection' } },
        { title: this.$t('cs.grafana.namespace'), dataIndex: 'namespace', width: 100 },
        { title: this.$t('cs.grafana.dashboardTitle'), dataIndex: 'dashboard_title' },
        { title: this.$t('cs.grafana.dashboardName'), dataIndex: 'dashboard_name' },
        { title: this.$t('cs.grafana.filterRules'), scopedSlots: { customRender: 'filter_rules' }, width: 200 },
        { title: this.$t('cs.grafana.mappingEnable'), scopedSlots: { customRender: 'enable' }, width: 80 },
        { title: this.$t('cs.grafana.varMapping'), scopedSlots: { customRender: 'var_mapping' } },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 160 },
      ],
      varMappingColumns: [
        { title: this.$t('cs.grafana.source'), dataIndex: 'grafana_var', scopedSlots: { customRender: 'grafana_var' } },
        { title: this.$t('cs.grafana.varType'), scopedSlots: { customRender: 'var_type' }, width: 110 },
        { title: this.$t('cs.grafana.mappingType'), dataIndex: 'map_type', scopedSlots: { customRender: 'map_type' }, width: 100 },
        { title: this.$t('cs.grafana.target'), dataIndex: 'target', scopedSlots: { customRender: 'target' } },
        { title: this.$t('cs.grafana.remark'), dataIndex: 'remark', scopedSlots: { customRender: 'remark' } },
        { title: this.$t('cs.grafana.operation'), scopedSlots: { customRender: 'action' }, width: 50 },
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
    filterRuleOperators() {
      return [
        { value: 'equal', label: this.$t('cs.grafana.op_equal') },
        { value: 'not_equal', label: this.$t('cs.grafana.op_not_equal') },
        { value: 'contains', label: this.$t('cs.grafana.op_contains') },
        { value: 'not_contains', label: this.$t('cs.grafana.op_not_contains') },
        { value: 'in', label: this.$t('cs.grafana.op_in') },
        { value: 'not_in', label: this.$t('cs.grafana.op_not_in') },
      ]
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
      if (record) {
        const mapped = (record.var_mapping || []).map((vm, idx) => ({
          _key: idx + 1,
          grafana_var: vm.grafana_var,
          map_type: vm.map_type || 'field',
          value: vm.value || vm.ci_attr || '',
          remark: vm.remark || '',
          enable: vm.enable !== undefined ? vm.enable : 1,
          var_type: vm.var_type || 'normal',
        }))
        this.varMappingKeyCounter = mapped.length
        this.mappingForm = {
          id: record.id,
          ci_type_id: record.ci_type_id,
          connection_id: record.connection_id,
          namespace: record.namespace || 'default',
          dashboard_name: record.dashboard_name,
          dashboard_title: record.dashboard_title,
          enable: record.enable === undefined ? 1 : record.enable,
          var_mapping: mapped,
        }
        const fr = record.filter_rules
        if (fr && fr.rules && fr.rules.length) {
          this.filterRulesLogic = fr.logic || 'and'
          this.filterRulesList = fr.rules.map((r) => ({
            field: r.field || '',
            operator: r.operator || 'equal',
            value: r.operator === 'in' || r.operator === 'not_in'
              ? (Array.isArray(r.value) ? [...r.value] : (r.value ? [r.value] : []))
              : (Array.isArray(r.value) ? r.value.join(',') : (r.value || '')),
          }))
          this.filterRulesActiveKey = 'filter_rules_panel'
        } else {
          this.filterRulesLogic = 'and'
          this.filterRulesList = []
          this.filterRulesActiveKey = ''
        }
      } else {
        this.varMappingKeyCounter = 0
        this.filterRulesLogic = 'and'
        this.filterRulesList = []
        this.filterRulesActiveKey = ''
        this.mappingForm = { id: null, ci_type_id: undefined, connection_id: undefined, namespace: 'default', dashboard_name: '', dashboard_title: '', var_mapping: [], enable: 1 }
      }
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
        // a-auto-complete data-source expects strings or {value, text} objects
        this.variableOptions = (res.variables || []).map((v) => v.name)
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
      // Auto-fill target if map_type is 'field' and variable name matches a CI attribute name
      if (vm.map_type === 'field' && !vm.value && this.ciAttrOptions.some((a) => a.name === value)) {
        vm.value = value
      }
    },
    addVarMapping() {
      this.mappingForm.var_mapping.push({
        _key: ++this.varMappingKeyCounter,
        grafana_var: undefined,
        map_type: 'field',
        value: '',
        remark: '',
        enable: 1,
        var_type: 'normal',
      })
    },
    removeVarMapping(index) {
      this.mappingForm.var_mapping.splice(index, 1)
    },
    handleMappingTypeChange(record) {
      if (record.map_type === 'fixed') {
        record.value = ''
      }
    },
    addFilterRule() {
      this.filterRulesList.push({ field: undefined, operator: 'equal', value: '' })
      this.filterRulesActiveKey = 'filter_rules_panel'
    },
    removeFilterRule(index) {
      this.filterRulesList.splice(index, 1)
      if (!this.filterRulesList.length) {
        this.filterRulesActiveKey = ''
      }
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
        const varMappings = this.mappingForm.var_mapping || []

        // Check each row has required fields
        const incomplete = varMappings.some(
          (vm) => !vm.grafana_var || !vm.value
        )
        if (incomplete) {
          this.$message.error(this.$t('cs.grafana.varMappingIncomplete'))
          return
        }

        // Check for duplicate grafana_var
        const varNames = varMappings.map((vm) => vm.grafana_var)
        if (new Set(varNames).size !== varNames.length) {
          this.$message.error(this.$t('cs.grafana.varMappingDuplicated'))
          return
        }

        this.saving = true
        try {
          const { id, ...data } = this.mappingForm
          // Build filter_rules from the form state
          if (this.filterRulesList.length) {
            data.filter_rules = {
              logic: this.filterRulesLogic,
              rules: this.filterRulesList.map((r) => ({
                field: r.field,
                operator: r.operator,
                value: r.value,
              })),
            }
          } else {
            data.filter_rules = null
          }
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
    async handleMappingToggleEnable(record, checked) {
      await putGrafanaMapping(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
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
