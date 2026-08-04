# CI Relation Topo — Colored Edges by Relation Type

> Feature: In the `ciDetailRelationTopo` graph, render edges with colors based on CI relation type, display the relation type name as a label on the edge, and provide a toggle to enable/disable this feature.

**Date**: 2026-08-04
**Status**: approved

---

## Overview

Currently, the CI detail relation topology graph (`ciDetailRelationTopo`) renders all edges in a uniform style — same color, no relation type information visible. Users cannot distinguish which relation type connects two CIs without knowing the CI type model.

This feature:
1. Adds a configurable **color** field to each relation type
2. Colors edges in the topology graph based on the relation type
3. Shows the relation type **name as a label** on each edge
4. Provides an **on/off toggle** so users can switch between plain and styled edges

---

## Backend Changes

### 1. Database — `c_relation_types` table

Add a `color` column:

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `color` | `VARCHAR(7)` | `'#1890ff'` | Hex color code (e.g. `#1890ff`) |

**Model change** (`cmdb-api/api/models/cmdb.py`, line 22):
```python
class RelationType(Model):
    __tablename__ = "c_relation_types"
    name = db.Column(db.String(16), index=True, nullable=False)
    color = db.Column(db.String(7), default='#1890ff')  # NEW
```

**Migration**: Alembic auto-generated migration — `ALTER TABLE c_relation_types ADD COLUMN color VARCHAR(7) DEFAULT '#1890ff'`.

### 2. API — Relation Type CRUD

**File**: `cmdb-api/api/views/cmdb/relation_type.py`

- **GET** `/v0.1/relation_types` — already returns all columns via `to_dict()`; the new `color` field is included automatically
- **POST** `/v0.1/relation_types` — accept optional `color` field (default: `#1890ff`)
- **PUT** `/v0.1/relation_types/{id}` — accept optional `color` field for updates

### 3. API — CI Type Relation data

**File**: `cmdb-api/api/lib/cmdb/ci_type.py`, method `_wrap_relation_type_dict()` (line 900)

Add `relation_type_color` to the returned dict:
```python
ci_type_dict["relation_type"] = relation_inst.relation_type.name
ci_type_dict["relation_type_color"] = relation_inst.relation_type.color  # NEW
```

This ensures `parentCITypeList` and `childCITypeList` items carry both the relation type name and color.

### 4. API — CI Relation search (expand scenario)

**File**: `cmdb-api/api/lib/cmdb/search/ci_relation/search.py`

When `redrawData()` expands a node, it calls `searchCIRelation` which returns individual CIs. Currently these records do not include relation type info. The relation type must be correlated from the CI type relation data.

Two options:
- **Option A** (simpler): The frontend already has access to `parentCITypeList`/`childCITypeList` via the parent component. Pass these as props to `ciDetailRelationTopo`, and in `redrawData()`, look up the relation type by matching the CI's `_type` (type id) against the list.
- **Option B**: Include `relation_type_id` in the CI search result so the frontend can look up the color.

**Decision**: Use Option A — no backend change needed. The `ciDetailRelationTopo` component will receive the CI type relation lists as props.

---

## Frontend Changes

### 5. Relation Type Management — Color Column

**File**: `cmdb-ui/src/modules/cmdb/views/relation_type/index.vue`

Add a color column between `name` and `updated_at`:

- Display: colored circle swatch using inline `background-color`
- Edit: use the existing `colorPicker` component (`cmdb-ui/src/modules/cmdb/components/colorPicker/index.vue`)
- Inline edit via vxe-table `edit-render`
- CRUD operations: `createRelationType` and `updateRelationType` include the `color` field

### 6. Topology Graph — Edge Styling

#### 6a. Data flow: Pass relation type lists to the topo component

**File**: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue`

- Add props to `ciDetailRelationTopo`: `:parentCITypeList` and `:childCITypeList` (the relation data already includes `relation_type` name and `relation_type_color` after backend change #3)
- In `handleTopoData()`: when building edges, look up the relation type from the CI type list, attach `label` and color to each edge object.

Edge format after change:
```js
edges.push({
  id: `${parentCi._id}_Root`,
  source: 'right', target: 'left',
  sourceNode: `${parentCi._id}`, targetNode: `Root_${this.currentTypeId}`,
  type: 'endpoint',
  label: parent.relation_type,                    // NEW: relation type name
  style: { stroke: parent.relation_type_color },   // NEW: edge color
})
```

#### 6b. Expand scenario — `redrawData()`

**File**: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue`

The `redrawData()` method calls `searchCIRelation` and creates new edges without relation type info. The root's `parentCITypeList`/`childCITypeList` only cover the root's CI type relations — expanded nodes have different CI types, so they need their own CI type relation data.

**Approach**: Fetch CI type relations on demand for the expanded node's CI type, with an in-memory cache to avoid redundant API calls.

```js
// In ciDetailRelationTopo/index.vue
import { getCITypeParent, getCITypeChildren } from '@/modules/cmdb/api/CITypeRelation'

// Cache: { typeId: { parents: [...], children: [...] } }
const typeRelationCache = {}

async getTypeRelations(typeId) {
  if (!typeRelationCache[typeId]) {
    const [parentsRes, childrenRes] = await Promise.all([
      getCITypeParent(typeId),
      getCITypeChildren(typeId),
    ])
    typeRelationCache[typeId] = {
      parents: parentsRes?.parents || [],
      children: childrenRes?.children || [],
    }
  }
  return typeRelationCache[typeId]
}
```

In `redrawData()`:
1. The clicked node has `ci_type_id` (from node options)
2. For `reverse=1` (left/parents): call `getTypeRelations(sourceNodeTypeId)`, get `parents` list — each item has `id` (parent CI type), `relation_type`, `relation_type_color`
3. For `reverse=0` (right/children): get `children` list — each item has `id` (child CI type), `relation_type`, `relation_type_color`
4. Match each search result's `_type` against the list to find the relation type
5. Attach `label` and `style` to the edge (when toggle is on)

The `ci_type_id` is already stored on each node's options (set during node creation in both `handleTopoData` and `redrawData`).

#### 6c. Toggle switch

Add a toggle switch in the topology view header (alongside the existing layout radio buttons):

```html
<div class="topo-layout-switch">
  <a-radio-group v-model="currentLayout" ...>
    <!-- existing layout buttons -->
  </a-radio-group>
  <a-switch v-model="showRelationStyle" size="small" style="margin-left: 12px">
    <template #checked>{{ $t('cmdb.topo.relationStyleOn') }}</template>
    <template #unchecked>{{ $t('cmdb.topo.relationStyleOff') }}</template>
  </a-switch>
</div>
```

- `showRelationStyle` defaults to `true` (enabled)
- Persisted via `Vue.ls` (localStorage), same pattern as other app preferences
- When `false`: edges are plain (no `label`, no `style` — current behavior)
- When `true`: edges carry `label` and `style` with relation type name and color

Implementation note: butterfly-dag does NOT support reactive updates to existing edges. When the toggle changes, the topology must be re-rendered by calling `setTopoData()` again with the updated edge data (with or without labels/colors).

### 7. i18n

**Files**: `cmdb-ui/src/modules/cmdb/lang/zh.js`, `cmdb-ui/src/modules/cmdb/lang/en.js`

```js
// zh
cmdb.topo.relationStyleOn: '关系标注',
cmdb.topo.relationStyleOff: '关系标注',

// en
cmdb.topo.relationStyleOn: 'Relation Labels',
cmdb.topo.relationStyleOff: 'Relation Labels',
```

### 8. Edge label styling

**File**: `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.less`

Add styles for the edge labels (butterfly-dag renders labels as `span.butterflies-label`):
```less
.butterflies-label {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.85);
  padding: 2px 6px;
  border-radius: 3px;
  white-space: nowrap;
  pointer-events: none;
}
```

---

## Files Summary

| Layer | File | Change |
|-------|------|--------|
| Backend | `cmdb-api/api/models/cmdb.py` | Add `color` column to `RelationType` |
| Backend | `cmdb-api/migrations/` | Alembic migration (auto) |
| Backend | `cmdb-api/api/views/cmdb/relation_type.py` | Accept `color` in POST/PUT |
| Backend | `cmdb-api/api/lib/cmdb/ci_type.py` | Include `relation_type_color` in `_wrap_relation_type_dict()` |
| Frontend | `cmdb-ui/src/modules/cmdb/views/relation_type/index.vue` | Add color picker column |
| Frontend | `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelation.vue` | Pass relation type data to topo; attach `label`+`style` to edges |
| Frontend | `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.vue` | Props, toggle switch, `redrawData()` lookup, re-render on toggle |
| Frontend | `cmdb-ui/src/modules/cmdb/views/ci/modules/ciDetailRelationTopo/index.less` | Label styling |
| Frontend | `cmdb-ui/src/modules/cmdb/lang/zh.js` | i18n keys |
| Frontend | `cmdb-ui/src/modules/cmdb/lang/en.js` | i18n keys |

---

## Edge Cases & Constraints

1. **Existing relation types without color**: Migration sets default `#1890ff`, so all existing types get a blue color automatically.
2. **Toggle off → on**: Re-render the topology with labels/colors appended to edges.
3. **Node expansion while toggle is on**: `redrawData()` must also apply color/label to newly created edges.
4. **Multiple edges between same CI types**: The relation type is determined by the CI type relation, not the CI instances — same color for all edges of the same relation type.
5. **Color validation**: Frontend color picker outputs valid hex; API accepts any 7-character hex string.

---

## Implementation Order

1. Backend: Model + migration + API changes
2. Frontend: Relation type management UI (color column)
3. Frontend: Topology graph edge styling + toggle
4. Frontend: i18n keys
5. Integration testing
