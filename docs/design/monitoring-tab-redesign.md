# CI 详情监控Tab 重构设计方案

## 1. 背景与目标

### 1.1 当前状态
- CI 详情页有一个固定显示的 "Grafana" Tab（tab_6），无论 CI 类型是否配置了 Grafana 仪表板映射都会显示
- Tab 名称为硬编码的 "Grafana"
- Grafana 配置存储在后端 `CommonData` 表（`data_type='Grafana'`），加密为一个 JSON，结构为：
  ```json
  {
    "connections": [{ "id": 1, "name": "...", "url": "...", "api_key": "...", "enable": 1 }],
    "mappings": [{ "id": 1, "ci_type_id": 5, "connection_id": 1, "dashboard_name": "...", ... }]
  }
  ```
- 后端 API：`GET /v0.1/ci/{ci_id}/grafana` → `resolve_ci_grafana()`
- 前端 API：`getCIGrafana(ciId)` 在 `cmdb-ui/src/modules/cmdb/api/ci.js`

### 1.2 目标
1. **重命名**：将 "Grafana" Tab 改为 **"监控"**（Monitoring）
2. **可扩展**：使监控 Tab 能根据配置支持 Grafana、Zabbix 或其他监控工具，**默认行为仍是 Grafana**
3. **条件显示**：如果 CI 类型没有任何监控仪表板映射（Grafana、Zabbix 等），则**不显示监控 Tab**

## 2. 架构设计

### 2.1 数据流

```
┌──────────────────────────────────────────────────────────────────┐
│  CI 详情页加载                                                    │
│  ciDetailTab.create(ciId)                                        │
│    │                                                              │
│    ├── 1. getCI() → 获取 CI 数据，得到 ci_type_id                  │
│    ├── 2. checkCITypeMonitoring(ci_type_id) → 检查是否有监控配置    │
│    │       └── GET /v0.1/ci_type/{ci_type_id}/monitoring/check    │
│    ├── 3. hasMonitoring ? 显示"监控"Tab : 隐藏                     │
│    └── 4. 用户点击监控 Tab → 加载 CiDetailMonitoring 组件          │
│            └── GET /v0.1/ci/{ci_id}/monitoring                     │
│                 └── 返回 { tool_type, ... } → 路由到对应组件        │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 组件关系

```
ciDetailTab.vue (Tab 容器)
  ├── tab_1: 详情
  ├── tab_2: 拓扑
  ├── tab_3: 变更记录
  ├── tab_4: 触发器记录
  ├── tab_5: 关联ITSM
  └── tab_6: 监控 [条件显示: v-if="hasMonitoring"]
       └── CiDetailMonitoring.vue (新建，替代 CiDetailGrafana)
            ├── 根据 tool_type 动态渲染：
            │   ├── tool_type="grafana" → CiDetailGrafana (现有实现)
            │   ├── tool_type="zabbix"  → CiDetailZabbix (未来扩展)
            │   └── tool_type="..."     → CiDetailXxx (未来扩展)
            └── 当前默认 tool_type = "grafana"
```

## 3. 后端变更

### 3.1 新增 API：检查 CI 类型是否有监控配置

**端点**：`GET /v0.1/ci_type/{ci_type_id}/monitoring/check`

**功能**：快速检查指定 CI 类型是否配置了任何监控仪表板映射，用于前端决定是否显示"监控"Tab。

**实现文件**：`cmdb-api/api/views/cmdb/grafana.py`（新增路由函数）

**请求**：
```
GET /api/v0.1/ci_type/5/monitoring/check
```

**响应**：
```json
{
  "has_monitoring": true
}
```

**后端逻辑**：
```python
# cmdb-api/api/lib/cmdb/grafana.py

def check_ci_type_monitoring(ci_type_id):
    """检查 CI 类型是否配置了任何监控仪表板映射"""
    from api.lib.common_setting.grafana import GrafanaConfigCRUD
    config = GrafanaConfigCRUD().get_config()
    mappings = config.get("mappings", [])
    connections = config.get("connections", [])
    
    if not connections:
        return {"has_monitoring": False}
    
    # 检查是否有该 CI 类型的启用映射
    type_mappings = [m for m in mappings 
                     if m.get("ci_type_id") == ci_type_id 
                     and m.get("enable", 1) != 0]
    
    return {"has_monitoring": len(type_mappings) > 0}
```

### 3.2 修改现有 API：增加 tool_type 字段

**端点**：`GET /v0.1/ci/{ci_id}/grafana`（保持不变，兼容旧版）

**修改内容**：在 `resolve_ci_grafana()` 返回值中增加 `has_monitoring` 和 `tool_type` 字段。

**修改文件**：`cmdb-api/api/lib/cmdb/grafana.py`

**修改后的响应格式**：
```json
{
  "configured": true,
  "has_monitoring": true,
  "tool_type": "grafana",
  "result": {
    "connection_id": 1,
    "grafana_url": "https://grafana.example.com",
    "uid": "abc123",
    "slug": "my-dashboard",
    "vars": [...]
  }
}
```

**关键修改点**（`resolve_ci_grafana` 函数）：
- 在返回结果中增加 `"has_monitoring": true/false` — 表示该 CI 所属类型是否有监控映射
- 在返回结果中增加 `"tool_type": "grafana"` — 表示当前使用的监控工具类型（为将来扩展预留）
- 当无连接时返回 `configured: false, has_monitoring: false`
- 当无映射时返回 `configured: true, has_monitoring: false`

### 3.3 新增文件：监控抽象层（可选，为将来扩展准备）

**文件**：`cmdb-api/api/lib/cmdb/monitoring.py`

这个文件作为监控工具的抽象层，当前只是一个薄封装，委托给 Grafana：

```python
# 监控工具类型常量
MONITORING_TOOL_GRAFANA = "grafana"
MONITORING_TOOL_ZABBIX = "zabbix"

# 支持的监控工具类型列表
SUPPORTED_MONITORING_TOOLS = [MONITORING_TOOL_GRAFANA]

def resolve_ci_monitoring(ci_id):
    """解析 CI 的监控仪表板（支持多种工具类型）"""
    result = resolve_ci_grafana(ci_id)
    if result.get("configured") and result.get("result"):
        result["tool_type"] = MONITORING_TOOL_GRAFANA
    return result
```

> **注意**：这个文件在当前阶段是可选的。如果团队认为当前只需最小变动，可以直接在 grafana.py 中修改，将来 Zabbix 等加入时再抽取抽象层。

### 3.4 注册新路由

**文件**：`cmdb-api/api/views/cmdb/grafana.py`

新增路由：
```python
@router.get("/ci_type/{ci_type_id:int}/monitoring/check")
def ci_type_monitoring_check(ci_type_id: int):
    return check_ci_type_monitoring(ci_type_id)
```

### 3.5 不变的部分
- Grafana 配置的存储方式不变（`CommonData` 表，`data_type='Grafana'`）
- `GrafanaConfigCRUD` 类不变
- `GrafanaClient` 类不变
- `pick_dashboard`、`build_vars` 等工具函数不变
- 现有的 Grafana Proxy 路由不变
- 现有的 Grafana 管理设置页面不变

## 4. 前端变更

### 4.1 新增 API 函数

**文件**：`cmdb-ui/src/modules/cmdb/api/ci.js`

```javascript
// 检查 CI 类型是否有监控配置
export function checkCITypeMonitoring(ciTypeId) {
  return axios({
    url: `${urlPrefix}/ci_type/${ciTypeId}/monitoring/check`,
    method: 'GET'
  })
}

// 获取 CI 的监控仪表板配置（替代 getCIGrafana，但保留兼容）
export function getCIMonitoring(ciId) {
  return axios({
    url: `${urlPrefix}/ci/${ciId}/grafana`,  // 复用现有端点
    method: 'GET'
  })
}
```

### 4.2 修改 i18n 语言文件

**文件**：`cmdb-ui/src/modules/cmdb/lang/zh.js`

```javascript
// 修改前：
grafana: 'Grafana',
// 修改后：
monitoring: '监控',
// 保留旧 key 兼容：
grafana: '监控',
```

**文件**：`cmdb-ui/src/modules/cmdb/lang/en.js`

```javascript
// 修改前：
grafana: 'Grafana',
// 修改后：
monitoring: 'Monitoring',
// 保留旧 key 兼容：
grafana: 'Monitoring',
```

### 4.3 新建 CiDetailMonitoring 组件（容器组件）

**文件**：`cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailMonitoring.vue`

这是一个轻量级容器组件，根据 `tool_type` 动态渲染对应的监控工具组件：

```vue
<template>
  <div class="ci-detail-monitoring">
    <CiDetailGrafana v-if="toolType === 'grafana'" :ciId="ciId" />
    <!-- 未来扩展：
    <CiDetailZabbix v-else-if="toolType === 'zabbix'" :ciId="ciId" />
    -->
    <a-empty v-else ... />
  </div>
</template>

<script>
import CiDetailGrafana from './ciDetailGrafana.vue'

export default {
  name: 'CiDetailMonitoring',
  components: { CiDetailGrafana },
  props: {
    ciId: { type: Number, required: true },
    toolType: { type: String, default: 'grafana' }
  }
}
</script>
```

### 4.4 修改 ciDetailTab.vue

**文件**：`cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue`

**修改点 1**：Tab 标签名和图标
```vue
<!-- 修改前 -->
<a-tab-pane key="tab_6">
  <span slot="tab"><a-icon type="dashboard" />{{ $t('cmdb.ci.grafana') }}</span>

<!-- 修改后 -->
<a-tab-pane key="tab_6" v-if="hasMonitoring">
  <span slot="tab"><ops-icon type="veops-monitor" />{{ $t('cmdb.ci.monitoring') }}</span>
```

**修改点 2**：组件引用
```vue
<!-- 修改前 -->
<CiDetailGrafana v-if="ciId" :key="ciId" :ciId="ciId" />

<!-- 修改后 -->
<CiDetailMonitoring v-if="ciId" :key="ciId" :ciId="ciId" :toolType="monitoringToolType" />
```

**修改点 3**：data 中新增字段
```javascript
data() {
  return {
    // ...existing fields...
    hasMonitoring: false,         // 是否显示监控 Tab
    monitoringToolType: 'grafana', // 监控工具类型，默认 grafana
  }
}
```

**修改点 4**：`create()` 方法中增加监控检查
```javascript
async create(ciId, activeTabKey = 'tab_1', typeId = null) {
  // ...existing code...
  await this.getCI()
  if (this.hasPermission) {
    // ...existing code...
    await this.checkMonitoring()  // 新增：检查是否有监控配置
  }
}

async checkMonitoring() {
  try {
    const res = await checkCITypeMonitoring(this.typeId)
    this.hasMonitoring = res.has_monitoring || false
    this.monitoringToolType = res.tool_type || 'grafana'
  } catch (e) {
    this.hasMonitoring = false
  }
}
```

**修改点 5**：import 更新
```javascript
// 移除：
import CiDetailGrafana from './ciDetailGrafana.vue'
// 新增：
import CiDetailMonitoring from './ciDetailMonitoring.vue'
import { checkCITypeMonitoring } from '@/modules/cmdb/api/ci'
```

### 4.5 CiDetailGrafana.vue

**保持现有逻辑不变**，但增加对 tool_type 的感知（通过父组件传递的 prop）。

> **注意**：当前 CiDetailGrafana 的 `mounted()` 中直接调用 `load()` 加载 Grafana 数据。在 Monitoring 容器组件中，只有当该组件被渲染时（tab 被激活）才会触发 mounted。这与现有行为一致。

### 4.6 instanceDetail.vue（资源搜索侧边栏详情）

如果该实例详情也有 Grafana 相关内容，需要同步检查是否需要修改。根据代码分析，`instanceDetail.vue` 没有直接引用 Grafana Tab，仅使用 `CiDetailTab`，因此无需额外修改。

## 5. 测试计划

### 5.1 后端测试
- [ ] `GET /v0.1/ci_type/{ci_type_id}/monitoring/check` 无映射时返回 `{"has_monitoring": false}`
- [ ] `GET /v0.1/ci_type/{ci_type_id}/monitoring/check` 有映射时返回 `{"has_monitoring": true}`
- [ ] `GET /v0.1/ci_type/{ci_type_id}/monitoring/check` 无连接时返回 `{"has_monitoring": false}`
- [ ] `GET /v0.1/ci_type/{ci_type_id}/monitoring/check` 映射被禁用时返回 `{"has_monitoring": false}`
- [ ] `GET /v0.1/ci/{ci_id}/grafana` 响应新增 `has_monitoring` 和 `tool_type` 字段
- [ ] 现有 Grafana 管理设置页面功能正常

### 5.2 前端测试
- [ ] CI 类型配置了 Grafana 映射时，显示"监控"Tab
- [ ] CI 类型未配置 Grafana 映射时，不显示"监控"Tab
- [ ] Grafana 未配置连接时，不显示"监控"Tab
- [ ] 点击"监控"Tab 正常加载 Grafana 仪表板 iframe
- [ ] i18n 切换中英文正常
- [ ] CI 详情页其他 Tab 功能不受影响
- [ ] 资源搜索侧边栏的 CI 详情抽屉正常

## 6. 实施步骤

| 步骤 | 内容 | 影响文件 |
|------|------|----------|
| 1 | 后端：新增 `check_ci_type_monitoring()` 函数 | `cmdb-api/api/lib/cmdb/grafana.py` |
| 2 | 后端：修改 `resolve_ci_grafana()` 增加字段 | `cmdb-api/api/lib/cmdb/grafana.py` |
| 3 | 后端：新增 `/ci_type/{ci_type_id}/monitoring/check` 路由 | `cmdb-api/api/views/cmdb/grafana.py` |
| 4 | 前端：新增 `checkCITypeMonitoring` API 函数 | `cmdb-ui/src/modules/cmdb/api/ci.js` |
| 5 | 前端：修改 i18n 语言文件 | `cmdb-ui/src/modules/cmdb/lang/zh.js`, `en.js` |
| 6 | 前端：新建 `CiDetailMonitoring.vue` 容器组件 | `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailMonitoring.vue` |
| 7 | 前端：修改 `ciDetailTab.vue` 条件渲染 + 标签名 | `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailTab.vue` |

## 7. 向后兼容性

- 旧 API `GET /v0.1/ci/{ci_id}/grafana` 保持可用，响应格式仅增加字段不删除字段
- 旧的 i18n key `cmdb.ci.grafana` 保留，值更新为"监控"
- 旧的 `CiDetailGrafana` 组件保留不变
- Grafana 管理后台设置页面完全不变

## 8. 未来扩展指引

当需要支持 Zabbix 或其他监控工具时：

1. **配置层**：在 mappings 中增加 `tool_type` 字段（当前默认为 "grafana"），或新建独立的 Zabbix 配置存储
2. **后端**：
   - 在 `resolve_ci_monitoring()` 中根据 `tool_type` 分派到不同的解析器
   - 新增 Zabbix 相关的 client 和 resolver（类比 `grafana_client.py` / `grafana.py`）
   - 新增 Zabbix proxy 路由（类比 grafana proxy）
3. **前端**：
   - 在 `CiDetailMonitoring.vue` 中增加新工具类型的条件渲染
   - 新建对应的 viewer 组件（如 `CiDetailZabbix.vue`）
   - 在设置页面增加 Zabbix 配置管理
