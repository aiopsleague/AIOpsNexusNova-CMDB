# 关系类型多语言显示 — 设计与实施计划

> 状态：待确认 | 日期：2026-08-05

## 背景

`c_relation_types` 表目前只有一个 `name` 字段（`VARCHAR(16)`），存储单一语言的关系类型名称。系统切换语言时，拓扑图边标签、模型关系表格、管理页面等所有位置的名称文字不会变化。

当前 i18n（`cmdb-ui/src/modules/cmdb/lang/zh.js` / `en.js` 中 `relation_type` 部分）只覆盖了 UI 标签（按钮、提示文字），没有覆盖数据本身的翻译。

## 目标

为关系类型（RelationType）添加 `name_en` 字段，根据请求的 `Accept-Language` 自动返回对应语言的关系类型名称，实现全系统多语言显示。

## 影响范围分析

### 数据库

| 表 | 操作 | 说明 |
|---|------|------|
| `c_relation_types` | 添加列 `name_en` | `VARCHAR(64) NULL DEFAULT ''`，比 `name` 的 16 字符更长以容纳英文 |

### 后端影响文件

| 文件 | 改动程度 | 说明 |
|------|---------|------|
| [api/models/cmdb.py:22-27](cmdb-api/api/models/cmdb.py#L22-L27) | 小 | Model 添加 `name_en` 列定义 |
| [api/lib/cmdb/relation_type.py](cmdb-api/api/lib/cmdb/relation_type.py) | 小 | `add()`/`update()` 支持 `name_en` 参数 |
| [api/views/cmdb/relation_type.py](cmdb-api/api/views/cmdb/relation_type.py) | 小 | POST/PUT 接口接收 `name_en` |
| [api/lib/cmdb/ci_type.py:911](cmdb-api/api/lib/cmdb/ci_type.py#L911) | **关键** | `_wrap_relation_type_dict` 改用 `get_display_name()` |
| [api/core/i18n.py](cmdb-api/api/core/i18n.py) | 无 | 已有 `get_locale()`，复用即可 |
| 数据库迁移 | 新文件 | Alembic migration `0004_add_name_en_to_relation_types` |

### 前端影响文件

| 文件 | 改动程度 | 说明 |
|------|---------|------|
| [cmdb-ui/src/modules/cmdb/views/relation_type/index.vue](cmdb-ui/src/modules/cmdb/views/relation_type/index.vue) | 中 | 添加 `name_en` 编辑列 |
| [cmdb-ui/src/modules/cmdb/lang/zh.js](cmdb-ui/src/modules/cmdb/lang/zh.js#L821) | 小 | 添加 `nameEnTips` 等 UI 文本 |
| [cmdb-ui/src/modules/cmdb/lang/en.js](cmdb-ui/src/modules/cmdb/lang/en.js#L824) | 小 | 同上英文版 |
| 拓扑图边标签 | **无需改** | 后端返回已选语言名称 |
| 模型关系表格 | **无需改** | 同上 |
| CI 类型关系 Tab | **无需改** | 同上 |
| 操作审计 | **无需改** | 同上 |
| 关系搜索 | **无需改** | 同上 |

### 下游自动生效的位置

以下位置渲染 `relation_type.name` 或 `relation_type` 字符串，后端 `_wrap_relation_type_dict` 改动后全部自动获得正确语言：

- 拓扑图边标签：[ciDetailRelationTopo/index.vue:250](cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue#L250)
- 模型关系表格：[modelRelationTable.vue](cmdb-ui/src/modules/cmdb/views/model_relation/modules/modelRelationTable.vue)
- CI 类型关系 Tab：[relationTable.vue](cmdb-ui/src/modules/cmdb/views/ci_types/relationTable.vue)
- 服务树定义：[preference_relation/index.vue](cmdb-ui/src/modules/cmdb/views/preference_relation/index.vue)
- 操作审计：[operation_history/modules/relation.vue](cmdb-ui/src/modules/cmdb/views/operation_history/modules/relation.vue)
- 关系搜索：[relationSearch/index.vue](cmdb-ui/src/modules/cmdb/views/resource_search_2/relationSearch/index.vue)
- CI 详情关系：[ciDetailRelation.vue](cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue)

## 详细设计

### Step 1：数据库迁移

```python
# migrations/versions/0004_add_name_en_to_relation_types.py
"""add name_en to c_relation_types

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-05
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('c_relation_types',
        sa.Column('name_en', sa.String(64), nullable=True, server_default=''))

def downgrade():
    op.drop_column('c_relation_types', 'name_en')
```

### Step 2：Model 改动

[api/models/cmdb.py](cmdb-api/api/models/cmdb.py#L22-L27)：

```python
class RelationType(Model):
    __tablename__ = "c_relation_types"

    name = db.Column(db.String(16), index=True, nullable=False)
    name_en = db.Column(db.String(64), nullable=True, default='')
    color = db.Column(db.String(7), default='#1890ff', nullable=False, server_default='#1890ff')

    def get_display_name(self):
        """根据当前请求语言返回对应的名称"""
        from api.core.i18n import get_locale
        locale = get_locale()
        if locale and locale.startswith('en') and self.name_en:
            return self.name_en
        return self.name
```

### Step 3：Manager 改动

[api/lib/cmdb/relation_type.py](cmdb-api/api/lib/cmdb/relation_type.py)：

- `add(name, color=None, name_en=None)` — kwargs 中增加 `name_en`
- `update(rel_id, name, color=None, name_en=None)` — 同上

### Step 4：View 改动

[api/views/cmdb/relation_type.py](cmdb-api/api/views/cmdb/relation_type.py)：

- POST/PUT 方法中从 `request.values.get("name_en")` 获取 `name_en` 参数
- 传递给 Manager 的 `add()`/`update()`

### Step 5：核心改动 — `_wrap_relation_type_dict`

[api/lib/cmdb/ci_type.py:911](cmdb-api/api/lib/cmdb/ci_type.py#L911)：

```python
# 修改前
ci_type_dict["relation_type"] = relation_inst.relation_type.name

# 修改后
ci_type_dict["relation_type"] = relation_inst.relation_type.get_display_name()
```

这是最关键的一行改动 —— 所有下游（拓扑图、表格、搜索等）通过此方法获取关系类型名称，改一行即全局生效。

### Step 6：前端管理页面

[cmdb-ui/src/modules/cmdb/views/relation_type/index.vue](cmdb-ui/src/modules/cmdb/views/relation_type/index.vue)：

1. 表格添加 `name_en` 列（可编辑文本输入）
2. `handleCreate()` 中 `newRow` 增加 `name_en: ''`
3. `createRelationType()` 和 `updateRelationType()` 的 data 中增加 `name_en`
4. `handleEditClose()` 中判断逻辑增加 `name_en` 变更检测

### Step 7：前端 i18n 补充

[zh.js](cmdb-ui/src/modules/cmdb/lang/zh.js#L821-L825)：

```js
relation_type: {
    addRelationType: '新增关系类型',
    nameTips: '请输入类型名（中文）',
    nameEnTips: '请输入英文名',
    color: '颜色',
},
```

[en.js](cmdb-ui/src/modules/cmdb/lang/en.js#L824-L828)：

```js
relation_type: {
    addRelationType: 'New',
    nameTips: 'Please enter type name (Chinese)',
    nameEnTips: 'Please enter English name',
    color: 'Color',
},
```

## 注意事项

1. **`RelationTypeCache`** ([cache.py:100-128](cmdb-api/api/lib/cmdb/cache.py#L100-L128)) — 通过 `name` 做 key 查找（如 `ci_relation.py:150` 解析请求中的关系类型名），前端请求仍传中文名，不受影响。

2. **`name` 字段长度**当前 `VARCHAR(16)`，对中文足够；`name_en` 设为 `VARCHAR(64)` 以容纳较长英文。

3. **`get_names()` / `get_pairs()`** — 保持返回 `name`（中文），仅展示层用 `get_display_name()`。

4. **`to_dict()` 序列化** — `FormatMixin.to_dict()` 自动序列化所有映射列，`name_en` 会被包含在 API 返回中。前端可选择使用或忽略。

5. **回退策略** — `get_display_name()` 中当 `name_en` 为空时自动回退到 `name`，兼容旧数据（已存在的类型没有英文名）。

## 为什么不用纯前端 i18n 映射

关系类型是**用户可管理**的（relation_type/index.vue 支持增删改），用户可随时创建新类型。纯前端在 i18n 文件中维护映射表无法覆盖动态创建的类型，新增类型时必须同时更新两个语言文件，容易遗漏。
