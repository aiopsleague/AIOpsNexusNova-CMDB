<template>
  <div class="ci-detail-relation-topo" :style="{ width: '100%', height: '100%', position: 'relative' }">
    <div
      id="ci-detail-relation-topo"
      :style="{ width: '100%', height: '100%' }"
    ></div>
    <div class="topo-layout-switch">
      <a-radio-group
        v-model="currentLayout"
        size="small"
        button-style="solid"
        @change="switchLayout"
      >
        <a-radio-button value="mindmap">
          <a-icon type="apartment" />
          {{ $t('cmdb.topo.layoutMindmap') }}
        </a-radio-button>
        <a-radio-button value="compactBox">
          <a-icon type="cluster" />
          {{ $t('cmdb.topo.layoutCompactBox') }}
        </a-radio-button>
      </a-radio-group>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'
import { TreeCanvas } from 'butterfly-dag'
import { searchCIRelation } from '@/modules/cmdb/api/CIRelation'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import Node from './node.js'

import 'butterfly-dag/dist/index.css'
import './index.less'

export default {
  name: 'CiDetailRelationTopo',
  data() {
    return {
      topoData: {},
      exsited_ci: [],
      currentLayout: 'mindmap',
    }
  },
  inject: ['ci_types'],
  computed: {
    layoutOptions() {
      const canvas = document.createElement('canvas')
      const context = canvas.getContext('2d')
      context.font = '16px'

      const measureWidth = (d) => {
        const metrics = context.measureText(d?.title || '')
        return metrics.width + 20 + 4 + 40
      }

      const layouts = {
        mindmap: {
          type: 'mindmap',
          options: {
            direction: 'H',
            getSide(d) {
              return d.data.side || 'right'
            },
            getHeight(d) { return 10 },
            getWidth: measureWidth,
            getHGap(d) { return 80 },
            getVGap(d) { return 40 },
          },
        },
        compactBox: {
          type: 'compactBox',
          options: {
            direction: 'LR',
            getHeight(d) { return 10 },
            getWidth: measureWidth,
            getHGap(d) { return 60 },
            getVGap(d) { return 30 },
          },
        },
      }
      return layouts[this.currentLayout] || layouts.mindmap
    },
  },
  methods: {
    init() {
      const root = document.getElementById('ci-detail-relation-topo')
      const layoutConfig = this.layoutOptions

      this.canvas = new TreeCanvas({
        root: root,
        disLinkable: false, // 可删除连线
        linkable: false, // 可连线
        draggable: true, // 可拖动
        zoomable: true, // 可放大
        moveable: true, // 可平移
        theme: {
          edge: {
            shapeType: 'AdvancedBezier',
            arrow: true,
            arrowPosition: 1,
          },
        },
        layout: layoutConfig,
      })
      this.canvas.setZoomable(true, true)

      this.canvas.on('events', ({ type, data }) => {
        const sourceNode = data?.id || null
        if (type === 'custom:clickLeft') {
          this.debounceClick(sourceNode, 1)
        }
        if (type === 'custom:clickRight') {
          this.debounceClick(sourceNode, 0)
        }
        if (type === 'custom:dblclickNode') {
          const { ci_id, ci_type_id } = data || {}
          if (ci_id && ci_type_id) {
            this.$emit('nodeDblclick', { ciId: Number(ci_id), typeId: Number(ci_type_id) })
          }
        }
      })
    },

    debounceClick: _.debounce(function(sourceNode, reverse) {
      searchCIRelation(`root_id=${Number(sourceNode)}&level=1&reverse=${reverse}&count=10000`).then((res) => {
        this.redrawData(res, sourceNode, reverse === 1 ? 'left' : 'right')
      })
    }, 300),

    switchLayout() {
      // Re-render existing data with new layout
      if (this.topoData && Object.keys(this.topoData).length) {
        this.setTopoData(this.topoData)
      }
    },

    setTopoData(data) {
      const root = document.getElementById('ci-detail-relation-topo')
      if (root && root?.innerHTML) {
        root.innerHTML = ''
      }
      this.canvas = null
      this.init()
      this.topoData = _.cloneDeep(data)

      this.canvas.redraw(data, {}, () => {
        this.canvas.focusCenterWithAnimate()
      })
    },
    async redrawData(res, sourceNode, side) {
      const newNodes = []
      const newEdges = []
      if (!res.result.length) {
        this.$message.info(this.$t('cmdb.ci.noLevel'))
        return
      }
      const ci_types_list = this.ci_types()
      for (let i = 0; i < res.result.length; i++) {
        const r = res.result[i]
        if (!this.exsited_ci.includes(r._id)) {
          const _findCiType = ci_types_list.find((item) => item.id === r._type)
          if (_findCiType) {
            const { attributes } = await getCITypeAttributesById(_findCiType.id)
            const unique_id = _findCiType.show_id || _findCiType.unique_id
            const _findUnique = attributes.find((attr) => attr.id === unique_id)
            const unique_name = _findUnique?.name
            const unique_alias = _findUnique?.alias || _findUnique?.name || ''
            newNodes.push({
              id: `${r._id}`,
              Class: Node,
              title: r.ci_type_alias || r.ci_type,
              name: r.ci_type,
              side: side,
              unique_alias,
              unique_name,
              unique_value: r[unique_name],
              ci: r, // 悬停详情用的完整 CI 数据
              attributes, // 悬停详情用的属性元数据
              ci_id: r._id, // 双击跳转拓扑关系用
              ci_type_id: r._type, // 双击跳转拓扑关系用
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
          }
        }
        newEdges.push({
          id: `${r._id}`,
          source: 'right',
          target: 'left',
          sourceNode: side === 'right' ? sourceNode : `${r._id}`,
          targetNode: side === 'right' ? `${r._id}` : sourceNode,
          type: 'endpoint',
        })
      }

      const { nodes, edges } = this.canvas.getDataMap()
      // 删除原节点和边
      this.canvas.removeNodes(nodes.map((node) => node.id))
      this.canvas.removeEdges(edges)

      const _topoData = _.cloneDeep(this.topoData)
      _topoData.edges.push(...newEdges)
      let result
      const getTreeItem = (data, id) => {
        for (let i = 0; i < data.length; i++) {
          if (data[i].id === id) {
            result = data[i] // 结果赋值
            result.edges = _topoData.edges
            break
          } else {
            if (data[i].children && data[i].children.length) {
              getTreeItem(data[i].children, id)
            }
          }
        }
      }

      getTreeItem(_topoData.nodes.children, sourceNode)
      result.children.push(...newNodes)

      this.topoData = _topoData
      this.canvas.draw(_topoData, {}, () => {})
      this.exsited_ci = [...new Set([...this.exsited_ci, ...res.result.map((r) => r._id)])]
    },
  },
}
</script>

<style></style>
