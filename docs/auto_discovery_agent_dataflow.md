# CMDB 与 OneAgent / OneMaster 的数据流分析

> 本文基于 `cmdb-api` 源码分析（非产品文档），回答以下问题：
> 1. CMDB 是否主动拉取 OneAgent 的数据？
> 2. CMDB 是否主动拉取 OneMaster 的数据？
> 3. OneAgent 是向 OneMaster 推送数据，还是向 CMDB 推送？
> 4. OneMaster 是否向 CMDB 推送数据？
> 5. OneMaster 如何向 CMDB 推送数据？
> 6. 自动发现的工作原理。

---

## 结论速览

| 问题 | 结论 |
| --- | --- |
| CMDB 主动拉取 OneAgent 数据？ | **否**。CMDB 从不主动连接 OneAgent，反向是 OneAgent 主动拉取 CMDB 的规则 |
| CMDB 主动拉取 OneMaster 数据？ | **否**。同上，OneMaster 只是 agent_id 为 0 的特殊 OneAgent |
| OneAgent 推给 OneMaster 还是 CMDB？ | **直接推给 CMDB**（`POST /api/v0.1/adc`）。CMDB 代码里不存在 OneAgent→OneMaster 的任何调用 |
| OneMaster 是否推给 CMDB？ | **是**。走与 OneAgent 完全相同的 REST 接口 |
| OneMaster 如何推给 CMDB？ | 先 `GET /adt/sync` 拉取分配的任务（含子网扫描规则），再 `POST /adc` 上报发现实例、`POST /ipam/history/scan` 上报子网扫描结果 |
| 自动发现原理 | Agent 轮询规则 → 执行采集 → 上报实例 → CMDB 入库(暂存) → 接受后生成 CI/关系 |

关键事实：**CMDB 中只有“OneAgent”这一个身份概念（`oneagent_id`），OneMaster 没有被单独建模**。代码中唯一的区分点是 `auto_discovery.py:296` 的 `if not int(oneagent_id, 16):  # excludes master` —— 即“master”是 16 进制解析后为 0 的 agent_id（如 `0x0`）。因此 OneMaster 对 CMDB 而言就是一个 agent_id 全 0 的 OneAgent，通信机制完全相同。

---

## 1. CMDB 不主动拉取 OneAgent / OneMaster 的数据

判断依据（全部来自代码）：

1. **无出站调用点**：`cmdb-api/api/lib/http_cli.py` 提供了带 API Key 签名的出站 HTTP 助手 `api_request()`，但全仓库 grep 不到任何一处调用（`http_cli` 零使用者）。
2. **唯一的出站 `requests` 调用都不涉及 Agent**。全量检索 `requests./httpx./aiohttp` 后，出站请求只发往：
   - HR 系统（`api/views/acl/user.py:88`，`HR_URI`）
   - Vault 密钥服务（`api/commands/click_cmdb.py:373/401/435`）
   - Prometheus / Grafana（`common_setting/prometheus_client.py`、`grafana_client.py`）
   - OAuth2 第三方登录（`perm/authentication/oauth2/routing.py`）
   - Webhook / 通知（`api/lib/webhook.py`、`notify.py`）
   - 无任何指向 OneAgent / OneMaster 的 URL。
3. **Celery Beat 无“拉取”类任务**：`CMDB_BEAT_SCHEDULE`（`api/tasks/cmdb.py:503`）只有三个本地统计任务：
   - `cmdb.counter_main`（每分钟）
   - `cmdb.counter_adc`（每 5 分钟）
   - `cmdb.counter_daily`（每天零点）
   - 都是纯 DB 聚合，不向外部发请求。
4. **数据方向是 Agent 主动来找 CMDB**：`GET /api/v0.1/adt/sync`（`api/views/cmdb/auto_discovery.py:312`）由 OneAgent 携带 `oneagent_id` / `oneagent_name` / `last_update_at` 调用，CMDB 只是“被动地”把属于该 agent 的规则返回。规则同步历史由 `write_ad_rule_sync_history` 任务在 CMDB 侧记录谁同步了什么。

> 结论：CMDB 是纯被动的服务端，从不主动去连 OneAgent 或 OneMaster。

---

## 2. 反向：OneAgent / OneMaster 主动“拉” CMDB 的规则

Agent 通过 `GET /api/v0.1/adt/sync` 拉取自己负责的采集规则（`auto_discovery_rule_sync_view_get`）：

```
GET /api/v0.1/adt/sync?oneagent_id=<hex>&oneagent_name=<name>&last_update_at=<ts>
```

处理逻辑：
1. 仅 `PRIVILEGED_USERS = ("cmdb_agent", "worker", "admin")` 可调用（`const.py:5`）。
2. 若 CI 存在 `oneagent_id` 属性，则用查询 `oneagent_id:<id>` 在 CMDB 里找到“Agent 自己的 CI”（agent 作为 CI 注册在 CMDB 中），据此把规则与 agent 关联（`auto_discovery.py` 的 `AutoDiscoveryCITypeCRUD.get`）。
3. 返回 `{"rules": [...], "subnet_scan_rules": [...], "last_update_at": "..."}`（增量同步：仅当 `new_last_update_at > last_update_at` 时返回规则，否则返回空）。

规则归属判断（`AutoDiscoveryCITypeCRUD.get`，`auto_discovery.py:249-325`）：
- 规则显式绑定 `agent_id == oneagent_id` → 该 agent 拿；
- 规则带 `query_expr` → 用查询表达式在 CMDB 搜索，命中的 CI 关联到该 agent；
- 未绑定 agent 也无 query_expr 的 **AGENT 类型** 规则 → 分发给**除 master 外**的所有 OneAgent（`if not int(oneagent_id, 16): continue  # excludes master`）；
- 返回前会 `decrypt_account` 解密账号（仅对 `PRIVILEGED_USERS` 或规则 owner，`auto_discovery.py:911`），并把凭证随规则下发。

---

## 3. OneAgent 直接推送给 CMDB，不经过 OneMaster

CMDB 侧证据：

- 实例上报端点 `POST /api/v0.1/adc`（`auto_discovery.py` 视图 `auto_discovery_ci_view_post`）直接由任何 agent 调用，要求 `type_id` / `adt_id` / `instance` / `unique_value`，入库到 `c_ad_ci`（`AutoDiscoveryCI`）。
- 执行日志上报端点 `POST /api/v0.1/adc/exec/histories`。
- 全仓库没有任何“OneAgent 数据先到 OneMaster 再转发”的代码路径；CMDB 只见过 `oneagent_id`，从不引用 Master 作为中转。

> 结论：OneAgent → **CMDB**（直连），不经 OneMaster。

---

## 4. OneMaster 也向 CMDB 推送

- 模型里 agent 身份只有 `oneagent_id`（`AutoDiscoveryRuleSyncHistory.oneagent_id`，`IPAMSubnetScan.agent_id`）。
- Master 的唯一特殊点在 `auto_discovery.py:296`：agent_id 为 `0x0...`（`int(x,16)==0`）的 agent 被认定为 master，并被排除在“通用 AGENT 规则”之外（避免 master 重复执行本机组件类规则）。
- 子网扫描（IPAM）是 OneMaster 的典型职责：`SubnetManager.scan_rules(oneagent_id, ...)`（`api/lib/cmdb/ipam/subnet.py:33`）按 `agent_id` 返回其负责扫描的子网（含 CIDR、cron）。

> 结论：OneMaster 会把数据推给 CMDB，接口与 OneAgent 完全相同。

---

## 5. OneMaster 如何向 CMDB 推送

以子网/IPAM 流程为例，完整时序：

1. **拉取任务**：OneMaster 调 `GET /api/v0.1/adt/sync`，CMDB 除常规规则外还会经 `SubnetManager.scan_rules(oneagent_id, last_update_at)` 返回 `subnet_scan_rules`（来自 `c_ipam_subnet_scans` 中 `agent_id` 匹配的记录，含 `cidr`、`cron`）。
2. **执行扫描**：Master 按 cron 扫描子网，产生活跃 IP 列表。
3. **上报扫描结果**：`POST /api/v0.1/ipam/history/scan`，body 含 `exec_id`、`ci_id`（子网 CI）、`cidr`、`start_at`、`end_at`、`status`、`ips`、`subnet_scan_id` 等。处理逻辑 `ScanHistoryManager.add`（`api/lib/cmdb/ipam/history.py:33`）：
   - 写入 `c_ipam_subnet_scan_histories`（按 `exec_id` 幂等）；
   - 对 `ips` 逐个调用 `IpAddressManager.assign_ips(...)` 分配为已用 IP；
   - 更新对应子网扫描规则的 `last_scan_time`；
   - 只保留每个子网最近 100 条历史。
4. **上报发现实例**：与普通 OneAgent 相同，`POST /api/v0.1/adc` 写入 `c_ad_ci`。

**认证方式**：所有 `/api/v0.1/*` 接口挂在 `Depends(authenticate)` 下（`auto_discovery.py` 视图 `router = APIRouter(dependencies=[Depends(authenticate)])`）。Agent 使用 **API Key 认证**（`_auth_with_key`，`api/lib/perm/auth.py:43`）：请求带 `_key` + `_secret`（对 path+排序参数做 SHA1 签名，见 `http_cli.py:build_api_key` 同款算法），视图在处理前会 `request.values.pop("_key"/"_secret")`（`auto_discovery.py` 视图 `auto_discovery_ci_view_post`）。Agent 身份是 `cmdb_agent` 用户，由 `cli.py cmdb_agent-init`（`api/commands/click_cmdb.py:494`）创建/授权：对**所有 CI 类型**授予 READ/UPDATE/ADD/DELETE，并打印出 Key/Secret。

---

## 6. 自动发现工作原理（CMDB 侧）

### 6.1 角色与数据模型

| 角色 | 说明 | CMDB 中的体现 |
| --- | --- | --- |
| CMDB | 规则中心 + 数据落地 | `c_ad_rules`(规则)、`c_ad_ci_types`(规则-CI 类型绑定)、`c_ad_ci`(发现暂存)、`c_ad_rule_sync_histories`(同步记录) |
| OneAgent | 每台目标机/区域上运行的采集执行者 | 身份 = `oneagent_id` + `oneagent_name` |
| OneMaster | agent_id 为 0 的特殊 Agent，负责子网扫描等 | `c_ipam_subnet_scans.agent_id`，`# excludes master` |

规则类型（`AutoDiscoveryType`，`api/lib/cmdb/const.py:98`）：
- `agent` — 本机采集（组件类，如 Nginx/Tomcat/MySQL/Redis 等，见 `const.py` 的 `DEFAULT_INNER`）；
- `http` — 云平台 API（阿里云/腾讯云/华为云/AWS/VCenter/KVM，`CLOUD_MAP` 定义了每家的资源模板与 `collect_key`）；
- `snmp` — 网络设备（交换机/路由器/防火墙/F5 等）；
- `components` — 应用组件。

### 6.2 同步阶段（Agent 拉规则）

`GET /adt/sync` → `AutoDiscoveryCITypeCRUD.get()`：
- 按 `agent_id` / `query_expr` / 通用 AGENT 规则匹配该 agent 的规则；
- 附上解密后的账号凭证（HTTP/SNMP 需要）；
- 写 `c_ad_rule_sync_histories`（`write_ad_rule_sync_history` 异步任务）；
- 返回 `last_update_at` 供增量同步。当规则的 `agent_id`/`query_expr` 变更时，`AutoDiscoveryCITypeCRUD.update` 会更新 `SystemConfigManager("ad_rules_updated_at")` 并清空旧同步记录，强制 agent 全量重拉。

### 6.3 采集阶段（Agent 侧，CMDB 不感知）

Agent 在目标上执行：
- HTTP 规则 → 调云厂商 API 拉资源（ECS、RDS、VPC…），结果字段按 `collect_key`（如 `ali.ecs`）组织；
- SNMP 规则 → 扫网络设备端口/表项；
- AGENT/COMPONENTS → 采集本机组件实例。

### 6.4 上报阶段（Agent → CMDB）

`POST /adc` → `AutoDiscoveryCICRUD.upsert`（`auto_discovery.py:627`）：
- 以 `(type_id, unique_value)` 为唯一键：存在则合并 `instance`（`update` 并写 “update resource” 历史），不存在则新建（写 “add resource” 历史）；
- `instance` 以 `ad_key → 值` 的形式存储，`ad_key` 由 `adt.attributes` 映射到 CMDB 属性名；
- 若该绑定 `auto_accept=True` → 直接调 `accept()` 生成正式 CI；否则置 `is_accept=False`，进入 UI 人工确认。
- 上报会写入 `c_ad_exec_histories`（`POST /adc/exec/histories`），并在 counter 中统计 `exec_target_count`（按去重的 `oneagent_id` 计数，`api/lib/cmdb/cache.py:515`）。

### 6.5 接受阶段（入库生成 CI）

UI 点“接受” → `PUT /adc/{id}/accept` → `AutoDiscoveryCICRUD.accept`（`auto_discovery.py:711`）：
1. 用 `adt.attributes` 把 `ad_key` 翻译成 CMDB 属性名，拼出 `ci_dict`；
2. 若为云资源，套用预定义值映射/路径映射（`AutoDiscoveryHTTPManager.get_predefined_value_mapping`）；
3. `CIManager.add(type_id, is_auto_discovery=True, ...)` 生成正式 CI（带 `is_auto_discovery` 标记）；
4. 异步任务 `build_relations_for_ad_accept`：按 `c_ad_ci_type_relations` 的 `ad_key → (peer_type_id, peer_attr_id)` 找到对端 CI 并建关联（来源 `RelationSourceEnum.AUTO_DISCOVERY`）；
5. 若是网络设备且有 `ports` → 异步 `add_net_device_ports` 建端口；
6. 更新 `is_accept=True`、`accept_by`、`accept_time`、`ci_id`。

### 6.6 全景时序

```
┌─────────┐   ① GET /api/v0.1/adt/sync (oneagent_id, oneagent_name, last_update_at)
│ OneAgent ├───────────────────────────────────────────────────────────►┐
│ (含Master)│   ② 返回 rules + subnet_scan_rules + last_update_at          │
│          │◄────────────────────────────────────────────────────────────┤
│          │                                                             │  CMDB
│          │   ③ POST /api/v0.1/adc  (type_id, adt_id, instance, unique) │  (FastAPI,被动)
│          ├───────────────────────────────────────────────────────────►│  ├─ c_ad_rules / c_ad_ci_types
│          │   ④ POST /api/v0.1/adc/exec/histories (type_id, stdout)     │  ├─ c_ad_ci  (暂存, is_accept=False)
│          ├───────────────────────────────────────────────────────────►│  ├─ c_ipam_subnet_scans
│          │   ⑤ POST /api/v0.1/ipam/history/scan (Master: exec_id,ips)  │  └─ c_ipam_subnet_scan_histories
│          └───────────────────────────────────────────────────────────►│
│                                                                       │  ⑥ 人工/auto_accept
└────────────────────────────────────────────────────────────────────────►  CIManager.add → 正式 CI + 关系
```

---

## 关键代码索引

| 代码位置 | 说明 |
| --- | --- |
| `api/views/cmdb/auto_discovery.py:312` | `GET /adt/sync` — Agent 拉规则入口 |
| `api/views/cmdb/auto_discovery.py:262` | `POST /adc` — Agent 上报实例入口 |
| `api/views/cmdb/auto_discovery.py:399` | `POST /adc/exec/histories` — 上报执行日志 |
| `api/views/cmdb/ipam/ipam_history.py:50` | `POST /ipam/history/scan` — 上报子网扫描结果 |
| `api/lib/cmdb/auto_discovery/auto_discovery.py:249` | `AutoDiscoveryCITypeCRUD.get` — 规则匹配给哪个 agent |
| `api/lib/cmdb/auto_discovery/auto_discovery.py:296` | `# excludes master` — master 判定 |
| `api/lib/cmdb/auto_discovery/auto_discovery.py:627` | `AutoDiscoveryCICRUD.upsert` — 实例 upsert |
| `api/lib/cmdb/auto_discovery/auto_discovery.py:711` | `AutoDiscoveryCICRUD.accept` — 生成正式 CI |
| `api/lib/cmdb/ipam/subnet.py:33` | `SubnetManager.scan_rules` — 子网扫描规则下发 |
| `api/lib/cmdb/ipam/history.py:33` | `ScanHistoryManager.add` — 扫描结果入库+分配 IP |
| `api/lib/perm/auth.py:43` | `_auth_with_key` — Agent API Key 认证 |
| `api/commands/click_cmdb.py:494` | `cli.py cmdb_agent-init` — Agent 账号授权 |
| `api/lib/http_cli.py` | 出站 HTTP 助手（**无调用者**，佐证 CMDB 不主动拉取） |
