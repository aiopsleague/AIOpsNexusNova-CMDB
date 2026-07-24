<template>
  <div>
    <div class="ci-detail-header">{{ this.type.alias }}</div>
    <div class="ci-detail-page">
      <ci-detail-tab ref="ciDetailTab" :typeId="typeId" :attributeHistoryTableHeight="windowHeight - 250" @navigateToCi="handleNavigateToCi" />
    </div>
  </div>
</template>

<script>
import CiDetailTab from './modules/ciDetailTab.vue'
import { getCITypeAttributesById } from '@/modules/cmdb/api/CITypeAttr'
import { getCIType } from '@/modules/cmdb/api/CIType'

export default {
  name: 'CiDetailPage',
  components: { CiDetailTab },
  data() {
    return {
      typeId: Number(this.$route.params.typeId),
      type: {},
      attrList: [],
      attributes: {},
    }
  },
  computed: {
    windowHeight() {
      return this.$store.state.windowHeight
    },
  },
  provide() {
    return {
      attrList: () => {
        return this.attrList
      },
      attributes: () => {
        return this.attributes
      },
    }
  },
  mounted() {
    this.loadByRoute()
  },
  watch: {
    // 同一路由不同参数（如双击拓扑节点跳转）时组件实例被复用，
    // mounted 不会再次触发，需要监听 $route 重新加载
    '$route'(to) {
      if (to.name === 'cmdb_ci_detail') {
        this.loadByRoute()
      }
    },
  },
  methods: {
    loadByRoute() {
      this.typeId = Number(this.$route.params.typeId)
      const { ciId = undefined } = this.$route.params
      const { tab = 'tab_1' } = this.$route.query
      if (ciId) {
        // nextTick：等 ciDetailTab 的 typeId prop 随本次变更更新后再加载
        this.$nextTick(() => {
          this.$refs.ciDetailTab.create(Number(ciId), tab)
        })
      }
      getCIType(this.typeId).then((res) => {
        this.type = res.ci_types[0]
      })
      this.getAttributeList()
    },
    // 双击拓扑节点：同步更新地址栏 URL（ciDetailTab 已原地刷新了内容）
    handleNavigateToCi({ typeId, ciId }) {
      // 已匹配当前路由，无需重复跳转
      if (
        Number(this.$route.params.typeId) === typeId &&
        Number(this.$route.params.ciId) === ciId
      ) {
        return
      }
      this.$router
        .push({
          name: 'cmdb_ci_detail',
          params: { typeId, ciId },
          query: { tab: 'tab_2' },
        })
        .catch((err) => {
          if (err?.name !== 'NavigationDuplicated') throw err
        })
    },
    async getAttributeList() {
      await getCITypeAttributesById(this.typeId).then((res) => {
        this.attrList = res.attributes
        this.attributes = res
      })
    },
  },
}
</script>

<style lang="less" scoped>
.ci-detail-header {
  border-left: 3px solid @primary-color;
  padding-left: 10px;
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 10px;
}
.ci-detail-page {
  background-color: #fff;
  height: calc(100vh - 122px);
}
</style>
