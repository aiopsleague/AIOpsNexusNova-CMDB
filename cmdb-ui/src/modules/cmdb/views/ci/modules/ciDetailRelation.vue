<template>
  <div class="ci-detail-relation">
    <CiDetailRelationTopo ref="ciDetailRelationTopo" :parentCITypeList="relationData.parentCITypeList" :childCITypeList="relationData.childCITypeList" @nodeDblclick="handleNodeDblclick"/>
  </div>
</template>

<script>
import CiDetailRelationTopo from './ciDetailRelationTopo/index.vue'
import Node from './ciDetailRelationTopo/node.js'

export default {
  name: 'CIDetailRelation',
  components: { CiDetailRelationTopo },
  props: {
    ciId: {
      type: Number,
      default: 0,
    },
    typeId: {
      type: Number,
      default: 0,
    },
    ci: {
      type: Object,
      default: () => {},
    },
    relationData: {
      type: Object,
      default: () => {}
    }
  },
  data() {
    return {
      firstCIs: {},
      secondCIs: {},
      topoData: {
        nodes: {},
        edges: []
      },
    }
  },
  computed: {
    // 优先从当前 CI 数据获取实际类型 ID，兜底使用 prop（兼容初次加载时 ci 尚未就绪）
    currentTypeId() {
      return (this.ci && this.ci._type) || this.typeId
    },
    exsited_ci() {
      const _exsited_ci = [this.ciId]
      this.relationData.parentCITypeList.forEach((parent) => {
        if (this.firstCIs[parent.name]) {
          this.firstCIs[parent.name].forEach((parentCi) => {
            _exsited_ci.push(parentCi._id)
          })
        }
      })
      this.relationData.childCITypeList.forEach((child) => {
        if (this.secondCIs[child.name]) {
          this.secondCIs[child.name].forEach((childCi) => {
            _exsited_ci.push(childCi._id)
          })
        }
      })
      return _exsited_ci
    },
  },
  inject: {
    attrList: { from: 'attrList' },
    attributes: { from: 'attributes' },
    ci_types: { from: 'ci_types' },
    relationViewRefreshNumber: {
      from: 'relationViewRefreshNumber',
      default: () => null,
    },
  },

  watch: {
    relationData: {
      immediate: true,
      deep: true,
      handler(val) {
        this.init(val)
      }
    }
  },

  methods: {
    async init(relationData) {
      const ci_types_list = this.ci_types()
      const _findCiType = ci_types_list.find((item) => item.id === this.currentTypeId)
      if (!_findCiType) {
        return
      }

      this.getFirstCIs(relationData.parentCIList)
      this.getSecondCIs(relationData.childCIList)

      this.handleTopoData()
      this.$nextTick(() => {
        if (this.$refs.ciDetailRelationTopo) {
          this.$refs.ciDetailRelationTopo.exsited_ci = this.exsited_ci
          this.$refs.ciDetailRelationTopo.setTopoData(this.topoData)
        }
      })
    },
    async getFirstCIs(parentCIList) {
      const firstCIs = {}
      parentCIList.forEach((item) => {
        if (item.ci_type in firstCIs) {
          firstCIs[item.ci_type].push(item)
        } else {
          firstCIs[item.ci_type] = [item]
        }
      })
      this.firstCIs = firstCIs
    },
    async getSecondCIs(childCIList) {
      const secondCIs = {}
      childCIList.forEach((item) => {
        if (item.ci_type in secondCIs) {
          secondCIs[item.ci_type].push(item)
        } else {
          secondCIs[item.ci_type] = [item]
        }
      })
      this.secondCIs = secondCIs
    },

    // 双击拓扑节点：通知父组件导航到目标 CI
    handleNodeDblclick({ typeId, ciId }) {
      if (!typeId || !ciId) {
        return
      }
      if (typeId === this.currentTypeId && ciId === this.ciId) {
        return // 当前 CI 自身，无需跳转
      }
      // 将导航事件向上冒泡，由父组件（ciDetailTab）决定如何导航：
      // - 抽屉场景：直接调用 create() 原地刷新，URL 不变
      // - 独立页面场景：ciDetailPage 进一步更新路由 URL
      this.$emit('navigateToCi', { typeId, ciId })
    },

    handleTopoData() {
      const ci_types_list = this.ci_types()
      if (!ci_types_list?.length) {
        this.$set(this, 'topoData', {
          nodes: {},
          edges: []
        })
        return
      }

      const _findCiType = ci_types_list.find((item) => item.id === this.currentTypeId)
      const unique_id = _findCiType.show_id || _findCiType.unique_id
      const _findUnique = this.attrList().find((attr) => attr.id === unique_id)
      const unique_name = _findUnique?.name
      const unique_alias = _findUnique?.alias || _findUnique?.name || ''

      const nodes = {
        isRoot: true,
        id: `Root_${this.currentTypeId}`,
        title: _findCiType.alias || _findCiType.name, // 中文名
        name: _findCiType.name, // 英文名
        Class: Node,
        unique_alias,
        unique_name,
        unique_value: this.ci[unique_name],
        ci: this.ci, // 悬停详情用的完整 CI 数据
        attributes: this.attrList(), // 悬停详情用的属性元数据
        icon: _findCiType?.icon || '',
        endpoints: [
          {
            id: 'left',
            orientation: [-1, 0],
            pos: [0, 0.5],
          },
          {
            id: 'right',
            orientation: [1, 0],
            pos: [0, 0.5],
          },
        ],
        children: [],
      }
      const edges = []
      this.relationData.parentCITypeList.forEach((parent) => {
        const _findCiType = ci_types_list.find((item) => item.id === parent.id)
        if (this.firstCIs[parent.name] && _findCiType) {
          const unique_id = _findCiType.show_id || _findCiType.unique_id
          const _findUnique = parent.attributes.find((attr) => attr.id === unique_id)
          const unique_name = _findUnique?.name
          const unique_alias = _findUnique?.alias || _findUnique?.name || ''
          this.firstCIs[parent.name].forEach((parentCi) => {
            nodes.children.push({
              id: `${parentCi._id}`,
              Class: Node,
              title: parent.alias || parent.name,
              name: parent.name,
              side: 'left',
              unique_alias,
              unique_name,
              unique_value: parentCi[unique_name],
              ci: parentCi, // 悬停详情用的完整 CI 数据
              attributes: parent.attributes, // 悬停详情用的属性元数据
              ci_id: parentCi._id, // 双击跳转拓扑关系用
              ci_type_id: parent.id, // 双击跳转拓扑关系用
              children: [],
              icon: _findCiType?.icon || '',
              endpoints: [
                {
                  id: 'left',
                  orientation: [-1, 0],
                  pos: [0, 0.5],
                },
                {
                  id: 'right',
                  orientation: [1, 0],
                  pos: [0, 0.5],
                },
              ],
            })
            edges.push({
              id: `${parentCi._id}_Root`,
              source: 'right',
              target: 'left',
              sourceNode: `${parentCi._id}`,
              targetNode: `Root_${this.currentTypeId}`,
              type: 'endpoint',
              label: parent.relation_type || '',
              labelPosition: 0.5,
              strokeColor: parent.relation_type_color || '#1890ff',
            })
          })
        }
      })
      this.relationData.childCITypeList.forEach((child) => {
        const _findCiType = ci_types_list.find((item) => item.id === child.id)
        if (this.secondCIs[child.name] && _findCiType) {
          const unique_id = _findCiType.show_id || _findCiType.unique_id
          const _findUnique = child.attributes.find((attr) => attr.id === unique_id)
          const unique_name = _findUnique?.name
          const unique_alias = _findUnique?.alias || _findUnique?.name || ''
          this.secondCIs[child.name].forEach((childCi) => {
            nodes.children.push({
              id: `${childCi._id}`,
              Class: Node,
              title: child.alias || child.name,
              name: child.name,
              side: 'right',
              unique_alias,
              unique_name,
              unique_value: childCi[unique_name],
              ci: childCi, // 悬停详情用的完整 CI 数据
              attributes: child.attributes, // 悬停详情用的属性元数据
              ci_id: childCi._id, // 双击跳转拓扑关系用
              ci_type_id: child.id, // 双击跳转拓扑关系用
              children: [],
              icon: _findCiType?.icon || '',
              endpoints: [
                {
                  id: 'left',
                  orientation: [-1, 0],
                  pos: [0, 0.5],
                },
                {
                  id: 'right',
                  orientation: [1, 0],
                  pos: [0, 0.5],
                },
              ],
            })
            edges.push({
              id: `Root_${childCi._id}`,
              source: 'right',
              target: 'left',
              sourceNode: `Root_${this.currentTypeId}`,
              targetNode: `${childCi._id}`,
              type: 'endpoint',
              label: child.relation_type || '',
              labelPosition: 0.5,
              strokeColor: child.relation_type_color || '#1890ff',
            })
          })
        }
      })
      this.$set(this, 'topoData', {
        nodes,
        edges
      })
    }
  },
}
</script>

<style lang="less" scoped>
.ci-detail-relation {
  height: 100%;
}
</style>
