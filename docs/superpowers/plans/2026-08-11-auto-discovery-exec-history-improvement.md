# 自动发现池执行日志改进方案

> 改进 `AutoDiscoveryExecHistory` 的 `stdout` 内容，提升运维排查和审计能力。

---

## 现状分析

### 当前日志格式

| 操作 | stdout 内容 | 触发条件 |
|------|-------------|----------|
| 新增资源 | `add resource: {unique_value}` | 资源首次上报 |
| 更新资源 | `update resource: {unique_value}` | 已存在且 instance 发生变化 |
| 删除资源 | `delete resource: {unique_value}` | 手动删除 |
| 接纳资源 | `accept resource: {unique_value}` | 资源被接纳进 CMDB |

### 当前问题

1. **缺少上下文信息**：日志只有 `unique_value`（如 UUID），无法直接看出是哪个规则、哪种资源类型、哪个 Agent 触发的操作
2. **"无变化上报"静默**：Agent 上报了但 instance 未变时，只静默刷新 `oneagent_id`/`oneagent_name`/`updated_at`，不产生任何历史记录。无法区分"Agent 没上报"和"上报了但数据没变"
3. **update 不记录变更内容**：不知道哪些字段发生了变化，不利于审计和问题回溯

### 当前代码路径

- **模型**: `AutoDiscoveryExecHistory` (`c_ad_exec_histories`)，字段 `type_id` + `stdout`
- **业务逻辑**: `AutoDiscoveryCICRUD.upsert()` / `delete()` / `delete2()` / `accept()` — [auto_discovery.py:636-762](cmdb-api/api/lib/cmdb/auto_discovery/auto_discovery.py#L636-L762)
- **前端展示**: [discoveryCI/index.vue:489-491](cmdb-ui/src/modules/cmdb/views/discoveryCI/index.vue#L489-L491) — `[${log.created_at}] ${log.stdout}`，纯文本展示

---

## 改进方案

### 改进一：增加基础上下文信息（必须）

在所有执行历史记录的 `stdout` 中附带规则名称和 Agent 名称。

**格式变化**：

```
# 改前
add resource: 49abd990-8959-46e3-bb9b-215e614ec292

# 改后
add resource: 49abd990-8959-46e3-bb9b-215e614ec292 | rule: Linux服务器发现 | agent: node1-agent
```

**涉及的 4 处记录点**：

| 方法 | 原 stdout | 新 stdout |
|------|-----------|-----------|
| `upsert` (add) | `add resource: {unique_value}` | `add resource: {unique_value} \| rule: {adr_name} \| agent: {oneagent_name}` |
| `upsert` (update) | `update resource: {unique_value}` | `update resource: {unique_value} \| rule: {adr_name} \| agent: {oneagent_name}` |
| `delete` / `delete2` | `delete resource: {unique_value}` | `delete resource: {unique_value} \| rule: {adr_name} \| agent: -` |
| `accept` | `accept resource: {unique_value}` | `accept resource: {unique_value} \| rule: {adr_name} \| agent: -` |

> **注意**：delete 和 accept 操作是由用户在 UI 上手动触发的，不是 Agent 上报，所以 `agent` 字段显示 `-`。

### 改进二：记录"无变化同步"事件（可配置，默认关闭）

当 Agent 上报资源但 instance 数据未变化时，可记录一条 `sync resource` 日志，表明 Agent 确实在活跃上报。

**配置方式**：通过系统配置 `auto_discovery_exec_log_types` 控制记录哪些类型的日志。该配置是一个字符串列表，支持的类型：`add`、`update`、`delete`、`accept`、`sync`。

- **默认值**: `["add", "update", "delete", "accept"]` — sync 不在默认列表中
- **启用 sync**: 添加 `"sync"` 到列表

```python
# 启用 sync 日志（追加 sync 类型，保留默认的四种）
SystemConfigManager.create_or_update("auto_discovery_exec_log_types",
                                     {"v": ["add", "update", "delete", "accept", "sync"]})
```

> **使用建议**：sync 日志默认不记录，避免高频上报场景导致执行历史表膨胀。需要排查 Agent 同步问题时再开启。

### 改进三：记录变更字段（可选，建议按需实现）

在 update 时记录具体变更了哪些字段。

```
update resource: 49abd990... | rule: Linux服务器发现 | agent: node1-agent | changed: cpu_count(4→8), memory(8192→16384)
```

> 此改进会显著增加 `stdout` 字段长度，且需要对 `instance` dict 做 diff。建议在审计需求明确时再实施，本方案暂不在代码中实现。

---

## 实施影响评估

| 影响维度 | 说明 |
|----------|------|
| **向后兼容** | `stdout` 字段为纯文本，前端仅做展示，改变格式不影响功能 |
| **数据库** | 无需修改表结构，`stdout TEXT` 字段足够容纳新格式 |
| **性能** | 每次 upsert 增加 `AutoDiscoveryRule.get_by_id()` 查询（获取 adr_name）；sync 日志默认不记录，无额外开销 |
| **前端** | 无需改动，`stdout` 文本直接展示 |

---

## 实施步骤

### 后端（cmdb-api）

1. 新增 `_get_exec_log_types()` 静态方法，从 `SystemConfigManager` 读取启用的日志类型，默认 `["add", "update", "delete", "accept"]`
2. 在 `upsert` 方法中：获取 `adr_name` 和 `agent_name`，改进 add/update/sync 的 stdout 格式，并根据配置判断是否写入
3. 改进 `delete`/`delete2`/`accept` 的 stdout 格式，增加 `adr_name` 上下文，并根据配置判断是否写入

### 前端（cmdb-ui）

4. 在发现池日志弹窗（`discoveryCI/index.vue`）标题栏增加齿轮设置图标，点击展开日志类型配置面板
5. 配置面板使用 `a-checkbox-group` 展示五种日志类型（add/update/delete/accept/sync），勾选即生效
6. 通过已有的 `GET/POST /v0.1/system_config` API 读写配置，key 为 `auto_discovery_exec_log_types`
7. 新增 i18n 键 `logConfig` 和 `execLogTypes`
