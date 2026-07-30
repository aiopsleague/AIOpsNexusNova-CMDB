# 初始化命令说明

> 对应 `dev.sh` 中 `run_init()` 执行的六个初始化命令。这些命令在 CMDB 首次部署或升级时用于建表、补齐列、预热缓存、初始化权限体系等。

## 执行顺序

```
db-setup                      → 先建表（基础）
common-check-new-columns      → 补齐新列（模型迁移）
cmdb-init-cache               → 预热 CI 缓存
cmdb-init-acl                 → 建立 CMDB 权限体系
init-import-user-from-acl     → 同步 ACL 用户到员工表
init-department               → 初始化部门并绑定 ACL 角色
```

> 部分命令（如 `cmdb-init-acl`）不是幂等的，在已初始化的库上重新执行会报错。`dev.sh` 采用「逐条执行、失败只告警不中断」的策略 (`dev.sh:186-207`)。

---

## 1. `db-setup`

**源文件**: `cmdb-api/api/commands/common.py:86-109`

**作用**: 创建所有数据库表（DDL 建表）。

- 导入所有 ORM 模型（`api.models.acl`、`api.models.cmdb`、`api.models.common_setting`），确保它们注册到 SQLAlchemy 元数据中
- 调用 `db.Model.metadata.create_all(db.engine)` 创建所有缺失的表
- 设置 MySQL `sql_mode`（`STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION`）
- 设置 `tidb_enable_noop_functions='ON'`（TiDB 兼容性）

**幂等性**: 是 — 只创建不存在的表，不改变已存在的表。

---

## 2. `common-check-new-columns`

**源文件**: `cmdb-api/api/commands/click_common_setting.py:207-213`  
**核心逻辑**: `cmdb-api/api/lib/common_setting/utils.py:33-92`

**作用**: 将 ORM 模型中新添加的列自动同步到数据库（`ALTER TABLE ADD COLUMN`）。

- 遍历数据库表，对比数据库现有列与 ORM 模型定义的列
- 如果模型中定义但数据库里没有 → 执行 `ALTER TABLE ... ADD COLUMN` 追加新列
- 检查 ENUM 列是否需要变更
- 为新列自动添加相应索引

> 这是升级迁移的辅助命令 — 代码升级后模型新增了字段，运行此命令即可自动补齐数据库列，无需手动编写 ALTER 语句。

---

## 3. `cmdb-init-cache`

**源文件**: `cmdb-api/api/commands/click_cmdb.py:51-116`

**作用**: 初始化 Redis 缓存（或 ES 索引），将 CMDB 核心数据预热到缓存中。

具体操作：

1. **CI 关系缓存**: 将所有 CI 关系加载到 Redis，构建两个映射：
   - `REDIS_PREFIX_CI_RELATION`：一级关系（`first_ci_id → {second_ci_id: type_id}`）
   - `REDIS_PREFIX_CI_RELATION2`：带祖先路径的关系（`"ancestor_ids,first_ci_id" → {second_ci_id: type_id}`）
2. **ES 索引映射**（仅在启用 `USE_ES` 时）: 为所有属性在 Elasticsearch 中创建索引映射，文本类型使用 `ik_max_word` / `ik_smart` 中文分词器，索引字段附带 `keyword` 子字段
3. **CI 详情缓存**: 遍历所有 CI，逐个将其完整信息写入 Redis 或 ES（已存在的跳过）

**幂等性**: 基本幂等 — 已缓存的 CI 会跳过。

---

## 4. `cmdb-init-acl`

**源文件**: `cmdb-api/api/commands/click_cmdb.py:119-177`

**作用**: 初始化 CMDB 模块的 ACL 权限体系。

具体操作：

1. **创建资源类型**（ResourceType）:
   - 为 `ResourceTypeEnum` 中定义的所有资源类型（CI、CI_TYPE、RELATION_VIEW、TOPOLOGY_VIEW、CI_TYPE_RELATION、CI_FILTER、PAGE 等）注册到 ACL 系统
   - 各资源类型配置对应的可用权限：
     - `CI_FILTER` / `PAGE`：仅 `READ`
     - `CI_TYPE_RELATION`：`ADD`、`DELETE`、`GRANT`
     - `RELATION_VIEW` / `TOPOLOGY_VIEW`：`READ`、`UPDATE`、`DELETE`、`GRANT`
     - 其他（CI、CI_TYPE 等）：全部权限

2. **创建角色**（Role）:
   - `CONFIG`：配置管理角色（管理员级）
   - `CMDB_READ_ALL`：全部 CI 读权限角色

3. **创建资源并授权**:
   - 为每个 CI Type 创建对应的 Resource 记录
   - 将 `CMDB_READ_ALL` 角色授予每个 CI Type 的 `READ` 权限
   - 为每个关联视图（RelationView）创建 Resource 并授予 `READ` 权限

**幂等性**: 否 — 在已初始化的库上会因资源/角色已存在而抛出 `AbortException`。

---

## 5. `init-import-user-from-acl`

**源文件**: `cmdb-api/api/commands/click_common_setting.py:186-192`  
**核心逻辑**: `cmdb-api/api/commands/click_common_setting.py:13-57`

**作用**: 将 ACL 系统中的用户导入到「员工管理」（Employee）表中。

具体操作：

1. 先执行 `InitDepartment().init()` — 确保「全公司」部门存在
2. 从 ACL 系统获取所有用户列表
3. 对每个 ACL 用户：
   - 已存在于 Employee 表 → 更新 `acl_uid`、`acl_rid`、`block` 状态
   - 不存在 → 在 Employee 表中创建新记录，关联 ACL 用户信息（跳过密码字段）

> 这实现了 ACL 认证体系与组织人员管理的桥接 — 在 ACL 中创建的用户需要同步到员工表才能参与部门、通知等业务。

---

## 6. `init-department`

**源文件**: `cmdb-api/api/commands/click_common_setting.py:195-204`  
**核心逻辑**: `cmdb-api/api/commands/click_common_setting.py:66-184`

**作用**: 部门初始化。

具体操作：

1. **`init_wide_company()`** — 创建根部门「全公司」（`department_id=0`, `department_parent_id=-1`）
2. **`create_acl_role_with_department()`** — 为每个已有部门在 ACL 中创建对应的角色，并回写 `acl_rid` 到部门记录，实现部门与 ACL 角色的绑定
3. **`init_backend_resource()`** — 为 admin 用户授予「backend」应用的 ACL 权限

**幂等性**: 基本幂等 — 已存在的部门会跳过或更新。

---

## 使用方式

```bash
# FastAPI 后端
cd cmdb-api && uv run python cli.py <命令名>

# 或通过 dev.sh 一键执行全部初始化
./dev.sh init
```
