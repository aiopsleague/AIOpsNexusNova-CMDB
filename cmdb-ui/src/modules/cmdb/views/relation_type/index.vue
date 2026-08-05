<template>
  <a-card :bordered="false">
    <div class="action-btn">
      <a-button @click="handleCreate" type="primary" style="margin-bottom: 15px;">{{ $t('cmdb.relation_type.addRelationType') }}</a-button>
    </div>
    <vxe-table
      ref="relationTypeTable"
      :data="tableData"
      keep-source
      highlight-hover-row
      :edit-config="{ trigger: 'manual', mode: 'row' }"
      @edit-closed="handleEditClose"
      stripe
      class="ops-stripe-table"
      bordered
    >
      <vxe-table-column
        field="name"
        :title="$t('name')"
        :edit-render="{ name: 'input', attrs: { type: 'text' }, events: { keyup: customCloseEdit } }"
      ></vxe-table-column>
      <vxe-table-column
        field="color"
        :title="$t('cmdb.relation_type.color')"
        width="100"
        align="center"
        :edit-render="{}"
      >
        <template #default="{ row }">
          <div
            class="color-swatch"
            :style="{ backgroundColor: row.color || '#1890ff' }"
          ></div>
        </template>
        <template #edit="{ row }">
          <input
            type="color"
            v-model="row.color"
            style="width: 50px; height: 28px; border: 1px solid #d9d9d9; border-radius: 2px; cursor: pointer;"
          />
        </template>
      </vxe-table-column>
      <vxe-table-column field="updateTime" :title="$t('updated_at')">
        <template #default="{row}">
          {{ row.updated_at || row.created_at }}
        </template>
      </vxe-table-column>
      <vxe-table-column field="operation" :title="$t('operation')" align="center">
        <template #default="{row}">
          <template>
            <a><a-icon type="edit" @click="handleEdit(row)"/></a>
            <a-divider type="vertical" />
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDelete(row)" :okText="$t('yes')" :cancelText="$t('no')">
              <a :style="{ color: 'red' }"><a-icon type="delete"/></a>
            </a-popconfirm>
          </template>
        </template>
      </vxe-table-column>
    </vxe-table>
  </a-card>
</template>

<script>
import moment from 'moment'
import {
  getRelationTypes,
  deleteRelationType,
  addRelationType,
  updateRelationType,
} from '@/modules/cmdb/api/relationType'

export default {
  name: 'RelationType',
  components: {},
  data() {
    return {
      tableData: [],
    }
  },

  computed: {},
  mounted() {
    this.loadData()
  },

  methods: {
    loadData() {
      getRelationTypes().then((res) => {
        this.tableData = res
      })
    },
    handleEdit(row) {
      const $table = this.$refs.relationTypeTable
      $table.setActiveRow(row)
    },
    handleCreate() {
      const $table = this.$refs.relationTypeTable
      const newRow = {
        name: '',
        color: '#1890ff',
        created_at: moment().format('YYYY-MM-DD hh:mm:ss'),
      }
      $table.insert(newRow).then(({ row }) => $table.setActiveRow(row))
    },
    handleEditClose({ row, rowIndex, column }) {
      const $table = this.$refs.relationTypeTable
      if (row.id) {
        if (row.name && ($table.isUpdateByRow(row, 'name') || $table.isUpdateByRow(row, 'color'))) {
          this.updateRelationType(row.id, { name: row.name, color: row.color })
        } else {
          $table.revertData(row)
        }
      } else {
        if (row.name) {
          this.createRelationType({ name: row.name, color: row.color || '#1890ff' })
        } else {
          this.loadData()
        }
      }
    },
    updateRelationType(id, data) {
      updateRelationType(id, data).then((res) => {
        this.$message.success(this.$t('updateSuccess'))
        this.loadData()
      })
    },

    createRelationType(data) {
      addRelationType(data).then((res) => {
        this.$message.success(this.$t('addSuccess'))
        this.loadData()
      })
    },
    handleDelete(record) {
      this.deleteRelationType(record.id)
    },
    deleteRelationType(id) {
      deleteRelationType(id).then((res) => {
        this.$message.success(this.$t('deleteSuccess'))
        this.loadData()
      })
    },
    customCloseEdit(value, $event) {
      // enter, close edit
      if ($event.keyCode === 13) {
        const $table = this.$refs.relationTypeTable
        $table.clearActived()
      }
    },
  },
  watch: {},
}
</script>

<style lang="less" scoped>
.color-swatch {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  vertical-align: middle;
}
</style>
