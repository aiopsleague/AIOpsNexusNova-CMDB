# 自关联模型（CI 类型自身关联）拓扑图混乱 — 修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 修复 CI 类型与自身建立关联（源模型 = 目标模型）时，拓扑图/资源数据 CI 拓扑关系图中出现节点自我连线、重复连线、展开后不断重复增长的问题。

**状态：** 已实现于分支 `fix/ci-relation-topo-self-relation`（基于 `feature-ci-relation-topo-colored-edges` 创建），**尚未提交**。

**架构：** 自关联类型在实例层面形成自环（`first_ci_id == second_ci_id`）与环路，而拓扑图采用树形布局，无法无歧义地表达环。修复在三处统一"去自环 + 去重 + 打断环路"：后端拓扑数据生成（主拓扑视图与预览的唯一数据源）、前端主拓扑视图渲染、资源数据 CI 详情拓扑（初始化 + 展开）。

**技术栈：** Python 3.12 / FastAPI / Redis；Vue 2.6 Options API / relation-graph（npm）/ butterfly-dag / Less

---

## 背景与根因

### 复现数据（连库核实）

- CI 类型 128 = `hello1111`，两条实例：**3867**（唯一值 424a1807…）、**3871**（唯一值 f5c4cb22…）
- `c_ci_relations` 中的关系（relation_type_id=5 "connect"）：
  - `3867 → 3867`（自环）
  - `3871 → 3871`（自环）
  - `3867 → 3871`（正常关系）
- 对 CI 3871 查询 `searchCIRelation`：父 = {3867, **3871(自身)**}，子 = {**3871(自身)**}

### 缺陷点

1. **后端 `cmdb-api/api/lib/cmdb/topology.py` 的 `topology_view()`**
   - 正向/反向遍历把自环链路（`from == to`）直接加入 `links`；
   - 遍历 key（`new_key`/`_ci_ids`）不去重，同一节点可被多次遍历 → 重复链路；
   - 根节点既在 `nodes` 中又出现在 `id2node` → 同一节点重复出现在 `nodes` 数组。

2. **前端主拓扑视图 `cmdb-ui/src/modules/cmdb/views/topology_view/index.vue`**
   - `showTopoView()` 直接把后端返回的 `links`/`nodes` 交给 relation-graph，无自环过滤/去重；
   - `initMoreNodesData()`（聚合分页"更多"）对子节点递归，无环路保护。

3. **资源数据 CI 详情拓扑初始化 `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue` `handleTopoData()`**
   - 把"当前 CI 是自身的父 / 是自身的子"都当作普通关系加入初始树 → 当前 CI 被加入两次（左/右各一次），再叠加根节点，形成自我连线与重复节点。**（残留问题根因，此前只修了展开逻辑）**

4. **资源数据 CI 详情拓扑展开 `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue` `redrawData()`**
   - 节点已存在（含与自身关联）仍 push 自环边 → butterfly-dag 画出节点指向自身的弧线。

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `cmdb-api/api/lib/cmdb/topology.py` | 后端 `topology_view()`：自环过滤 + `visited` 去重 + `seen_links` 边去重 + 节点去重 |
| `cmdb-ui/src/modules/cmdb/views/topology_view/index.vue` | `showTopoView()` 过滤/去重；`initMoreNodesData()` 环路保护 |
| `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue` | `handleTopoData()` 初始树跳过当前 CI 与自身的关系 |
| `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue` | `redrawData()` 跳过自环边 |

---

### Task 1: 后端 `topology_view()` — 去自环、去重、打断环路

**Files:**
- Modify: `cmdb-api/api/lib/cmdb/topology.py`

- [x] **Step 1: 在正/反向遍历前初始化去重集合**

在 `id2node = {}` 之后新增：

```python
# 自关联的模型（源模型=目标模型）在实例层面会形成自环/环路，导致拓扑图中
# 节点自我连线、同一条边重复出现、展开后不断重复增长。这里统一做两层去重：
#   visited    - 每个节点只被添加/遍历一次，打断环路并避免跨层级重复
#   seen_links - 同一条边（含双向边 A->B / B->A）只保留一条
visited = set()
seen_links = set()
```

- [x] **Step 2: 正向遍历（level > 0）过滤条件**

将 `if type_id in type_ids:` 块改为按顺序过滤：类型不匹配、自环（`to_id == from_id`）、已访问（`to_id in visited`）、边已存在（`tuple(sorted((from_id, to_id)))`）。通过过滤后才 append link / 写入 `id2node` / 标记 `visited` / 加入 `new_key` / 补充 `type2meta`。

- [x] **Step 3: 反向遍历（level < 0）同样处理**

对 `from_id` 应用相同的自环、`visited`、`seen_links` 过滤；`visited` 集合与正向遍历**共享**，避免同一节点在正向与反向两侧重复出现。

- [x] **Step 4: 节点列表按 id 去重**

在 `nodes.extend(id2node.values())` 之后，用 `node_ids = set()` 对 `nodes` 按 `node['id']` 去重（根节点与子节点重叠时只保留一条）。

- [x] **Step 5: 验证**

```bash
cd cmdb-api && uv run ruff check api/lib/cmdb/topology.py --select E,F,W
```

```bash
# 实测预览接口（与 /topology_views/{id}/view 共用同一方法）
curl -s -X POST http://localhost:5000/api/v0.1/topology_views/preview \
  -H 'X-Real-IP: 127.0.0.1' -H 'Content-Type: application/json' \
  -d '{"central_node_type": 128, "central_node_instances": "q=_type:(128)", "path": {"0": ["128"], "1": ["128"]}}'
# 期望返回：nodes=[3867, 3871]，links=[{3867 -> 3871}]，无自环、无重复
```

- [x] **Step 6: 提交**（待用户确认后统一提交）

---

### Task 2: 前端主拓扑视图 — `showTopoView` 过滤与去重

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/topology_view/index.vue`

- [x] **Step 1: 构建 `links` 时过滤自环并去重**

在 `showTopoView` 中：

```js
const seenLinks = new Set()
res.links.forEach(item => {
  const from = `${item.from}`
  const to = `${item.to}`
  if (!from || !to || from === to) {
    return
  }
  const linkKey = from < to ? `${from}->${to}` : `${to}->${from}`
  if (seenLinks.has(linkKey)) {
    return
  }
  seenLinks.add(linkKey)
  links.push({ from, to, disableDefaultClickEffect: false })
})
```

- [x] **Step 2: 构建 `nodes` 时按 id 去重**

```js
const nodeIds = new Set()
res.nodes.forEach(item => {
  const id = `${item.id}`
  if (nodeIds.has(id)) {
    return
  }
  nodeIds.add(id)
  nodes.push({ id, text: item.name, /* ...原有字段... */ })
})
```

- [x] **Step 3: 验证**

```bash
cd cmdb-ui && node_modules/.bin/eslint src/modules/cmdb/views/topology_view/index.vue
```

---

### Task 3: 前端主拓扑视图 — `initMoreNodesData` 环路保护

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/topology_view/index.vue`

- [x] **Step 1: 增加 `visited` 集合参数并守卫递归**

```js
initMoreNodesData(node, jsonData, visited) {
  const childs = node.lot.childs
  if (!childs?.length) {
    return
  }
  // 防止自关联形成的环路导致递归无限/重复增长
  if (!visited) {
    visited = new Set()
  }
  if (visited.has(node.id)) {
    return
  }
  visited.add(node.id)
  // ... 原有逻辑 ...
  this.initMoreNodesData(childNode, jsonData, visited)
}
```

---

### Task 4: 资源数据 CI 详情拓扑 — 初始化渲染跳过自身关系

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue`

- [x] **Step 1: 父节点循环跳过当前 CI 自身**

在 `handleTopoData()` 的 `this.firstCIs[parent.name].forEach((parentCi) => {...})` 块内、`nodes.children.push` 之前：

```js
// 跳过当前 CI 与自身建立的关系，避免初始树中出现自我连线/重复节点
if (Number(parentCi._id) === Number(this.ciId)) {
  return
}
```

- [x] **Step 2: 子节点循环跳过当前 CI 自身**

在 `this.secondCIs[child.name].forEach((childCi) => {...})` 块内、`nodes.children.push` 之前：

```js
// 跳过当前 CI 与自身建立的关系，避免初始树中出现自我连线/重复节点
if (Number(childCi._id) === Number(this.ciId)) {
  return
}
```

- [x] **Step 3: 验证**

```bash
cd cmdb-ui && node_modules/.bin/eslint src/modules/cmdb/views/ci/modules/ciDetailRelation.vue
```

---

### Task 5: 资源数据 CI 详情拓扑 — 展开跳过自环边

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue`

- [x] **Step 1: `redrawData` 循环开头跳过自环**

```js
for (let i = 0; i < res.result.length; i++) {
  const r = res.result[i]
  // 自关联（节点与自身建立关系）：跳过，避免在节点上画出自我连线的自环弧线
  if (String(r._id) === String(sourceNode)) {
    continue
  }
  // ... 原有逻辑 ...
}
```

- [x] **Step 2: 验证**

```bash
cd cmdb-ui && node_modules/.bin/eslint src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue
```

---

### Task 6: 整体验证

- [ ] **Step 1: 后端 lint 与语法检查**

```bash
cd cmdb-api && uv run ruff check api/lib/cmdb/topology.py --select E,F,W
uv run python -c "import ast; ast.parse(open('api/lib/cmdb/topology.py').read())"
```

- [ ] **Step 2: 实测后端预览接口**

使用 hello1111（type 128）数据构造 preview 请求（见 Task 1 Step 5），确认返回 `links` 无自环、无重复，`nodes` 无重复 id；多级自关联 path（如 `{"0":["128"],"1":["128"],"2":["128"]}`）同样干净。

- [ ] **Step 3: 前端手工验证**

在前端页面强制刷新（Ctrl/Cmd+Shift+R，HMR 对嵌套组件有时需整页刷新）后：
1. 主拓扑视图：两条实例各出现一次、彼此保留一条连线、无自身连线；
2. 点击节点右侧"+"展开/折叠：层级有限、不再重复堆积；
3. 拓扑视图预览（preview）同样正常；
4. 资源数据 → CI 详情 → 拓扑关系：初始渲染与展开均不再出现自环弧线/重复节点。

- [ ] **Step 4: 提交**

```bash
git add cmdb-api/api/lib/cmdb/topology.py \
        cmdb-ui/src/modules/cmdb/views/topology_view/index.vue \
        cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue \
        cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue
git commit -m "fix: handle self-relation CI types in topology views

Skip self-loop edges, dedupe links/nodes, and break cycles caused by
self-referencing CI types (source model = target model) in the main
topology view and CI detail relation graph.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## 备注

- **数据层不动**：本方案仅修复展示逻辑，不禁止创建"实例与自身关联（A→A）"的数据。如后续希望禁止此类数据，可在 `CIRelationManager.add` 增加校验，另行评估。
- **菱形结构取舍**：当图中一个节点有多个父节点时，本方案只保留首个父路径的边。这与前端树形布局器 `lot.eached`"每节点只放置一次"的行为一致，属于预期取舍。
- **关系表格（`ciRelationTable.vue`）**：展示真实关系数据，自关联在表格中按普通数据展示，不随本方案改动。
