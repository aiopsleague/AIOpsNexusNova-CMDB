# 自动发现（Auto Discovery）

> 自动发现是 CMDB 中用于自动采集和纳管 IT 基础设施资源的子系统。通过 OneAgent 从云平台、网络设备、中间件、虚拟机等数据源自动拉取资源信息，经确认后纳入 CMDB 管理。

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      CMDB 管理后台                           │
│  ┌──────────────┐  ┌──────────────────┐                     │
│  │ 规则管理页面  │  │ CI类型配置(AD Tab)│                    │
│  │ /cmdb/discovery│  │ attrADTabpane   │                    │
│  └──────┬───────┘  └────────┬─────────┘                    │
│         │                   │                               │
│  ┌──────┴───────────────────┴──────────┐                    │
│  │         AutoDiscoveryRule (ADR)      │ ← 规则定义        │
│  │    AutoDiscoveryCIType (ADT)          │ ← 规则→CI类型绑定 │
│  │    AutoDiscoveryCI (ADC)              │ ← 发现的实例      │
│  └──────────────────────────────────────┘                    │
│                                                              │
│  ┌──────────────────────────────────────┐                    │
│  │         /api/v0.1/adt/sync           │ ← Agent 拉取规则   │
│  └──────────────────────────────────────┘                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP API
┌──────────────────────────┴──────────────────────────────────┐
│                       OneAgent                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │云平台采集│  │SNMP 采集 │  │组件发现  │  │自定义插件│   │
│  │(阿里云等)│  │(交换机等)│  │(MySQL等) │  │(Python)  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │            │             │            │
│       └─────────────┴────────────┴─────────────┘            │
│                         │                                    │
│              调用 /api/v0.1/adc 上报实例数据                  │
└─────────────────────────┴───────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────┐
│                         CMDB                                 │
│  发现实例(ADC) ──接纳──▶ 正式 CI + CI关系                    │
└─────────────────────────────────────────────────────────────┘
```

---

## OneMaster 与 OneAgent

自动发现系统有两种执行角色，通过 `oneagent_id` 区分：

### OneAgent

安装在**被管理服务器**上的采集代理，`oneagent_id` 是以 `0x` 开头的 16 进制标识（如 `0xABCD1234`）。

**负责执行**：Agent 类型的发现规则（采集本机信息）、被指定执行的 Plugin 规则。

### OneMaster

集中式采集控制节点，`oneagent_id` 固定为 **`0x0000`**。

**负责执行**：不需要分散到每台机器的集中式采集任务——HTTP 云平台 API 调用、SNMP 网络设备扫描、Component 端口扫描与组件识别。

### 规则分配逻辑

Agent 同步规则时（`AutoDiscoveryCITypeCRUD.get()`），CMDB 按以下优先级匹配规则：

1. `agent_id == oneagent_id` → 精确匹配，分配给指定 Agent
2. `query_expr` 匹配 → 通过 CMDB 查询表达式动态匹配 CI，分配给对应 Agent
3. `agent_id` 和 `query_expr` 均为空 → "所有机器"规则
   - **Master（`0x0000`）被排除**（`int('0x0000', 16) == 0`）
   - **SNMP 和 HTTP 类型被排除**（这些是 Master 专属）

| | OneMaster | OneAgent |
|------|------|------|
| **agent_id** | `0x0000` | `0x` + 16 进制（如 `0xABCD1234`） |
| **安装位置** | 单独部署的中心节点 | 每台被管服务器 |
| **数量** | 1 个（或少量） | 与服务器数量对应 |
| **执行任务** | HTTP 云平台、SNMP 扫描、组件发现、Plugin | Agent 采集、Plugin |
| **接收"所有机器"规则** | ❌ 被排除 | ✅ |

---

## 核心概念

自动发现系统有三层核心模型：

### ADR — `AutoDiscoveryRule`（自动发现规则）

定义"用什么方式去发现什么"的**规则模板**。一条规则描述了一种数据源的采集方式。

- 数据库表：`c_ad_rules`
- 系统内置 20+ 条规则（阿里云、腾讯云、华为云、AWS、VCenter、KVM、Nginx、MySQL、交换机、路由器等）
- 支持自定义 Plugin 规则（编写 Python 采集脚本）

### ADT — `AutoDiscoveryCIType`（CI 类型映射）

将规则绑定到具体的 CMDB CI 类型，是**规则与 CI 类型之间的桥梁**。

- 数据库表：`c_ad_ci_types`
- 核心配置：属性映射、执行目标、调度周期、自动接纳、云平台凭证

### ADC — `AutoDiscoveryCI`（发现实例）

Agent 执行采集后上报的**原始资源数据**，等待管理员确认接纳。

- 数据库表：`c_ad_ci`
- 接纳后自动创建正式 CI 并建立 CI 关系

---

## 发现类型

系统支持 6 种发现类型，通过 `AutoDiscoveryRule.type` 字段区分：

### 1. HTTP（云平台）

通过云厂商 API 采集云资源。支持的平台及资源：

```
阿里云 (aliyun)
├── 计算
│   ├── 云服务器 ECS
│   └── 云服务器 Disk
├── 网络与CDN
│   ├── 内容分发CDN
│   ├── 负载均衡SLB
│   ├── 专有网络VPC
│   └── 交换机Switch
├── 存储
│   ├── 块存储EBS
│   └── 对象存储OSS
└── 数据库
    ├── 云数据库RDS MySQL
    ├── 云数据库RDS PostgreSQL
    └── 云数据库 Redis

腾讯云 (tencentcloud) / 华为云 (huaweicloud) / AWS (aws)
（资源分类类似，涵盖计算、网络、存储、数据库等品类）
```

### 2. HTTP（私有云）

```
VCenter  ─── 计算（主机、虚拟机、主机集群）
        ─── 网络（网络、标准交换机、分布式交换机）
        ─── 存储（数据存储、数据存储集群）
        ─── 其他（资源池、数据中心、文件夹）

KVM     ─── 计算（虚拟机）
        ─── 存储（存储）
        ─── 网络（网络）
```

### 3. Agent

部署了 OneAgent 的服务器，通过 Agent 上报本机信息。

### 4. SNMP（网络设备）

通过 SNMP 协议发现网络设备，内置支持：

- 交换机
- 路由器
- 防火墙
- 光纤交换机
- F5

属性模板定义在 `api/lib/cmdb/auto_discovery/templates/net_device.json`，包含 manufacturer、sn、name、model、manager_ip、ips、ports 等字段。

### 5. Components（组件）

发现服务器上运行的中间件/数据库组件：

- Nginx、Apache、Tomcat
- MySQL、MSSQL、Oracle
- Redis

通过端口扫描等方式发现，配置包含 CIDR 范围和端口列表。

### 6. Plugin（自定义插件）

用户编写 Python 脚本自定义采集逻辑，适用于系统内置规则无法覆盖的场景。

**脚本要求**（CMDB 后端通过 `safe_script.py` 校验）：

- 脚本中需定义 `AutoDiscovery` 类
- 实现 `unique_key` 属性（唯一标识字段名）
- 实现 `attributes()` 静态方法（返回属性定义列表 `[[name, type, desc], ...]`）
- 脚本通过 AST 级别沙箱检查：禁止 `import`/`from import`、禁止 `eval`/`exec`/`open` 等危险函数

**Plugin 脚本模板：**

```python
# -*- coding:utf-8 -*-
import json

class AutoDiscovery(object):

    @property
    def unique_key(self):
        """返回唯一标识字段名"""
        return "instance_id"

    @staticmethod
    def attributes():
        """
        定义采集的属性字段
        :return: [(name, type, description), ...]
          type: String Integer Float Date DateTime Time JSON Bool Reference
        """
        return [
            ("instance_id", "String", "实例ID"),
            ("name", "String", "名称"),
            ("status", "String", "运行状态"),
        ]
```

### 内置规则 vs Plugin

| | 内置 MySQL（Components） | Plugin |
|------|------|------|
| **type** | `components` | 用户定义 |
| **采集引擎** | OneAgent 内置的 Native 模块（`collect_key: "mysql"`） | 用户编写的 Python 脚本，存储在 DB 的 `plugin_script` 字段 |
| **CMDB 配置** | 只需配置 CIDR 扫描范围 + 端口 | 需编写完整采集脚本 + 定义属性列表 |
| **安全校验** | 不涉及（OneAgent 内部逻辑） | AST 沙箱检查（`safe_script.py`） |
| **执行位置** | Master 机器 | Master 或 Agent（可配置） |
| **扩展性** | 受限于 OneAgent 内置能力 | 完全由用户定义 |

---

## 数据模型

### c_ad_rules（自动发现规则）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `name` | varchar(32) | 规则名称（如"阿里云"、"交换机"） |
| `type` | enum | 发现类型：agent / snmp / http / components |
| `is_inner` | bool | 是否系统内置规则 |
| `owner` | int | 创建者 UID |
| `option` | json | UI 展示配置（图标等） |
| `attributes` | json | 自定义属性定义（仅 Agent/Plugin） |
| `is_plugin` | bool | 是否为自定义插件 |
| `plugin_script` | text | Python 采集脚本（仅 Plugin） |
| `unique_key` | varchar(64) | 唯一标识字段名（仅 Plugin） |

### c_ad_ci_types（CI 类型映射）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `type_id` | int | 目标 CI 类型 ID → `c_ci_types.id` |
| `adr_id` | int | 所属规则 ID → `c_ad_rules.id` |
| `attributes` | json | 属性映射：`{"ad_key": "cmdb_key"}` |
| `auto_accept` | bool | 是否自动接纳（跳过人工确认） |
| `agent_id` | varchar(8) | 指定执行的 OneAgent ID |
| `query_expr` | text | 目标主机 CMDB 查询表达式 |
| `cron` | varchar(128) | Cron 定时表达式 |
| `extra_option` | json | 扩展配置（云平台凭证、region、扫描参数等） |
| `uid` | int | 配置者 UID |
| `enabled` | bool | 是否启用 |

**`agent_id` 与 `query_expr` 的执行目标逻辑：**

| agent_id 值 | query_expr | 含义 |
|-------------|-----------|------|
| `0x0000` | 空 | Master 机器执行 |
| 空 | 空 | 所有安装了 OneAgent 的机器执行 |
| `0xABCD...` | 空 | 指定 ID 的 OneAgent 执行 |
| 空 | `q=...` | 匹配查询表达式的 CI 上的 Agent 执行 |

### c_ad_ci（发现实例）

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | int | 主键 |
| `type_id` | int | CI 类型 ID |
| `adt_id` | int | 对应的 ADT ID |
| `unique_value` | varchar(128) | 唯一标识值（用于去重 upsert） |
| `instance` | json | 采集到的原始实例数据 |
| `ci_id` | int | 接纳后生成的正式 CI ID |
| `is_accept` | bool | 是否已接纳 |
| `accept_by` | varchar(64) | 接纳人 |
| `accept_time` | datetime | 接纳时间 |

### c_ad_ci_type_relations（CI 类型关系映射）

| 字段 | 类型 | 说明 |
|------|------|------|
| `ad_type_id` | int | CI 类型 ID |
| `ad_key` | varchar(128) | 发现字段名 |
| `peer_type_id` | int | 关联的目标 CI 类型 ID |
| `peer_attr_id` | int | 关联的目标属性 ID |

### c_ad_accounts（账号配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| `uid` | int | 所属用户 |
| `name` | varchar(64) | 账号名称 |
| `adr_id` | int | 所属规则 ID |
| `config` | json | 账号配置（密码/Secret 经 AES 加密存储） |

### 辅助表

- `c_ad_exec_histories` — 执行历史日志（type_id, stdout, created_at）
- `c_ad_rule_sync_histories` — Agent 同步规则历史（adt_id, oneagent_id, sync_at）
- `c_ad_counter` — 按 CI 类型统计（rule_count, instance_count, accept_count, 本周/月增量）

---

## API 接口

所有接口挂载在 `/api/v0.1` 下，均需认证。

### 规则管理（ADR）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/adr` | 获取所有规则列表（自动补全缺失的内置规则） |
| `GET` | `/adr/{id}` | 获取单条规则 |
| `POST` | `/adr` | 创建规则（需 name） |
| `PUT` | `/adr/{id}` | 更新规则 |
| `DELETE` | `/adr/{id}` | 删除规则（被 ADT 引用时不可删） |
| `GET/POST` | `/adr/template/import/file` | 导入规则模板 |
| `GET/POST` | `/adr/template/export/file` | 导出规则模板（`cmdb_auto_discovery.json`） |

### 规则内省

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/adr/http/{name}/categories` | 获取云平台的资源分类 |
| `GET` | `/adr/http/{name}/attributes?resource=` | 获取某云资源的属性模板 |
| `GET` | `/adr/http/{name}/mapping?resource=` | 获取某云资源的属性映射 |
| `GET` | `/adr/snmp/{name}/attributes` | 获取 SNMP 设备属性模板 |
| `GET` | `/adr/components/{name}/attributes` | 获取组件属性模板 |

### CI 类型映射（ADT）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/adt/ci_types/{type_id}` | 获取 CI 类型的所有 ADT |
| `GET` | `/adt/ci_types/{type_id}/attributes` | 获取该 CI 类型可用的所有发现字段 |
| `GET` | `/adt/{adt_id}` | 获取单个 ADT 详情 |
| `POST` | `/adt/ci_types/{type_id}` | 创建 ADT 映射（属性映射 + 执行配置 + 凭证） |
| `PUT` | `/adt/{adt_id}` | 更新 ADT |
| `DELETE` | `/adt/{adt_id}` | 删除 ADT（有关联 ADC 时不可删） |
| `GET/POST/PUT/DELETE` | `/adt/ci_types/{type_id}/relations` | ADT 关系映射 CRUD |
| `GET` | `/adt/sync?oneagent_id=&oneagent_name=&last_update_at=` | **Agent 同步接口**（仅特权用户） |
| `GET` | `/adt/{adt_id}/sync/histories` | 同步历史 |
| `GET/POST` | `/adt/{adt_id}/test` | 执行测试（当前为 stub） |

### 发现实例（ADC）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/adc?type_id=&page=&page_size=` | 分页查询发现实例 |
| `GET` | `/adc/ci_types?need_other=` | 获取有 AD 配置的 CI 类型分组 |
| `GET` | `/adc/ci_types/{type_id}/attributes` | 获取可展示的属性字段 |
| `GET` | `/adc/{id}` | 获取单条实例原始数据 |
| `POST/PUT` | `/adc` | 写入/更新发现实例（Agent 上报用） |
| `DELETE` | `/adc/{id}` | 删除实例 |
| `DELETE` | `/adc?type_id=&unique_value=` | 按类型+唯一值删除 |
| `PUT` | `/adc/{id}/accept` | **接纳**实例为正式 CI |
| `GET` | `/adc/exec/histories?type_id=` | 执行历史日志 |
| `GET` | `/adc/counter?type_id=` | 统计计数 |

### 账号配置

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/adr/accounts?adr_id=` | 获取规则下的账号配置 |
| `POST` | `/adr/accounts` | 批量创建/更新账号配置 |
| `PUT` | `/adr/accounts/{id}` | 更新单个账号 |
| `DELETE` | `/adr/accounts/{id}` | 删除账号 |

---

## 完整工作流

### 步骤一：规则初始化

系统启动时，首次访问 `GET /adr` 会自动检查并补全内置规则（`DEFAULT_INNER`）。内置规则涵盖 4 大公有云、2 个私有云平台、7 种中间件组件、5 类网络设备。

### 步骤二：配置 CI 类型映射

管理员在 CI 类型详情页的"自动发现"Tab 中完成配置：

1. **选择规则**：从规则列表中选择一个规则（如"阿里云"）绑定到当前 CI 类型
2. **属性映射**：将规则提供的发现字段（左侧）映射到 CMDB 属性（右侧），确保唯一键已被映射
3. **执行配置**：
   - **执行机器**：选择 Master / 指定机器 / 从 CMDB 选择 / 所有机器
   - **自动入库**：开启后采集到的实例直接成为正式 CI
   - **采集频率**：配置 Cron 表达式
4. **凭证配置**（HTTP 类型）：填写云平台 AccessKey/SecretKey，或 vCenter 主机/账号/密码

### 步骤三：Agent 同步规则

OneAgent 定期调用 `GET /api/v0.1/adt/sync` 拉取属于自己的规则：

- 传入 `oneagent_id`、`oneagent_name`、`last_update_at`
- 服务端根据 `agent_id` 或 `query_expr` 匹配属于该 Agent 的规则
- 返回规则列表 + 增量更新时间戳
- 对于 HTTP 规则，会解密并下发云平台凭证
- 同步完成后写入 `c_ad_rule_sync_histories` 记录

### 步骤四：Agent 执行采集

OneAgent 根据拿到的规则按 Cron 调度执行采集：

- **HTTP 规则**：调用云厂商 API（如阿里云 ECS DescribeInstances）
- **SNMP 规则**：通过 SNMP 协议扫描网络设备
- **Component 规则**：端口扫描 + 组件识别
- **Plugin 规则**：执行用户自定义 Python 脚本

采集结果调用 `POST /api/v0.1/adc` 上报，通过 `(type_id, unique_value)` 进行 upsert。

### 步骤五：接纳为正式 CI

管理员在"发现实例"页面查看采集结果：

- 按 CI 类型分组浏览
- 查看原始 JSON 数据
- 单个接纳或批量接纳

接纳流程（`AutoDiscoveryCICRUD.accept()`）：

1. 根据 ADT 的属性映射将 raw 数据转为 CMDB 属性
2. 应用云平台预定义值映射（如阿里云 region ID → 名称）
3. 调用 `CIManager.add()` 创建正式 CI
4. 异步任务 `build_relations_for_ad_accept` 创建 CI 关系
5. 网络设备额外调用 `add_net_device_ports` 创建端口 CI

---

## 前端页面

### 规则管理页

- 路由：`/cmdb/discovery`
- 组件：`cmdb-ui/src/modules/cmdb/views/discovery/index.vue`
- 功能：
  - 按 HTTP / 私有云 / Agent / 组件 / SNMP / Plugin 分类展示规则卡片
  - 搜索和分类过滤
  - 导入/导出规则模板 JSON 文件
  - 自定义 Plugin 规则新增、编辑、删除
  - 云平台账号配置（AccessKey/SecretKey）

### CI 类型自动发现配置

- 组件：`cmdb-ui/src/modules/cmdb/views/ci_types/attrADTabpane.vue`
- 作为 CI 类型详情页的一个 Tab，包含：
  - **属性映射表**：发现字段 ↔ CMDB 属性的双向映射
  - **执行配置**：执行目标、自动入库开关、Cron 定时
  - **凭证配置**：公有云（Key/Secret）或私有云（Host/Account/Password）
  - **SNMP 配置**：节点设置、SNMP 参数、CIDR 扫描范围
  - **组件端口配置**：CIDR + 端口列表
  - **配置检查**：查看同步历史和测试结果

### 发现实例页

- 路由：`/cmdb/adc`
- 组件：`cmdb-ui/src/modules/cmdb/views/discoveryCI/index.vue`
- 功能：
  - 左侧：CI 类型分组树
  - 右侧：实例数据表格（含接纳状态标记）
  - 统计卡片：规则数、执行机器数、资源数、本周/月增量
  - 操作：接纳、查看原始数据、删除、批量操作
  - 执行日志弹窗

---

## 安全设计

### 凭证加密

云平台 AccessKey/SecretKey 和 vCenter 密码使用 AES 加密存储：

- 写入时：`encrypt_account()` 对 `password` 和 `secret` 字段加密
- 读取时：`decrypt_account()` 仅对 `cmdb_agent`、`worker`、`admin` 及创建者本人解密
- Agent 同步时使用 `cmdb_agent` 账号，可获取明文凭证

### 权限控制

- Plugin 规则的创建/更新/删除需要 ACL 权限（`Auto_Discovery.create_plugin` / `update_plugin` / `delete_plugin`）或 app admin
- Agent 同步接口仅 `cmdb_agent`、`worker`、`admin` 可访问
- 执行目标选择时校验用户是否为目标机器的运维/开发负责人
- 删除发现实例需要 CI 的 DELETE 权限
- 密码/Secret 修改仅创建者本人可操作

---

## 数据库初始化

- 核心表通过 SQLAlchemy `create_all()` 创建
- 内置规则通过 `docs/cmdb.sql` 中的 INSERT 语句种子化
- 版本升级时通过 `click_cmdb.py` 中的数据迁移脚本处理字段变更（如 `relation` JSON → `c_ad_ci_type_relations`，`interval` → `cron`）

---

## OneAgent 实现指南

> 本节面向需要用其他语言（如 Go）重新实现 OneAgent/OneMaster 的开发者，描述 CMDB 已定义好的接口契约及实现建议。

### CMDB ↔ Agent 接口契约

#### 1. 规则同步

Agent 定期调用此接口拉取属于自己的采集规则。

```
GET /api/v0.1/adt/sync?oneagent_id=0xABCD&oneagent_name=my-agent&last_update_at=2026-01-01 00:00:00
```

**认证**：需以 `cmdb_agent` 等特权用户身份调用。

**请求参数：**

| 参数 | 说明 |
|------|------|
| `oneagent_id` | Agent/Master 的 ID（Master 固定为 `0x0000`） |
| `oneagent_name` | Agent 名称 |
| `last_update_at` | 上次同步时间戳，用于增量更新 |

**返回结构：**

```json
{
  "rules": [
    {
      "id": 1,                           // adt_id
      "type_id": 5,                      // CI 类型 ID
      "adr_id": 3,                       // 规则 ID
      "attributes": {                    // 属性映射: ad_key → cmdb_key
        "InstanceId": "instance_id",
        "InstanceName": "name",
        "Status": "status"
      },
      "cron": "0 */2 * * *",            // 调度周期 (标准 5 位 crontab)
      "enabled": true,                   // 是否启用（禁用的规则也会返回，Agent 应跳过）
      "agent_id": "0x0000",
      "query_expr": "",
      "extra_option": {                  // 采集配置 + 已解密的凭证
        "key": "AK-xxx",                 // 云平台 AccessKey（明文）
        "secret": "SK-xxx",              // 云平台 SecretKey（明文）
        "category": "计算",
        "collect_key": "ali.ecs",        // OneAgent 内置采集模块标识
        "provider": "aliyun"             // 云厂商
      },
      "adr": {                           // 嵌套的规则定义
        "id": 3,
        "name": "阿里云",
        "type": "http",                  // agent | snmp | http | components
        "is_plugin": false,
        "plugin_script": null,           // 仅 Plugin 类型有值 (Python 代码)
        "unique_key": "InstanceId",
        "option": {
          "icon": {"name": "caise-aliyun"},
          "en": "aliyun",
          "collect_key": "ali.ecs"
        }
      }
    }
  ],
  "subnet_scan_rules": [                 // IPAM 子网扫描规则
    {
      "ci_id": 100,
      "scan_enabled": true,
      "cron": "0 2 * * *",
      "agent_id": "0xABCD"
    }
  ],
  "last_update_at": "2026-08-06 10:00:00"
}
```

**关键点：**

- `extra_option` 中的 `key`/`secret`/`password` 已经是 CMDB 后端解密后的**明文**，Agent 可直接使用
- `last_update_at` 是增量同步的关键——Agent 需在本地持久化此时间戳，下次请求时传回，CMDB 只返回有变化的规则
- 禁用的规则（`enabled: false`）也会返回且影响 `last_update_at`，Agent 应跳过不执行

#### 2. 数据上报

采集结果通过此接口上报，以 `(type_id, unique_value)` 作为 upsert 键。

```
POST /api/v0.1/adc
Content-Type: application/json

{
  "type_id": 5,
  "adt_id": 1,
  "instance": {
    "InstanceId": "i-bp67acfmxazb4p****",
    "InstanceName": "my-ecs",
    "Status": "Running",
    "Cpu": 8,
    "Memory": 16384
  },
  "unique_value": "i-bp67acfmxazb4p****"
}
```

**注意事项：**

- `instance` 中的字段名必须与 `attributes` 映射中的 `ad_key` 一致
- `unique_value` 必须对应 CI 类型的唯一标识字段值（CMDB 会校验，不符合则返回 400）
- 重复上报会更新已有记录，不会产生重复数据
- 不要携带 `_key` 和 `_secret` 参数（CMDB 会自动过滤）

#### 3. 数据删除

当采集源中资源被删除时，Agent 应同步删除 CMDB 中的发现实例。

```
DELETE /api/v0.1/adc?type_id=5&unique_value=i-bp67acfmxazb4p****
```

---

### Go 实现架构建议

```
OneAgent (Go)
├── SyncManager           ← 定时调用 /adt/sync 拉取规则
│   └── CronScheduler     ← robfig/cron，每条规则独立一个 cron 调度
│
├── Collectors (Go native)
│   ├── HTTPCollector     ← 阿里云/AWS/腾讯云/华为云 SDK 调用
│   ├── SNMPCollector     ← gosnmp 库，递归 walk + 邻居发现
│   ├── ComponentScanner  ← 端口扫描 (nmap/custom) + 组件指纹识别
│   └── AgentCollector    ← 本机信息采集 (cpu/mem/disk/os 等)
│
├── PluginExecutor        ← exec python3 ad_runner.py (子进程)
│   └── ad_runner.py      ← Python 插件运行器 wrapper(随 Agent 分发)
│
├── Reporter              ← 采集结果通过 /adc 上报
└── Persistence           ← 本地持久化 last_update_at + 调度状态
```

---

### 各发现类型的采集方式

#### HTTP 云平台

根据规则的 `extra_option.provider` 和 `collect_key` 确定调用哪个云 SDK 的哪个 API：

| provider | 需引入的 Go SDK |
|----------|---------------|
| `aliyun` | `github.com/aliyun/alibaba-cloud-sdk-go` |
| `tencentcloud` | `github.com/tencentcloud/tencentcloud-sdk-go` |
| `huaweicloud` | `github.com/huaweicloud/huaweicloud-sdk-go-v3` |
| `aws` | `github.com/aws/aws-sdk-go-v2` |

用 `extra_option.key` / `extra_option.secret` 做鉴权，API 返回的字段名要与 `attributes` 映射中的 `ad_key` 完全匹配。

#### SNMP 网络设备

`extra_option` 中包含完整 SNMP 配置：

```json
{
  "version": "2c",           // SNMP 版本: 1 / 2c / 3
  "community": "public",     // Community 字符串
  "timeout": 5,              // 超时 (秒)
  "retries": 3,              // 重试次数
  "recursive_scan": true,    // 是否递归扫描
  "max_depth": 5,            // 递归最大深度
  "nodes": [                 // 起始节点列表
    {"ip": "192.168.1.1", "community": "public", "version": "2c"}
  ],
  "cidr": ["10.0.0.0/24"]    // CIDR 白名单
}
```

Go 端使用 `gosnmp` 实现：从 `nodes` 出发执行 SNMP Walk → 通过 LLDP/CDP 邻居表发现下一跳 → 递归扫描 → 在 `cidr` 范围内过滤。

#### Components 组件

```json
{
  "collect_key": "mysql",          // 组件类型标识
  "cidr": "10.0.0.0/24",          // 扫描 CIDR 范围
  "ports": "3306",                 // 目标端口
  "enable_cidr": ""                // 额外 CIDR 过滤
}
```

Go 端需要实现端口扫描 + 组件指纹识别（如连接 3306 端口后执行探测命令确认是否为 MySQL）。

#### Plugin

详见下方「Python Plugin 执行方案」。

---

### Python Plugin 执行方案

Plugin 规则中 `adr.plugin_script` 字段存储的是用户编写的 Python 代码。要在 Go Agent 中执行 Python 脚本，有 3 种可行方案。

#### 推荐方案：子进程调用（subprocess + wrapper）

Go Agent 将 `plugin_script` 写入临时文件，通过 `os/exec` 调用一个随 Agent 分发的 `ad_runner.py` wrapper，由其加载并执行用户脚本。

```
Go Agent
  1. 从规则中提取 plugin_script
  2. 写入临时文件 (如 /tmp/ad_plugin_{uuid}.py)
  3. exec: python3 ad_runner.py --plugin /tmp/xxx.py --action collect --config '{}'
  4. 解析 stdout JSON 获取结果
  5. 调用 /api/v0.1/adc 上报
  6. 清理临时文件
```

**ad_runner.py（随 Agent 分发）：**

```python
"""OneAgent Plugin Runner — 由 Go Agent 通过 subprocess 调用"""
import json
import sys
import argparse
from importlib.util import spec_from_file_location, module_from_spec


def load_plugin(path):
    spec = spec_from_file_location("ad_plugin", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.AutoDiscovery


def cmd_metadata(plugin_cls):
    """获取插件元数据 (兼容 CMDB 后端的校验方式)"""
    inst = plugin_cls()
    attrs = plugin_cls.attributes() or []
    result = {"unique_key": inst.unique_key, "attributes": []}
    for item in attrs:
        if len(item) == 3:
            name, typ, desc = item
        elif len(item) == 2:
            name, typ = item
            desc = ""
        else:
            continue
        result["attributes"].append({"name": name, "type": typ, "desc": desc})
    print(json.dumps(result))


def cmd_collect(plugin_cls, config):
    """执行采集"""
    inst = plugin_cls()
    results = inst.collect(config) if hasattr(inst, 'collect') else []
    print(json.dumps(results))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", required=True, help="插件脚本路径")
    parser.add_argument("--action", choices=["metadata", "collect"],
                        default="collect")
    parser.add_argument("--config", default="{}", help="采集配置 JSON")
    args = parser.parse_args()

    plugin_cls = load_plugin(args.plugin)
    if args.action == "metadata":
        cmd_metadata(plugin_cls)
    else:
        cmd_collect(plugin_cls, json.loads(args.config))
```

**Go 侧调用示例：**

```go
func (e *PluginExecutor) Execute(pluginScript string, config map[string]interface{}) ([]map[string]interface{}, error) {
    // 1. 写入临时脚本文件
    tmpFile, _ := os.CreateTemp("", "ad_plugin_*.py")
    defer os.Remove(tmpFile.Name())
    tmpFile.WriteString(pluginScript)
    tmpFile.Close()

    // 2. 执行 Python wrapper
    configJSON, _ := json.Marshal(config)
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Minute)
    defer cancel()

    cmd := exec.CommandContext(ctx, "python3",
        "ad_runner.py",
        "--plugin", tmpFile.Name(),
        "--action", "collect",
        "--config", string(configJSON),
    )
    var stdout, stderr bytes.Buffer
    cmd.Stdout = &stdout
    cmd.Stderr = &stderr

    if err := cmd.Run(); err != nil {
        return nil, fmt.Errorf("plugin exec failed: %v, stderr: %s", err, stderr.String())
    }

    // 3. 解析结果
    var results []map[string]interface{}
    json.Unmarshal(stdout.Bytes(), &results)
    return results, nil
}
```

**优点**：Python 版本自由、进程隔离（插件崩溃不影响 Agent）、安全边界清晰、与 CMDB 后端校验方式兼容。

#### 备选方案

| 方案 | 实现方式 | 优点 | 缺点 |
|------|---------|------|------|
| **cgo 嵌入 CPython** | 使用 `go-python3` 直接调用 `PyRun_SimpleString` | 无进程启动开销 | 编译复杂、跨平台困难、插件 bug 会影响 Agent 进程、沙箱隔离困难 |
| **Python Sidecar** | Agent 启动时拉起 Python 进程，通过 gRPC/Unix Socket 通信 | Go 和 Python 职责分离清晰 | 架构复杂、部署和维护成本高 |

#### 安全加固建议

无论采用哪种方案，建议增加以下安全措施：

1. **超时控制**：插件执行超过 5 分钟自动 kill
2. **资源限制**：用 cgroup / ulimit 限制子进程内存和 CPU
3. **网络隔离**：插件不应有网络访问（采集由 Agent 主进程完成），可通过 network namespace 隔离
4. **文件系统隔离**：只暴露临时目录给插件进程
5. **信任 CMDB 校验**：CMDB 后端已通过 `safe_script.py` 做了 AST 级别的安全检查，Agent 侧可以信任

---

### 实现注意事项

1. **Cron 调度**：每个规则独立一个 cron，Go 端推荐 `robfig/cron` 库。cron 字段为标准 5 位格式（分 时 日 月 周）。
2. **增量更新**：Agent 需本地持久化 `last_update_at`，每次同步时传回。CMDB 会根据此时间戳只返还有变化的规则。
3. **唯一键校验**：上报前确认 `instance` 中包含 CI 类型唯一键字段。每个 ADT 绑定的 CI Type 有一个 `unique_id` 属性，不匹配则 CMDB 返回 400 错误。
4. **认证**：Agent 调用 CMDB API 需使用 `cmdb_agent` 特权用户身份（`_key/_secret` 或 JWT）。
5. **去重**：上报接口以 `(type_id, unique_value)` 自动 upsert，Agent 不需要自行去重。
6. **清理**：当采集源中资源消失时（如云平台 ECS 被释放），Agent 应主动调用 DELETE 接口清理发现实例。

---

## 文件索引

### 后端

| 文件 | 说明 |
|------|------|
| `cmdb-api/api/lib/cmdb/auto_discovery/auto_discovery.py` | 核心业务逻辑（CRUD、属性映射、接纳流程） |
| `cmdb-api/api/lib/cmdb/auto_discovery/const.py` | 常量定义（内置规则、云平台资源映射表） |
| `cmdb-api/api/lib/cmdb/auto_discovery/templates/` | 资源属性模板 JSON（ECS、CVM、EC2、SNMP） |
| `cmdb-api/api/views/cmdb/auto_discovery.py` | API 路由（451 行） |
| `cmdb-api/api/models/cmdb.py` | 数据模型定义（第 565-665 行） |
| `cmdb-api/api/tasks/cmdb.py` | 异步任务（接纳建关系、网络设备端口） |
| `cmdb-api/api/commands/click_cmdb.py` | 数据迁移脚本 |

### 前端

| 文件 | 说明 |
|------|------|
| `cmdb-ui/src/modules/cmdb/views/discovery/index.vue` | 规则管理页 |
| `cmdb-ui/src/modules/cmdb/views/discovery/editDrawer.vue` | 规则编辑抽屉 |
| `cmdb-ui/src/modules/cmdb/views/discovery/discoveryCard.vue` | 规则卡片 |
| `cmdb-ui/src/modules/cmdb/views/discovery/accountConfig/` | 账号配置弹窗 |
| `cmdb-ui/src/modules/cmdb/views/discoveryCI/index.vue` | 发现实例列表页 |
| `cmdb-ui/src/modules/cmdb/views/ci_types/attrADTabpane.vue` | CI 类型 AD 配置 Tab（核心配置页） |
| `cmdb-ui/src/modules/cmdb/api/discovery.js` | API 客户端 |
| `cmdb-ui/src/modules/cmdb/components/httpSnmpAD/` | HTTP/SNMP 属性映射组件 |
| `cmdb-ui/src/modules/cmdb/components/attrMapTable/` | 属性映射表格组件 |
