# CI Relation Topo — Colored Edges by Relation Type — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable per-relation-type colors to edges in the CI detail relation topology graph, with a user-toggleable display of relation type labels on edges.

**Architecture:** Backend: add `color` column to `RelationType` model, update API to accept/return color, propagate `relation_type_color` through CI type relation data. Frontend: add color picker to relation type management table, pass relation type data (name + color) to topology edges, add toggle switch to enable/disable edge labels and colors, re-render on toggle change.

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy / Alembic (backend), Vue 2.6 / Ant Design Vue / butterfly-dag / vxe-table (frontend)

---

## Task 1: Backend — Add `color` column to RelationType model

**Files:**
- Modify: `cmdb-api/api/models/cmdb.py:22-25`
- Create: `cmdb-api/migrations/versions/0003_add_color_to_relation_types.py`

- [ ] **Step 1: Add `color` column to RelationType model**

In `cmdb-api/api/models/cmdb.py`, modify the `RelationType` class (lines 22-25):

```python
class RelationType(Model):
    __tablename__ = "c_relation_types"

    name = db.Column(db.String(16), index=True, nullable=False)
    color = db.Column(db.String(7), default='#1890ff', nullable=False, server_default='#1890ff')
```

- [ ] **Step 2: Create Alembic migration**

Create `cmdb-api/migrations/versions/0003_add_color_to_relation_types.py`:

```python
# -*- coding:utf-8 -*-


"""add color to c_relation_types

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('c_relation_types', sa.Column('color', sa.String(7), nullable=False, server_default='#1890ff'))


def downgrade():
    op.drop_column('c_relation_types', 'color')
```

- [ ] **Step 3: Run migration to verify it works**

```bash
cd cmdb-api && uv run alembic upgrade head
```
Expected: migration runs without errors.

- [ ] **Step 4: Commit**

```bash
git add cmdb-api/api/models/cmdb.py cmdb-api/migrations/versions/0003_add_color_to_relation_types.py
git commit -m "feat: add color column to RelationType model

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 2: Backend — Update RelationTypeManager to handle color

**Files:**
- Modify: `cmdb-api/api/lib/cmdb/relation_type.py`

- [ ] **Step 1: Update `add()` method to accept and store color**

In `cmdb-api/api/lib/cmdb/relation_type.py`, modify the `add` method:

```python
@staticmethod
def add(name, color=None):
    RelationType.get_by(name=name, first=True, to_dict=False) and abort(
        400, ErrFormat.relation_type_exists.format(name))

    kwargs = dict(name=name)
    if color is not None:
        kwargs['color'] = color

    return RelationType.create(**kwargs)
```

- [ ] **Step 2: Update `update()` method to accept and store color**

In the same file, modify the `update` method:

```python
@staticmethod
def update(rel_id, name, color=None):
    existed = RelationType.get_by_id(rel_id) or abort(
        404, ErrFormat.relation_type_not_found.format("id={}".format(rel_id)))

    kwargs = dict(name=name)
    if color is not None:
        kwargs['color'] = color

    return existed.update(**kwargs)
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-api/api/lib/cmdb/relation_type.py
git commit -m "feat: accept color in RelationTypeManager add/update

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 3: Backend — Update relation type API views to accept color

**Files:**
- Modify: `cmdb-api/api/views/cmdb/relation_type.py`

- [ ] **Step 1: Update POST handler to accept color**

In `cmdb-api/api/views/cmdb/relation_type.py`, modify `relation_type_view_post` (line 35-39):

```python
@router.post("/relation_types/{rel_id}")
@router.post("/relation_types")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Relationship_Types,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
@args_validate(RelationTypeManager.cls)
def relation_type_view_post(rel_id: int = None):
    name = request.values.get("name") or abort(400, ErrFormat.argument_value_required.format("name"))
    color = request.values.get("color", None)
    rel = RelationTypeManager.add(name, color=color)

    return rel.to_dict()
```

- [ ] **Step 2: Update PUT handler to accept color**

In the same file, modify `relation_type_view_put` (line 48-52):

```python
@router.put("/relation_types/{rel_id}")
@router.put("/relation_types")
@perms_role_required(app_cli.app_name, app_cli.resource_type_name, app_cli.op.Relationship_Types,
                     app_cli.op.read, app_cli.admin_name)
@args_required("name")
@args_validate(RelationTypeManager.cls)
def relation_type_view_put(rel_id: int = None):
    name = request.values.get("name") or abort(400, ErrFormat.argument_value_required.format("name"))
    color = request.values.get("color", None)
    rel = RelationTypeManager.update(rel_id, name, color=color)

    return rel.to_dict()
```

- [ ] **Step 3: Commit**

```bash
git add cmdb-api/api/views/cmdb/relation_type.py
git commit -m "feat: accept color in relation type POST/PUT API

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 4: Backend — Include `relation_type_color` in CI type relation data

**Files:**
- Modify: `cmdb-api/api/lib/cmdb/ci_type.py:900-916`

- [ ] **Step 1: Add `relation_type_color` to `_wrap_relation_type_dict`**

In `cmdb-api/api/lib/cmdb/ci_type.py`, inside `CITypeRelationManager._wrap_relation_type_dict()` (line 911), add the color field:

In the method at line 911, change:
```python
ci_type_dict["relation_type"] = relation_inst.relation_type.name
```
to:
```python
ci_type_dict["relation_type"] = relation_inst.relation_type.name
ci_type_dict["relation_type_color"] = relation_inst.relation_type.color
```

- [ ] **Step 2: Commit**

```bash
git add cmdb-api/api/lib/cmdb/ci_type.py
git commit -m "feat: include relation_type_color in CI type relation data

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 5: Frontend — Add color column to relation type management UI

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/relation_type/index.vue`

- [ ] **Step 1: Add color column to the vxe-table**

In `cmdb-ui/src/modules/cmdb/views/relation_type/index.vue`, add a color column between `name` and `updateTime`. The column uses a native `<input type="color">` for editing and displays a colored circle for view mode.

Replace the template (lines 1-40) with:

```vue
<template>
  <a-card :bordered="false">
    <div class="action-btn">
      <a-button @click="handleCreate" type="primary" style="margin-bottom: 15px;">{{ $t('cmdb.relation_type.addRelationType') }}</a-button>
    </div>
    <vxe-table
      ref="relationTypeTable"
      :data="tableData"
      keep-source
      highlight-hover-row
      :edit-config="{ trigger: 'manual', mode: 'row' }"
      @edit-closed="handleEditClose"
      stripe
      class="ops-stripe-table"
      bordered
    >
      <vxe-table-column
        field="name"
        :title="$t('name')"
        :edit-render="{ name: 'input', attrs: { type: 'text' }, events: { keyup: customCloseEdit } }"
      ></vxe-table-column>
      <vxe-table-column
        field="color"
        :title="$t('cmdb.relation_type.color')"
        width="100"
        align="center"
      >
        <template #default="{ row }">
          <div
            class="color-swatch"
            :style="{ backgroundColor: row.color || '#1890ff' }"
          ></div>
        </template>
        <template #edit="{ row }">
          <input
            type="color"
            v-model="row.color"
            style="width: 50px; height: 28px; border: 1px solid #d9d9d9; border-radius: 2px; cursor: pointer;"
          />
        </template>
      </vxe-table-column>
      <vxe-table-column field="updateTime" :title="$t('updated_at')">
        <template #default="{row}">
          {{ row.updated_at || row.created_at }}
        </template>
      </vxe-table-column>
      <vxe-table-column field="operation" :title="$t('operation')" align="center">
        <template #default="{row}">
          <template>
            <a><a-icon type="edit" @click="handleEdit(row)"/></a>
            <a-divider type="vertical" />
            <a-popconfirm :title="$t('confirmDelete')" @confirm="handleDelete(row)" :okText="$t('yes')" :cancelText="$t('no')">
              <a :style="{ color: 'red' }"><a-icon type="delete"/></a>
            </a-popconfirm>
          </template>
        </template>
      </vxe-table-column>
    </vxe-table>
  </a-card>
</template>
```

- [ ] **Step 2: Update `handleCreate()` to include default color**

In the script section, modify `handleCreate()` (line 75-82):

```js
handleCreate() {
  const $table = this.$refs.relationTypeTable
  const newRow = {
    name: '',
    color: '#1890ff',
    created_at: moment().format('YYYY-MM-DD hh:mm:ss'),
  }
  $table.insert(newRow).then(({ row }) => $table.setActiveRow(row))
},
```

- [ ] **Step 3: Update `handleEditClose()` to include color in create/update calls**

Modify `handleEditClose()` (lines 83-98):

```js
handleEditClose({ row, rowIndex, column }) {
  const $table = this.$refs.relationTypeTable
  if (row.id) {
    if (row.name && ($table.isUpdateByRow(row, 'name') || $table.isUpdateByRow(row, 'color'))) {
      this.updateRelationType(row.id, { name: row.name, color: row.color })
    } else {
      $table.revertData(row)
    }
  } else {
    if (row.name) {
      this.createRelationType({ name: row.name, color: row.color || '#1890ff' })
    } else {
      this.loadData()
    }
  }
},
```

- [ ] **Step 4: Add color swatch CSS to the component**

In the `<style lang="less" scoped>` section:

```less
.color-swatch {
  display: inline-block;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid #d9d9d9;
  vertical-align: middle;
}
```

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/relation_type/index.vue
git commit -m "feat: add color column to relation type management table

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 6: Frontend — Build edge helper, attach labels and colors to initial topology edges

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue`

- [ ] **Step 1: Update `handleTopoData()` to attach relation type info to edges**

In `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue`, modify the edge creation code in `handleTopoData()`.

For parent edges (lines 221-228), change from:
```js
edges.push({
  id: `${parentCi._id}_Root`,
  source: 'right',
  target: 'left',
  sourceNode: `${parentCi._id}`,
  targetNode: `Root_${this.currentTypeId}`,
  type: 'endpoint',
})
```
to:
```js
edges.push({
  id: `${parentCi._id}_Root`,
  source: 'right',
  target: 'left',
  sourceNode: `${parentCi._id}`,
  targetNode: `Root_${this.currentTypeId}`,
  type: 'endpoint',
  label: parent.relation_type || '',
  labelPosition: 0.5,
  strokeColor: parent.relation_type_color || '#1890ff',
})
```

For child edges (lines 268-275), change from:
```js
edges.push({
  id: `Root_${childCi._id}`,
  source: 'right',
  target: 'left',
  sourceNode: `Root_${this.currentTypeId}`,
  targetNode: `${childCi._id}`,
  type: 'endpoint',
})
```
to:
```js
edges.push({
  id: `Root_${childCi._id}`,
  source: 'right',
  target: 'left',
  sourceNode: `Root_${this.currentTypeId}`,
  targetNode: `${childCi._id}`,
  type: 'endpoint',
  label: child.relation_type || '',
  labelPosition: 0.5,
  strokeColor: child.relation_type_color || '#1890ff',
})
```

- [ ] **Step 2: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue
git commit -m "feat: attach relation type labels and colors to initial topo edges

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 7: Frontend — Add toggle switch, expand scenario, and edge color application to topo component

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue`

This is the core task. It adds:
1. Props for `parentCITypeList`/`childCITypeList`
2. Toggle switch UI
3. Edge color application helper method
4. `redrawData()` update to look up relation types for expanded nodes
5. Re-render on toggle change

- [ ] **Step 1: Add props**

In the `<script>` section of `index.vue`, add props after the existing `inject`:

```js
props: {
  parentCITypeList: {
    type: Array,
    default: () => [],
  },
  childCITypeList: {
    type: Array,
    default: () => [],
  },
},
```

- [ ] **Step 2: Add toggle switch to template**

In the template, add the toggle switch after the existing layout radio group:

Replace lines 7-23 (the `.topo-layout-switch` div) with:

```html
<div class="topo-layout-switch">
  <a-radio-group
    v-model="currentLayout"
    size="small"
    button-style="solid"
    @change="switchLayout"
  >
    <a-radio-button value="mindmap">
      <a-icon type="apartment" />
      {{ $t('cmdb.topo.layoutMindmap') }}
    </a-radio-button>
    <a-radio-button value="compactBox">
      <a-icon type="cluster" />
      {{ $t('cmdb.topo.layoutCompactBox') }}
    </a-radio-button>
  </a-radio-group>
  <a-divider type="vertical" style="margin: 0 8px;" />
  <a-switch
    v-model="showRelationStyle"
    size="small"
    @change="handleRelationStyleToggle"
  >
    <a-icon slot="checkedChildren" type="check" />
    <a-icon slot="uncheckedChildren" type="close" />
  </a-switch>
  <span style="margin-left: 4px; font-size: 12px; color: #666;">{{ $t('cmdb.topo.relationStyle') }}</span>
</div>
```

- [ ] **Step 3: Add data, created hook, and imports**

Add `showRelationStyle` data property, `created()` hook for loading from localStorage, and import `getCITypeParent`/`getCITypeChildren`:

Add the import at the top of `<script>` (after existing imports):
```js
import { getCITypeParent, getCITypeChildren } from '@/modules/cmdb/api/CITypeRelation'
```

In the `data()` section, add:
```js
showRelationStyle: true,
_typeRelationCache: {},
```

Add a `created()` hook to load the saved preference from localStorage:

```js
created() {
  this.showRelationStyle = this.$ls.get('SHOW_RELATION_STYLE', true)
},
```

- [ ] **Step 4: Add helper method to apply edge colors**

Add this method to the `methods`:

```js
applyEdgeColors() {
  if (!this.canvas) return
  const { edges } = this.canvas.getDataMap()
  edges.forEach((edge) => {
    if (edge.dom) {
      const color = this.showRelationStyle && edge.options && edge.options.strokeColor
        ? edge.options.strokeColor
        : null
      if (color) {
        edge.dom.setAttribute('stroke', color)
      } else {
        edge.dom.removeAttribute('stroke')
      }
    }
  })
},
```

- [ ] **Step 5: Add method to fetch type relations for expanded nodes**

Add this method:

```js
async getTypeRelations(typeId) {
  if (!this._typeRelationCache[typeId]) {
    const [parentsRes, childrenRes] = await Promise.all([
      getCITypeParent(typeId),
      getCITypeChildren(typeId),
    ])
    this._typeRelationCache[typeId] = {
      parents: parentsRes?.parents || [],
      children: childrenRes?.children || [],
    }
  }
  return this._typeRelationCache[typeId]
},
```

- [ ] **Step 6: Update `setTopoData()` to apply edge colors after draw**

Modify `setTopoData()` to apply edge colors in the callback:

```js
setTopoData(data) {
  const root = document.getElementById('ci-detail-relation-topo')
  if (root && root?.innerHTML) {
    root.innerHTML = ''
  }
  this.canvas = null
  this.init()
  this.topoData = _.cloneDeep(data)

  this.canvas.redraw(data, {}, () => {
    this.canvas.focusCenterWithAnimate()
    this.$nextTick(() => {
      this.applyEdgeColors()
    })
  })
},
```

- [ ] **Step 7: Update `redrawData()` to look up relation types for expanded nodes and attach labels/colors**

Modify the `redrawData()` method. The key change is in the edge creation loop (lines 200-207). After looking up the source node's `ci_type_id` from existing nodes, fetch the type relations and attach labels.

Replace the edge creation in `redrawData()` (lines 200-207):

```js
newEdges.push({
  id: `${r._id}`,
  source: 'right',
  target: 'left',
  sourceNode: side === 'right' ? sourceNode : `${r._id}`,
  targetNode: side === 'right' ? `${r._id}` : sourceNode,
  type: 'endpoint',
})
```

With code that looks up the relation type:

```js
// Look up relation type for the edge
const { nodes } = this.canvas.getDataMap()
const sourceNodeObj = nodes.find((n) => n.id === sourceNode)
const sourceTypeId = sourceNodeObj?.options?.ci_type_id
let edgeLabel = ''
let edgeStrokeColor = '#1890ff'

if (sourceTypeId) {
  const typeRelations = await this.getTypeRelations(sourceTypeId)
  const targetList = side === 'right' ? typeRelations.children : typeRelations.parents
  const matchedType = targetList.find((t) => t.id === r._type)
  if (matchedType) {
    edgeLabel = matchedType.relation_type || ''
    edgeStrokeColor = matchedType.relation_type_color || '#1890ff'
  }
}

newEdges.push({
  id: `${r._id}`,
  source: 'right',
  target: 'left',
  sourceNode: side === 'right' ? sourceNode : `${r._id}`,
  targetNode: side === 'right' ? `${r._id}` : sourceNode,
  type: 'endpoint',
  label: edgeLabel,
  labelPosition: 0.5,
  strokeColor: edgeStrokeColor,
})
```

Also update the line that pushes to `newNodes` (line 170-198) to ensure `ci_type_id` is available in node options — it's already there as `ci_type_id: r._type`, so no change needed.

- [ ] **Step 8: Update `redrawData()` to apply edge colors after draw**

After the `this.canvas.draw(_topoData, {}, () => {})` call at line 236, add:

```js
this.$nextTick(() => {
  this.applyEdgeColors()
})
```

- [ ] **Step 9: Add toggle handler to re-render**

Add the method:

```js
handleRelationStyleToggle() {
  this.$ls.set('SHOW_RELATION_STYLE', this.showRelationStyle)
  if (this.topoData && Object.keys(this.topoData).length) {
    this.setTopoData(this.topoData)
  }
},
```

- [ ] **Step 10: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue
git commit -m "feat: add relation type labels, colors, and toggle to topo graph

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 8: Frontend — Add i18n keys and edge label styles

**Files:**
- Modify: `cmdb-ui/src/modules/cmdb/lang/zh.js`
- Modify: `cmdb-ui/src/modules/cmdb/lang/en.js`
- Modify: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.less`

- [ ] **Step 1: Add i18n keys to zh.js**

Find an appropriate location in `cmdb-ui/src/modules/cmdb/lang/zh.js` (near existing `cmdb.topo` keys) and add:

```js
// In the cmdb.topo section:
'cmdb.topo.relationStyle': '关系标注',
// In the cmdb.relation_type section:
'cmdb.relation_type.color': '颜色',
```

- [ ] **Step 2: Add i18n keys to en.js**

In `cmdb-ui/src/modules/cmdb/lang/en.js`:

```js
// In the cmdb.topo section:
'cmdb.topo.relationStyle': 'Relation Labels',
// In the cmdb.relation_type section:
'cmdb.relation_type.color': 'Color',
```

- [ ] **Step 3: Add edge label styles to index.less**

In `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.less`, add inside the `.ci-detail-relation-topo` block (after line 16, before the `}` on line 17):

```less
.butterflies-label {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
```

- [ ] **Step 4: Commit**

```bash
git add cmdb-ui/src/modules/cmdb/lang/zh.js cmdb-ui/src/modules/cmdb/lang/en.js cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.less
git commit -m "feat: add i18n keys and edge label styles for relation type edges

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Task 9: Integration — Verify end-to-end

- [ ] **Step 1: Verify backend API returns color field**

```bash
cd cmdb-api && uv run python -c "
from api.main import create_app
app = create_app()
from api.models.cmdb import RelationType
print('color' in [c.name for c in RelationType.__table__.columns])
"
```
Expected: `True`

- [ ] **Step 2: Verify CI type relations include `relation_type_color`**

Make a GET request to a CI type relation endpoint and verify the response includes `relation_type_color`:
```bash
# Start the API server, then:
curl -s http://localhost:5000/api/v0.1/ci_type_relations/1/children | python -m json.tool | grep relation_type_color
```
Expected: output shows `"relation_type_color": "#1890ff"` (or other color).

- [ ] **Step 3: Verify relation type CRUD accepts color**

```bash
# Create a relation type with color
curl -s -X POST http://localhost:5000/api/v0.1/relation_types \
  -H "Content-Type: application/json" \
  -d '{"name": "test_color_rel", "color": "#ff5500"}' | python -m json.tool
```
Expected: response includes `"color": "#ff5500"`.

- [ ] **Step 4: Clean up test data**

```bash
# Delete the test relation type (replace {id} with actual ID from previous step)
curl -s -X DELETE http://localhost:5000/api/v0.1/relation_types/{id}
```

- [ ] **Step 5: Verify frontend builds without errors**

```bash
cd cmdb-ui && yarn build
```
Expected: build succeeds.

---

## Summary

| Task | Files Changed | Description |
|------|--------------|-------------|
| 1 | Model + Migration | Add `color` column to `c_relation_types` |
| 2 | Manager | Accept `color` in `RelationTypeManager.add/update` |
| 3 | API Views | Accept `color` in POST/PUT `/relation_types` |
| 4 | ci_type.py | Include `relation_type_color` in CI type relation responses |
| 5 | relation_type/index.vue | Add color picker column to relation type management table |
| 6 | ciDetailRelation.vue | Attach `label` and `strokeColor` to initial topology edges |
| 7 | ciDetailRelationTopo/index.vue | Toggle switch, expand scenario lookups, edge color application |
| 8 | i18n + styles | Translation keys and edge label CSS |
| 9 | Integration | End-to-end verification |
