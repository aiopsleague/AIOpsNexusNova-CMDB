# OneAgent / OneMaster 开发指南

> 面向 OneAgent（采集代理）与 OneMaster（中心采集节点）开发者的 CMDB 接口契约与实现规范。
> 覆盖：架构与通信模型、规则同步（插件规则读取）、自定义脚本编写规范、数据上报格式、认证签名、unique_value 规则。
> 配套文档：[自动发现总览](auto_discovery.md)、[自动发现 FAQ](auto_discovery_faq.md)。

---

## 目录

1. [架构与通信模型](#1-架构与通信模型)
2. [规则同步：Agent 如何读取插件规则](#2-规则同步agent-如何读取插件规则)
3. [插件自定义脚本编写规范](#3-插件自定义脚本编写规范)
4. [数据上报格式](#4-数据上报格式)
5. [认证与签名](#5-认证与签名)
6. [unique_value 的确定规则](#6-unique_value-的确定规则)
7. [端到端流程示例](#7-端到端流程示例)
8. [实现注意事项](#8-实现注意事项)
9. [接口速查表](#9-接口速查表)

---

## 1. 架构与通信模型

### 1.1 三层架构

```
┌─────────────────────┐        ┌──────────────────────┐        ┌──────────────┐
│  OneAgent           │  agent │  OneMaster           │  HTTP  │  CMDB        │
│  (每台被管服务器)     │  协议   │  (中心采集节点)        │  +认证  │  (FastAPI)   │
│  - 采集本机信息       │────────▶│  - 维护 agent 清单    │────────▶│  - 规则同步   │
│  - 执行分发的 Plugin │        │  - 执行 HTTP/SNMP/    │        │  - 实例接纳   │
│  - 上报采集结果给     │        │    Component 采集     │        │  - CI 生成    │
│    OneMaster        │        │  - 汇总上报 CMDB      │        │              │
└─────────────────────┘        └──────────────────────┘        └──────────────┘
```

**角色职责：**

| | OneAgent | OneMaster |
|------|------|------|
| **安装位置** | 每台被管服务器 | 单独部署的中心节点 |
| **oneagent_id** | `0x` + 16 进制（如 `0xABCD1234`） | 固定 `0x0000` |
| **配置内容** | 仅 OneMaster 的连接地址 | CMDB 地址 + `cmdb_agent` 的 `_key`/`_secret` |
| **是否感知 CMDB** | ❌ 完全不感知 | ✅ 唯一的 CMDB 客户端 |
| **执行任务** | Agent 采集、被指定的 Plugin | HTTP 云平台、SNMP、组件发现、Plugin |

> ⚠️ **关键**：`_key`/`_secret`、CMDB 地址只配置在 OneMaster 上。OneAgent 不持有任何 CMDB 凭证，它只把采集结果交给 OneMaster，由 OneMaster 统一签名上报。

### 1.2 OneMaster 的 agent 清单职责

OneMaster 内部维护每台 OneAgent 的 `oneagent_id` 与名称。**规则同步必须按 agent 逐个调用**，因为 CMDB 的规则匹配依赖 `oneagent_id`：

```text
for agent in agent_list:
    rules = GET /api/v0.1/adt/sync?oneagent_id=<agent.id>&oneagent_name=<agent.name>&last_update_at=<agent.last_update_at>
    将 rules 分发给该 agent
```

上报时 OneMaster 统一调用 `/adc`，payload 中**不携带 agent 身份**——CMDB 仅按 `(type_id, unique_value)` 去重。

---

## 2. 规则同步：Agent 如何读取插件规则

### 2.1 接口

```
GET /api/v0.1/adt/sync?oneagent_id=0xABCD&oneagent_name=my-agent&last_update_at=2026-01-01 00:00:00
```

**认证**：必须以 `cmdb_agent` / `worker` / `admin` 身份调用（见 [第 5 节](#5-认证与签名)），否则 403。

**参数：**

| 参数 | 说明 |
|------|------|
| `oneagent_id` | Agent/Master 的 ID（Master 固定 `0x0000`） |
| `oneagent_name` | Agent 名称 |
| `last_update_at` | 上次同步时间戳，用于增量更新 |

### 2.2 规则分配逻辑

CMDB 按以下优先级匹配属于该 Agent 的规则（`AutoDiscoveryCITypeCRUD.get()`）：

| 优先级 | 规则特征 | 含义 |
|------|---------|------|
| 1 | `agent_id == oneagent_id` | 精确分配给指定 Agent |
| 2 | `query_expr` 非空 | 查询表达式匹配该 Agent 所在 CI → 下发 |
| 3 | `agent_id` 与 `query_expr` 均为空 | "所有机器"规则；排除 Master（`0x0000`）与 SNMP/HTTP 类型 |

### 2.3 同步响应结构

```json
{
  "rules": [
    {
      "id": 1,                          // ← adt_id（上报时回传）
      "type_id": 5,                     // ← 目标 CI 类型 ID（模型）
      "adr_id": 3,
      "attributes": {                   // 采集字段 → CMDB 属性映射
        "InstanceId": "instance_id",
        "InstanceName": "name"
      },
      "cron": "0 */2 * * *",           // 标准 5 位 crontab
      "enabled": true,                  // 禁用规则也返回，Agent 应跳过
      "agent_id": "0x0000",
      "query_expr": "",
      "auto_accept": false,             // 开启后上报即自动接纳
      "extra_option": {                 // 采集配置 + 已解密凭证（仅特权用户可看明文）
        "provider": "aliyun",
        "category": "计算",
        "collect_key": "ali.ecs",       // OneAgent 内置采集模块标识
        "key": "AK-xxx",                // 明文 AccessKey（Agent 直接用）
        "secret": "SK-xxx"              // 明文 SecretKey
      },
      "adr": {                          // 嵌套的规则定义
        "id": 3,
        "name": "阿里云",
        "type": "http",                 // agent | snmp | http | components | plugin
        "is_plugin": false,
        "plugin_script": null,          // ← 插件规则时是完整 Python 脚本
        "unique_key": "InstanceId",     // ← 插件规则的唯一字段名（adr.unique_key）
        "option": { "icon": {...}, "en": "aliyun" }
      }
    }
  ],
  "subnet_scan_rules": [               // IPAM 子网扫描规则（可选）
    { "ci_id": 100, "scan_enabled": true, "cron": "0 2 * * *", "agent_id": "0xABCD" }
  ],
  "last_update_at": "2026-08-06 10:00:00"
}
```

### 2.4 插件规则的关键点

当 `adr.type == "plugin"` 或 `adr.is_plugin == true` 时：

- **`adr.plugin_script`** 包含完整的用户自定义 Python 采集脚本
- **`adr.unique_key`** 是该插件声明的唯一字段名（来自脚本 `AutoDiscovery.unique_key` 属性）
- `adr.attributes` **不会**出现在同步响应中（CMDB 已剔除，它仅用于 UI 展示可用字段）
- Agent 拿到脚本后按 [第 3 节](#3-插件自定义脚本编写规范) 执行，用 `adr.unique_key` 取 unique_value

### 2.5 增量同步

- `last_update_at` 是增量关键：Agent 需**本地持久化**该时间戳，下次请求传回
- 服务端只返还有变化的规则；若无变化返回 `"rules": []`
- **禁用的规则（`enabled: false`）也会返回并影响 `last_update_at`**，Agent 应跳过不执行
- 同步完成后 CMDB 异步记录同步历史（`c_ad_rule_sync_histories`）

---

## 3. 插件自定义脚本编写规范

### 3.1 脚本结构

脚本必须定义 `AutoDiscovery` 类，包含三个成员：

```python
# -*- coding:utf-8 -*-
import json


class AutoDiscovery(object):

    @property
    def unique_key(self):
        """返回唯一标识字段名（CMDB 唯一键据此校验）"""
        return "instance_id"

    @staticmethod
    def attributes():
        """
        定义采集的属性字段
        :return: [(name, type, description), ...]
        """
        return [
            ("instance_id", "String", "实例ID"),
            ("name", "String", "名称"),
            ("status", "String", "运行状态"),
        ]

    @staticmethod
    def run():
        """
        执行入口，返回采集结果
        :return: [dict, ...]，dict 的 key 为属性名，value 为属性值
        """
        return [
            dict(instance_id="vm-001", name="web-1", status="Running"),
        ]


if __name__ == "__main__":
    result = AutoDiscovery().run()
    if isinstance(result, list):
        print("AutoDiscovery::Result::{}".format(json.dumps(result)))
    else:
        print("ERROR: The collection return must be a list")
```

### 3.2 成员要求

| 成员 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `unique_key` | `property` | ✅ | 唯一标识字段名（必须是 `attributes()` 中的某个 name） |
| `attributes()` | `staticmethod` | ✅ | 返回属性定义列表 `[(name, type, desc)]` |
| `run()` | `staticmethod` | ✅ | 返回采集结果列表，每项是 `{属性名: 值}` 字典 |

### 3.3 属性类型枚举

`attributes()` 中 `type` 字段只接受以下值：

```
String  Integer  Float  Date  DateTime  Time  JSON  Bool  Reference
```

### 3.4 输出约定（关键）

脚本被独立执行（`python plugin.py`）时，**stdout 中的标记行**是 Agent 解析结果的唯一通道：

```
AutoDiscovery::Result::{json数组}
```

- 标记格式固定为 `AutoDiscovery::Result::` 前缀 + JSON
- 只有标记行之后的 JSON 是有效采集结果
- `run()` 返回值必须为 list，否则输出 `ERROR: The collection return must be a list`

### 3.5 安全限制（AST 沙箱校验）

CMDB 保存插件脚本时通过 `safe_script.py` 做 AST 级检查，**Agent 侧可信任该校验**，但仍建议执行时做进程隔离。被禁止的内容：

**禁止的语法节点：**
```
Import, ImportFrom, Global, Nonlocal, AsyncFunctionDef, Await,
Yield, YieldFrom, Lambda, With, AsyncWith, Delete
```

**禁止的名字 / 函数：**
```
__import__, eval, exec, open, compile, input,
globals, locals, vars, dir, getattr, setattr, delattr,
help, breakpoint
```

**禁止访问以 `__` 开头的一切（名称、属性、函数调用）。**

**允许的 builtins（白名单）：**
```
__build_class__, object, Exception, str, int, float, bool,
dict, list, set, tuple, len, range, enumerate, zip,
min, max, sum, abs, sorted, all, any
```

### 3.6 编写建议

- `attributes()` 中的 `name` **必须用英文**（映射到 CMDB 属性名时更可靠）
- `unique_key` 指向的字段应能在 `run()` 返回的每项中稳定出现，且值全局唯一
- 脚本禁止 `import`，若确需外部逻辑应改用内置规则（组件/HTTP）或扩展 Agent 原生采集器
- `run()` 返回的字段名必须与 `attributes()` 声明的 name 一致

---

## 4. 数据上报格式

### 4.1 上报接口

```
POST /api/v0.1/adc          # 新增 / 更新（upsert），也可用 PUT
Content-Type: application/json
```

**必填参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| `type_id` | int | 目标 CI 类型 ID（同步下发的） |
| `adt_id` | int | ADT 映射 ID（同步下发的） |
| `instance` | object | 采集原始数据，**字段名 = ad_key**（非 CMDB 属性名） |
| `unique_value` | string | 唯一键字段的值（见 [第 6 节](#6-unique_value-的确定规则)） |

**示例：**

```json
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

### 4.2 upsert 语义（幂等）

- CMDB 以 **`(type_id, unique_value)`** 作为去重键（[`AutoDiscoveryCICRUD.upsert`](../cmdb-api/api/lib/cmdb/auto_discovery/auto_discovery.py)）
- 已存在 → 合并更新该记录；不存在 → 新增
- 重复上报不会产生重复数据，**Agent 无需自行去重**
- 不要携带 `_key`/`_secret` 在 body——CMDB 会剔除（它们应作为查询参数做认证）

### 4.3 auto_accept

若规则的 `auto_accept` 为 `true`，上报成功后 CMDB **立即执行接纳**，将数据转成正式 CI。此时字段一致性尤为重要：

- `instance` 中**必须包含唯一字段**（映射到模型唯一属性的那个 ad_key），否则接纳时 `CIManager.add` 报 400 `unique_key_required`
- `unique_value` 必须等于该唯一字段的值

### 4.4 数据删除

采集源资源消失时，Agent 应主动清理：

```
DELETE /api/v0.1/adc?type_id=5&unique_value=i-bp67acfmxazb4p****
```

> 注意：删除发现实例**不会**级联删除已接纳的正式 CI（CMDB 侧 `delete2` 留有 `# TODO: delete ci`）。

### 4.5 执行历史上报（可选）

Agent 每次执行可上报日志，便于 CMDB 界面展示：

```
POST /api/v0.1/adc/exec/histories
{ "type_id": 5, "stdout": "collect ok" }
```

---

## 5. 认证与签名

### 5.1 凭证来源

- `_key`/`_secret` 是 **CMDB 用户/角色的 API 凭证**，创建用户时自动生成（`key = uuid4().hex`，`secret = 32 位随机串`）
- 为 agent 准备的专用用户是 **`cmdb_agent`**：
  ```bash
  python cli.py add-user cmdb_agent <email> ...
  python cli.py cmdb-agent-init     # 打印 Key/Secret 并授予全部 CI 读写增删权限
  ```
- 这组凭证**只配置在 OneMaster**，安装 OneAgent 时无需任何 CMDB 信息

### 5.2 签名算法

**`_secret` 不是裸密钥**，而是服务端校验的签名值：

```python
# 服务端校验（User.authenticate_with_key）:
sha1(path + user.secret + "".join(req_args)) == 请求的 _secret
```

Agent 侧计算：

```
_secret = sha1hex(
    请求路径 path                     # 如 "/api/v0.1/adc"
  + 原始 secret（cmdb-agent-init 打印的值）
  + "".join(除 _key/_secret 外、按 key 排序的所有标量参数)
)
```

细节：
- 参数按 key 名排序后拼接 value（只拼标量，排除 dict/list）
- `_key` 与 `_secret` 放在 **查询参数** 中发送
- Agent 必须持有**原始 secret** 才能签名——安装配置的就是原始值

### 5.3 接口权限要求

| 接口 | 认证 | 附加要求 |
|------|------|---------|
| `GET /adt/sync` | 必须 | 仅 `cmdb_agent` / `worker` / `admin`，否则 403 |
| `POST/PUT/DELETE /adc` | 必须 | 无特权用户要求（认证通过即可） |

---

## 6. unique_value 的确定规则

**总原则**：`unique_value` 必须等于 `instance` 中唯一字段（ad_key）的值，且**重复采集时稳定不变**。它被 CMDB 用作去重键，也决定接纳后正式 CI 的唯一属性值。

### 6.1 分场景来源

| 规则类型 | unique_value 来源 | 说明 |
|---------|------------------|------|
| **Plugin** | `instance[adr.unique_key]` | 同步下发的 `adr.unique_key` 就是字段名 |
| **HTTP 云资源** | `instance[collect_key 约定字段]` | 采集器内置映射表，如 ECS→`InstanceId`、Disk→`DiskId` |
| **SNMP** | `instance["sn"]` | 序列号；缺失时用 MAC 等稳定标识生成确定性 UUID |
| **Components** | `IP:Port` 或实例标识 | 采集器自定，如 `"10.0.0.5:3306"` |
| **Agent（本机）** | 机器自身 UUID / hostname | Linux `dmidecode -s system-uuid` 等 |

### 6.2 一致性约束

CMDB 在配置 ADT 时**强制要求**：模型唯一属性名必须出现在映射 `attributes` 的 value 里（否则 400 `ad_not_unique_key`）。因此：

- 管理员把 Agent 上报的某个 ad_key 映射到模型唯一属性
- **Agent 的 unique_value 字段必须恰好是那个 ad_key**，两边才对齐

⚠️ **反面教材**：若模型唯一属性是**手工录入的随机 UUID v4**（与采集身份无关），Agent 采集不到该值，自动发现永远无法匹配到那条记录——唯一的凭证 `unique_value` 对不上。必须保证唯一键来自采集数据。

### 6.3 稳定性要求

- `unique_value` 必须确定性：同一资源每次生成相同值
- **禁止用时间戳 / 随机数**生成，否则每次上报都被当成新数据，`c_ad_ci` 表无限膨胀
- 缺失时用确定性算法兜底：`UUIDv5(namespace, 稳定标识如 MAC/IP/SN)`

---

## 7. 端到端流程示例

以"OneMaster 管理一台 OneAgent，执行一条 Plugin 规则"为例：

```
┌─ OneMaster ────────────────────────────────────────────────────┐
│ ① 为 agent 同步规则                                             │
│    GET /adt/sync?oneagent_id=0xABCD&oneagent_name=a1           │
│    → rules: [{ id:1, type_id:5, attributes:{instance_id:uuid,...}, │
│                adr:{ type:"plugin", plugin_script:"...", unique_key:"instance_id" } }] │
│ ② 下发规则给 OneAgent                                           │
└───────────────┬────────────────────────────────────────────────┘
                │ 分发规则（含 plugin_script）
┌─ OneAgent ────▼────────────────────────────────────────────────┐
│ ③ 执行插件: python plugin.py                                    │
│    stdout: AutoDiscovery::Result::[{"instance_id":"vm-001",...}] │
│ ④ 解析标记行得到采集结果                                         │
│ ⑤ unique_value = result[0]["instance_id"]                      │
│ ⑥ 把结果 + unique_value 回传给 OneMaster                        │
└───────────────┬────────────────────────────────────────────────┘
                │ 上报数据
┌─ OneMaster ───▼────────────────────────────────────────────────┐
│ ⑦ POST /adc (带 _key/_secret 签名)                              │
│    { type_id:5, adt_id:1, instance:{...}, unique_value:"vm-001" } │
│ ⑧ 本地持久化 last_update_at                                     │
└───────────────┬────────────────────────────────────────────────┘
                │
┌─ CMDB ────────▼────────────────────────────────────────────────┐
│ ⑨ (type_id, unique_value) upsert → 存 c_ad_ci                  │
│ ⑩ 若 auto_accept: 按映射转换属性，创建/更新正式 CI               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. 实现注意事项

1. **Cron 调度**：每条规则独立一个 cron（标准 5 位格式：分 时 日 月 周）。`robfig/cron`（Go）等库可直接使用。
2. **增量同步**：Agent 本地持久化 `last_update_at`，每次同步传回；无变化时服务端返回空规则。
3. **跳过禁用规则**：`enabled: false` 的规则仍会下发，Agent 不要执行。
4. **凭证解密**：同步下发的 `extra_option.key/secret/password` 已是明文（仅 `cmdb_agent` 等特权用户可见），Agent 直接用于云平台鉴权。
5. **唯一字段自检**：上报前确认 `instance` 中包含唯一字段且 `unique_value` 等于其值（否则可能 400 或产生脏数据）。
6. **幂等上报**：重复上报是安全的（upsert），无需额外去重逻辑。
7. **超时与隔离**：执行插件脚本建议加超时（如 5 分钟）、进程隔离（崩溃不影响 Agent 主进程）、限制资源。
8. **执行历史**：每次采集可上报 stdout 到 `/adc/exec/histories`，便于排查。
9. **网络设备**：SNMP 发现到的设备含 `ports` 字段时，接纳后会额外生成端口 CI（Agent 无需处理，CMDB 异步完成）。

---

## 9. 接口速查表

### 规则同步

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/adt/sync?oneagent_id=&oneagent_name=&last_update_at=` | 拉取规则（仅 `cmdb_agent`/`worker`/`admin`） |
| `GET` | `/adt/{adt_id}/sync/histories` | 同步历史 |

### 数据上报

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST/PUT` | `/adc` | 上报/更新实例（upsert） |
| `DELETE` | `/adc?type_id=&unique_value=` | 按类型+唯一值删除 |
| `POST` | `/adc/exec/histories` | 上报执行历史（`type_id` + `stdout`） |

### 认证

| 参数 | 位置 | 说明 |
|------|------|------|
| `_key` | 查询参数 | `cmdb_agent` 用户的 key |
| `_secret` | 查询参数 | `sha1(path + secret + 排序参数拼接)` |

---

## 相关文件

| 文件 | 说明 |
|------|------|
| `cmdb-api/api/lib/cmdb/auto_discovery/auto_discovery.py` | 核心业务逻辑（同步匹配、upsert、接纳） |
| `cmdb-api/api/lib/cmdb/safe_script.py` | 插件脚本 AST 沙箱校验 |
| `cmdb-api/api/views/cmdb/auto_discovery.py` | API 路由 |
| `cmdb-api/api/models/cmdb.py` | 数据模型 |
| `cmdb-ui/src/modules/cmdb/lang/zh.js` | 插件脚本默认模板（`pluginScript`） |
| `docs/auto_discovery.md` | 自动发现总览（含 Go 实现架构建议） |
