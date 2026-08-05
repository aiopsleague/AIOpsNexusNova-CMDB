# 自动发现 FAQ（常见问题）

> 基于自动发现系统的会话讨论整理。建议先阅读 [auto_discovery.md](auto_discovery.md) 了解整体架构。

---

## 目录

1. [自动发现功能概览](#1-自动发现功能概览)
2. [执行配置详解](#2-执行配置详解)
3. [OneMaster 与 OneAgent 的区别](#3-onemaster-与-oneagent-的区别)
4. [Plugin 是什么](#4-plugin-是什么)
5. [内置规则与 Plugin 的区别](#5-内置规则与-plugin-的区别)
6. [OneAgent/OneMaster 是否需要 Python 运行时](#6-oneagentonemaster-是否需要-python-运行时)
7. [用 Go 实现 OneAgent 的注意事项](#7-用-go-实现-oneagent-的注意事项)
8. [采集数据发送给谁](#8-采集数据发送给谁)
9. [网络隔离场景如何处理](#9-网络隔离场景如何处理)

---

## 1. 自动发现功能概览

### 这是什么？

自动发现是 CMDB 中用于**自动采集和纳管 IT 基础设施资源**的子系统。通过 OneAgent 从云平台、网络设备、中间件、虚拟机等数据源自动拉取资源信息，经确认后纳入 CMDB 管理。

### 核心三要素

| 概念 | 数据库表 | 作用 |
|------|---------|------|
| ADR（AutoDiscoveryRule） | `c_ad_rules` | 定义"用什么方式发现什么"的规则模板 |
| ADT（AutoDiscoveryCIType） | `c_ad_ci_types` | 将规则绑定到具体 CI 类型，配置属性映射、执行目标、调度 |
| ADC（AutoDiscoveryCI） | `c_ad_ci` | 采集到的原始实例数据，等待接纳为正式 CI |

### 六种发现类型

| 类型 | 说明 | 典型场景 | 执行者 |
|------|------|---------|--------|
| HTTP（公有云） | 云厂商 API 采集 | 阿里云、腾讯云、华为云、AWS | Master |
| HTTP（私有云） | 私有云 API 采集 | VCenter、KVM | Master |
| Agent | OneAgent 本机采集 | 服务器信息 | Agent |
| SNMP | SNMP 协议扫描 | 交换机、路由器、防火墙、F5 | Master |
| Components | 端口扫描 + 组件识别 | Nginx、MySQL、Redis、Tomcat | Master |
| Plugin | 自定义 Python 脚本 | 自研系统、特殊数据源 | Master / Agent（可配） |

---

## 2. 执行配置详解

在 CI 类型详情页的「自动发现」Tab 中，「执行配置」区域包含三项设置：

### 执行机器

决定**由哪台机器来执行采集任务**。数据存储在 `AutoDiscoveryCIType` 的 `agent_id` 和 `query_expr` 字段。

| 选项 | 存储逻辑 | 含义 |
|------|---------|------|
| **Master 机器** | `agent_id = '0x0000'` | 由安装 OneMaster 的机器执行（HTTP/SNMP/Components 默认选择） |
| **所有机器** | `agent_id = ''` 且 `query_expr = ''` | 所有 OneAgent 都执行（仅 Admin + Agent 类型可用） |
| **指定机器** | `agent_id = '0x...'` | 手动输入 16 进制 OneAgent ID |
| **从 CMDB 中选择** | `query_expr = 'q=...'` | CMDB 查询表达式动态匹配执行机器 |

**底层权限校验**：非 admin 用户选择"指定机器"或"从 CMDB 中选择"时，系统校验用户是否为目标机器的运维/开发负责人。

### 自动入库

对应 `auto_accept` 字段：

- **开启**：采集到的实例直接创建为正式 CI，无需人工确认
- **关闭**（默认）：实例进入"发现实例"列表（`is_accept = false`），需管理员手动接纳

### 采集频率

对应 `cron` 字段，标准 5 位 crontab 格式（分 时 日 月 周）。示例：`0 15 * * 1-5` 表示工作日下午 15:00 执行。

---

## 3. OneMaster 与 OneAgent 的区别

### 角色定义

| | OneMaster | OneAgent |
|------|------|------|
| **agent_id** | `0x0000` | `0x` + 16 进制（如 `0xABCD1234`） |
| **安装位置** | 单独部署的中心节点 | 每台被管服务器 |
| **数量** | 1 个（或少量） | 与服务器数量对应 |
| **执行任务** | HTTP 云平台、SNMP 扫描、组件发现、Plugin | Agent 采集（本机信息）、Plugin |

### 规则分配逻辑

Agent 同步规则时，CMDB 按以下优先级匹配：

1. **精确匹配**：`agent_id == oneagent_id`
2. **查询表达式匹配**：`query_expr` 匹配到的 CI 对应的 Agent
3. **全局规则**：`agent_id` 和 `query_expr` 均为空 → 但 **Master 被排除**（`int('0x0000', 16) == 0`），且 **SNMP 和 HTTP 类型被排除**（这些是 Master 专属）

### 一句话总结

**OneMaster 是"指挥部"**（集中式采集云平台/网络设备/组件），**OneAgent 是"侦察兵"**（分散在各服务器上采集本机信息）。

---

## 4. Plugin 是什么

Plugin 是**用户自定义的 Python 采集脚本**，用于覆盖系统内置规则无法满足的采集场景。

### 脚本要求

必须定义一个 `AutoDiscovery` 类，包含：

```python
class AutoDiscovery(object):

    @property
    def unique_key(self):
        """返回唯一标识字段名（用于去重 upsert）"""
        return "instance_id"

    @staticmethod
    def attributes():
        """定义采集的属性字段
        :return: [(name, type, description), ...]
        """
        return [
            ("instance_id", "String", "实例ID"),
            ("name", "String", "名称"),
            ("status", "String", "运行状态"),
        ]
```

### 沙箱安全检查

脚本在保存时经过 `safe_script.py` 的 AST 级别检查：

- **禁止**：`import` / `from import`、`eval` / `exec` / `open` / `compile`、双下划线方法
- **允许**的 builtins：`str` / `int` / `dict` / `list` / `json` / `len` / `range` / `sorted` 等

### 权限控制

创建/更新/删除 Plugin 需要 ACL 权限（`Auto_Discovery.create_plugin` / `update_plugin` / `delete_plugin`）或 app admin。

### Plugin 可以在哪些机器上执行？

都可以。配置 CI 类型映射时，执行机器的选择项中，**Plugin 始终可以选择 Master 机器**（非 Agent 类型的规则都会有此选项），同时也可选指定 Agent 或通过 CMDB 表达式动态匹配。

---

## 5. 内置规则与 Plugin 的区别

以「内置 MySQL」和「自定义 Plugin」为例：

| | 内置 MySQL（Components） | Plugin |
|------|------|------|
| **type** | `components` | 用户定义 |
| **采集引擎** | OneAgent 内置的 Native 模块 | 用户 Python 脚本，存储在 DB |
| **驱动方式** | `collect_key: "mysql"`（OneAgent 识别此标识并调用内置模块） | `plugin_script` 字段中的 Python 代码 |
| **CMDB 配置** | 只需配 CIDR 范围 + 端口 | 需编写完整采集脚本 + 定义属性列表 |
| **安全校验** | 不涉及（OneAgent 内部逻辑） | AST 沙箱检查 |
| **执行者** | Master | Master 或 Agent（可配） |
| **扩展性** | 受限于 OneAgent 内置能力 | 完全由用户定义 |

**本质区别**：内置 MySQL 是 OneAgent **已经会**的事情，你只需告诉它"去哪些 IP 段扫描"；Plugin 是 OneAgent **不会**的事情，你需要**手把手教它**（写 Python 脚本）。

---

## 6. OneAgent/OneMaster 是否需要 Python 运行时

### 分两种情况

#### 内置规则（云平台 / SNMP / Components）—— 不需要 Python

内置规则通过 `collect_key` 驱动（如 `ali.ecs`、`mysql`），这些 `collect_key` 指向的是 OneAgent 可执行程序内部的 **Native 模块**（通常用 Go/C 编写）。Agent 根据 `collect_key` 调用自己的内置采集模块，不涉及 Python。

#### Plugin 规则 —— 需要 Python

Plugin 规则存储的是完整的 Python 脚本。OneAgent/Master 拿到规则后，需要执行其中的 `AutoDiscovery` 类。因此如果需要支持 Plugin 功能，部署 OneAgent/Master 的机器上**必须有 Python 运行时**。

### 执行责任分工

| 步骤 | 执行方 | 做了什么 |
|------|--------|---------|
| 保存时校验 | **CMDB 后端** | AST 解析 → 沙箱安全检查 → 提取 `unique_key` + `attributes` → 存入数据库 |
| 同步下发 | **CMDB 后端** | `/adt/sync` 接口返回规则（含 `plugin_script` 原文） |
| 实际采集 | **OneAgent/Master** | 用 Python 解释器执行插件脚本，采集数据，上报 `/adc` |

---

## 7. 用 Go 实现 OneAgent 的注意事项

### CMDB ↔ Agent 接口契约

#### 规则同步

```
GET /api/v0.1/adt/sync?oneagent_id=0xABCD&oneagent_name=my-agent&last_update_at=2026-01-01
```

返回 `{rules: [...], subnet_scan_rules: [...], last_update_at: "..."}`。规则中包含已解密的云平台凭证、属性映射、cron 调度、采集配置等。

#### 数据上报

```
POST /api/v0.1/adc
{
  "type_id": 5, "adt_id": 1,
  "instance": {"InstanceId": "xxx", ...},
  "unique_value": "xxx"
}
```

以 `(type_id, unique_value)` 作为 upsert 键。

#### 数据删除

```
DELETE /api/v0.1/adc?type_id=5&unique_value=xxx
```

### Go 实现架构建议

```
OneAgent (Go)
├── SyncManager           ← 定时调用 /adt/sync 拉取规则
│   └── CronScheduler     ← robfig/cron，每条规则独立调度
├── Collectors (Go native)
│   ├── HTTPCollector     ← 各云厂商 Go SDK
│   ├── SNMPCollector     ← gosnmp 库
│   ├── ComponentScanner  ← 端口扫描 + 组件指纹
│   └── AgentCollector    ← 本机信息 (cpu/mem/disk)
├── PluginExecutor        ← exec python3 ad_runner.py
├── Reporter              ← 调用 /adc 上报
└── Persistence           ← 本地持久化 last_update_at
```

### Python Plugin 执行方案

**推荐方案**：Go Agent 将 `plugin_script` 写入临时文件，通过 `os/exec` 调用 Python wrapper（`ad_runner.py`），解析 stdout JSON 获取结果。

关键代码结构（Go 侧）：

```go
cmd := exec.CommandContext(ctx, "python3",
    "ad_runner.py",
    "--plugin", tmpFile,
    "--action", "collect",
    "--config", configJSON,
)
```

关键安全措施：

1. **超时控制**：`context.WithTimeout`，超 5 分钟自动 kill
2. **资源限制**：cgroup / ulimit 限制内存和 CPU
3. **网络隔离**：插件不应有网络访问
4. **信任 CMDB 校验**：CMDB 已通过 `safe_script.py` 做了 AST 安全检查

### 关键注意事项清单

1. **Cron 调度**：标准 5 位格式，推荐 `robfig/cron` 库
2. **增量更新**：本地持久化 `last_update_at`，每次同步时传回
3. **唯一键校验**：上报前确认 `instance` 中包含 CI 类型唯一键字段
4. **认证**：Agent 调用 CMDB API 需使用 `cmdb_agent` 特权用户身份
5. **去重**：上报接口自动 upsert，Agent 不需要自行去重
6. **清理**：采集源中资源消失时，Agent 应主动调用 DELETE 清理

---

## 8. 采集数据发送给谁

无论 OneAgent 还是 OneMaster，采集数据都统一发送给 **CMDB 后端 API**：

```
OneAgent ────┐
             │  POST /api/v0.1/adc
             ├──────────────────────▶  CMDB 后端 (FastAPI :5000)
OneMaster ───┘                       │
                                     ├── 写入 c_ad_ci 表
                                     ├── auto_accept 开启则直接接纳为 CI
                                     └── 写入 c_ad_exec_histories
```

从 CMDB 的视角看，它不关心数据来自谁——只要能通过认证（`cmdb_agent` 等特权用户），按约定格式上报，就可以写入发现实例表。

---

## 9. 网络隔离场景如何处理

### 问题

如果 OneAgent 所在的数据中心网络隔离，无法直接访问 CMDB 后端，如何处理？

### 方案一：OneMaster 中继代理（推荐）

在每个隔离区域部署一个 OneMaster 作为数据中继站：

```
隔离区域 B
┌──────────┐  内网 gRPC   ┌──────────────┐        POST /adc
│ OneAgent │─────────────▶│  OneMaster   │──────────────▶ CMDB
└──────────┘              │  (Region B)  │
┌──────────┐              │  聚合 + 转发  │
│ OneAgent │─────────────▶└──────────────┘
└──────────┘
```

- OneMaster 暴露内网接口供 Agent 上报
- OneMaster 代为执行 `/adt/sync` 并分发给区域内 Agent
- 只需 OneMaster 一台机器开放到 CMDB 的网络出口

### 方案二：消息队列解耦

```
隔离区域                           CMDB 可达区域
┌──────────┐  produce   ┌────┐  consume   ┌──────────────┐
│ OneAgent │──────────▶│ MQ │◀───────────│ CMDB Worker   │
└──────────┘           │    │            └──────────────┘
                       └────┘
```

利用现有 Celery + Redis 基础设施，Agent 投递到 MQ，Worker 消费写入。

### 方案三：CMDB 侧拉取（Pull 模式）

反转方向——CMDB 主动去 Agent 拉取。适合 Agent 完全没有出站权限的场景。Agent 暴露查询接口，CMDB 定时拉取。

### 方案四：HTTP 正向代理

最简单——Agent 通过 HTTP 代理出站。Go 的 `net/http` 天然支持 `HTTP_PROXY`。

### 方案对比

| 方案 | 复杂度 | 适用场景 | 改动范围 |
|------|--------|---------|---------|
| **OneMaster 中继** | 低 | 已有 OneMaster 的区域 | OneMaster 增加中继能力 |
| **消息队列** | 中 | 已有 MQ 基础设施，高吞吐 | Agent + CMDB Worker |
| **CMDB 拉取** | 高 | Agent 完全无出站权限 | Agent + CMDB 双向改造 |
| **HTTP 代理** | 最低 | 有统一代理出口的环境 | 无代码改动 |

**推荐组合**：OneMaster 中继 + HTTP 代理兜底——在每个隔离区域部署 OneMaster，同时支持通过 HTTP 代理出站连接 CMDB。
