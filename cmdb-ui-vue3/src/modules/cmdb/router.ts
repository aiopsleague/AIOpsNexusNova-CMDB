// src/modules/cmdb/router.ts
import type { AppRouteRecord } from '@/stores/routeFilter'

/**
 * 纯函数：构建 cmdb 路由树。component 用字符串占位，由 `modules/index.ts` 的
 * `componentMap` 统一解析为懒加载组件（与 acl 模块一致）。
 *
 * cmdb 路由为静态路由，无异步拉取（旧 Vue2 版本会调用 getRelationView 动态
 * 移除服务树菜单项，待视图迁移后再恢复该逻辑）。
 */
export function buildCmdbRoutes(): AppRouteRecord[] {
  const cmdb: AppRouteRecord = {
    path: '/cmdb',
    name: 'cmdb',
    component: 'BasicLayout',
    meta: { title: 'CMDB', keepAlive: false },
    redirect: '/cmdb/instances/types',
    children: [
      {
        path: '/cmdb/dashboard',
        name: 'cmdb_dashboard',
        component: 'cmdbDashboard',
        meta: {
          title: 'dashboard',
          icon: 'ops-cmdb-dashboard',
          selectedIcon: 'ops-cmdb-dashboard',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/topoviews',
        name: 'cmdb_topology_views',
        component: 'cmdbTopologyView',
        meta: {
          title: 'cmdb.menu.topologyView',
          appName: 'cmdb',
          icon: 'ops-topology_view',
          selectedIcon: 'ops-topology_view',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/disabled1',
        name: 'cmdb_disabled1',
        meta: { title: 'cmdb.menu.resources', disabled: true },
      },
      {
        path: '/cmdb/relationviews/:viewId?',
        name: 'cmdb_relation_views',
        component: 'cmdbRelationViews',
        meta: {
          title: 'cmdb.menu.serviceTree',
          appName: 'cmdb',
          icon: 'veops-servicetree',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/instances/types/:typeId?',
        name: 'cmdb_resource_views',
        component: 'cmdbResourceViews',
        meta: {
          title: 'cmdb.menu.ciTable',
          icon: 'ops-cmdb-resource',
          selectedIcon: 'ops-cmdb-resource',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/tree_views',
        name: 'cmdb_tree_views',
        component: 'cmdbTreeViews',
        meta: {
          title: 'cmdb.menu.ciTree',
          icon: 'ops-cmdb-tree',
          selectedIcon: 'ops-cmdb-tree',
          keepAlive: false,
        },
        hideChildrenInMenu: true,
        children: [
          {
            path: '/cmdb/tree_views/:typeId',
            name: 'cmdb_tree_views_item',
            component: 'cmdbTreeViews',
            meta: { title: 'cmdb.menu.ciTree', keepAlive: false },
            hidden: true,
          },
        ],
      },
      {
        path: '/cmdb/resourcesearch',
        name: 'cmdb_resource_search',
        hidden: true,
        component: 'cmdbResourceSearch',
        meta: {
          title: 'cmdb.menu.ciSearch',
          icon: 'ops-cmdb-search',
          selectedIcon: 'ops-cmdb-search',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/adc',
        name: 'cmdb_auto_discovery_ci',
        component: 'cmdbDiscoveryCI',
        meta: {
          title: 'cmdb.menu.adCIs',
          icon: 'ops-cmdb-adc',
          selectedIcon: 'ops-cmdb-adc',
          keepAlive: false,
          permission: ['admin', 'cmdb_admin'],
        },
      },
      {
        path: '/cmdb/cidetail/:typeId/:ciId',
        name: 'cmdb_ci_detail',
        hidden: true,
        component: 'cmdbCiDetail',
        meta: { title: 'cmdb.menu.cidetail', keepAlive: false },
      },
      {
        path: '/cmdb/disabled4',
        name: 'cmdb_disabled4',
        meta: {
          title: 'cmdb.menu.scene',
          appName: 'cmdb',
          disabled: true,
          permission: ['admin', 'cmdb_admin'],
        },
      },
      {
        path: '/cmdb/ipam',
        name: 'cmdb_ipam',
        component: 'cmdbIpam',
        meta: {
          title: 'IPAM',
          appName: 'cmdb',
          icon: 'veops-ipam',
          selectedIcon: 'veops-ipam',
          keepAlive: false,
          permission: ['admin', 'cmdb_admin'],
        },
      },
      {
        path: '/cmdb/dcim',
        name: 'cmdb_dcim',
        component: 'cmdbDcim',
        meta: {
          title: 'cmdb.menu.dcim',
          appName: 'cmdb',
          icon: 'veops-data_center',
          selectedIcon: 'veops-data_center',
          keepAlive: false,
          permission: ['cmdb_admin', 'admin'],
        },
      },
      {
        path: '/cmdb/disabled2',
        name: 'cmdb_disabled2',
        meta: { title: 'cmdb.menu.config', disabled: true },
      },
      {
        path: '/cmdb/preference',
        name: 'cmdb_preference',
        component: 'cmdbPreference',
        meta: {
          title: 'cmdb.menu.preference',
          icon: 'ops-cmdb-preference',
          selectedIcon: 'ops-cmdb-preference',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/batch',
        name: 'cmdb_batch',
        component: 'cmdbBatch',
        meta: {
          title: 'cmdb.menu.batchUpload',
          icon: 'ops-cmdb-batch',
          selectedIcon: 'ops-cmdb-batch',
          keepAlive: false,
        },
      },
      {
        path: '/cmdb/ci_types',
        name: 'ci_type',
        component: 'cmdbCiTypes',
        meta: {
          title: 'cmdb.menu.citypeManage',
          icon: 'ops-cmdb-citype',
          selectedIcon: 'ops-cmdb-citype',
          keepAlive: false,
          permission: ['cmdb_admin', 'admin'],
        },
      },
      {
        path: '/cmdb/disabled3',
        name: 'cmdb_disabled3',
        meta: {
          title: 'cmdb.menu.backend',
          disabled: true,
          permission: ['cmdb_admin', 'OneOPS_Application_Admin', 'admin'],
        },
      },
      {
        path: '/cmdb/citypes',
        name: 'cmdb_ci_type',
        component: 'RouteView',
        redirect: '/cmdb/ci_type',
        meta: {
          title: 'cmdb.menu.backendManage',
          icon: 'veops-setting2',
          selectedIcon: 'veops-setting2',
          permission: ['cmdb_admin', 'OneOPS_Application_Admin', 'admin'],
        },
        children: [
          {
            path: '/cmdb/customdashboard',
            name: 'cmdb_custom_dashboard',
            component: 'cmdbCustomDashboard',
            meta: {
              title: 'cmdb.menu.customDashboard',
              keepAlive: false,
              icon: 'ops-cmdb-customdashboard',
              selectedIcon: 'ops-cmdb-customdashboard-selected',
            },
          },
          {
            path: '/cmdb/preferencerelation',
            name: 'preference_relation',
            component: 'cmdbPreferenceRelation',
            meta: {
              title: 'cmdb.menu.serviceTreeDefine',
              keepAlive: false,
              icon: 'ops-cmdb-preferencerelation',
              selectedIcon: 'ops-cmdb-preferencerelation-selected',
            },
          },
          {
            path: '/cmdb/discovery',
            name: 'discovery',
            component: 'cmdbDiscovery',
            meta: {
              title: 'cmdb.menu.ad',
              keepAlive: false,
              icon: 'ops-cmdb-adr',
              selectedIcon: 'ops-cmdb-adr-selected',
            },
          },
          {
            path: '/cmdb/operationhistory',
            name: 'operation_history',
            hideChildrenInMenu: true,
            component: 'cmdbOperationHistory',
            meta: {
              title: 'cmdb.menu.operationHistory',
              keepAlive: false,
              icon: 'ops-cmdb-operation',
              selectedIcon: 'ops-cmdb-operation-selected',
            },
          },
          {
            path: '/cmdb/modelrelation',
            name: 'model_relation',
            hideChildrenInMenu: true,
            component: 'cmdbModelRelation',
            meta: {
              title: 'cmdb.menu.citypeRelation',
              keepAlive: false,
              icon: 'ops-cmdb-modelrelation',
              selectedIcon: 'ops-cmdb-modelrelation-selected',
            },
          },
          {
            path: '/cmdb/relationtype',
            name: 'relation_type',
            hideChildrenInMenu: true,
            component: 'cmdbRelationType',
            meta: {
              title: 'cmdb.menu.relationType',
              keepAlive: false,
              icon: 'ops-cmdb-relationtype',
              selectedIcon: 'ops-cmdb-relationtype-selected',
            },
          },
        ],
      },
    ],
  }

  const mobile: AppRouteRecord = {
    path: '/cmdb/mobile/:typeId/:ciId',
    name: 'cmdb_mobile_detail',
    hidden: true,
    component: 'cmdbMobileDetail',
    meta: { title: 'cmdb.ci.mobileDetail' },
  }

  return [cmdb, mobile]
}
