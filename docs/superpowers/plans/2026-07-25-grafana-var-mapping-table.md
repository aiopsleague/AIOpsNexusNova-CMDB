# Grafana 变量映射表格化 + 映射条目启用 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 变量映射改为表格（源/映射类型/目标/说明，滚动，源唯一），支持固定值与字段两种映射类型，映射记录增加启用开关。

**Architecture:** 后端 `get_dashboard_variables` 带 description；`var_mapping` 元素升级为 `{grafana_var, map_type, value, remark}`；`build_vars`/`pick_dashboard`/CRUD 同步升级；前端映射弹窗用 a-table 编辑变量映射，映射列表加启用列。

**Tech Stack:** FastAPI（兼容层）、requests、pytest；Vue2 + ant-design-vue 1.x。

**Spec:** `docs/superpowers/specs/2026-07-25-grafana-var-mapping-table-design.md`

## Global Constraints

- 只修改 `cmdb-api-fastapi/` 和 `cmdb-ui/`；不动 `cmdb-api/`。
- 不新增任何依赖；前端文案走 i18n（zh+en）。
- 轻量兼容旧行 `{grafana_var, ci_attr}`：`build_vars` 读取按 field+value=ci_attr 处理（规格已确认）。
- pytest：`cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -v`（当前 18 passed）。
- 提交信息：`feat(grafana): ...`。

## 关键接口约定（任务间契约）

- `GrafanaClient.get_dashboard_variables(name) -> [{"name": str, "description": str}]`
- variables 端点响应：`{"variables": [{"name", "description"}]}`
- var_mapping 元素（存储归一化后）：`{"grafana_var": str, "map_type": "field"|"fixed", "value": str, "remark": str}`
- 映射记录新增 `enable`（int 0/1，缺省 1）
- `build_vars` 行为：`fixed` 原样传 `value`（空串跳过）；`field` 取 `ci[value]`（None/""/[] 跳过）；旧键 `ci_attr` 作 `value` 回退；`mapping is None` → `[{name: "ci_name", value: unique_value}]`
- `pick_dashboard`：先过滤 `m.get("enable", 1) != 0` 的映射

---

### Task 1: 后端 grafana_client 升级 + 单测（TDD）

**Files:**
- Modify: `cmdb-api-fastapi/api/lib/common_setting/grafana_client.py`
- Test: `cmdb-api-fastapi/tests/test_grafana_client.py`

**Interfaces:**
- Produces: 新版 `get_dashboard_variables`、`build_vars`、`pick_dashboard`（契约见上）。

- [ ] **Step 1: 修改/新增测试（先确认失败）**

在 `cmdb-api-fastapi/tests/test_grafana_client.py` 中：

1. 替换 `test_get_dashboard_variables_excludes_datasource` 为：

```python
def test_get_dashboard_variables_with_description():
    client = GrafanaClient("http://g:3000/", "key")
    payload = {"dashboard": {"templating": {"list": [
        {"name": "instance", "type": "query", "description": "实例IP"},
        {"name": "datasource", "type": "datasource"},
        {"name": "maintype", "type": "query"},
        {"type": "query"},
    ]}}}
    with mock.patch("api.lib.common_setting.grafana_client.requests.get") as m:
        m.return_value.json.return_value = payload
        m.return_value.raise_for_status.return_value = None
        result = client.get_dashboard_variables("rYdddlPWo")
    assert result == [{"name": "instance", "description": "实例IP"},
                      {"name": "maintype", "description": ""}]
    args, kwargs = m.call_args
    assert args[0] == "http://g:3000/api/dashboards/uid/rYdddlPWo"
```

2. 替换 `test_build_vars_from_mapping` 与 `test_build_vars_skips_empty_values` 为：

```python
def test_build_vars_field_and_fixed():
    mapping = {"var_mapping": [
        {"grafana_var": "instance", "map_type": "field", "value": "ip", "remark": ""},
        {"grafana_var": "env", "map_type": "fixed", "value": "prod", "remark": ""},
    ]}
    ci = {"ip": "10.0.0.1"}
    assert build_vars(mapping, ci, "x") == [{"name": "instance", "value": "10.0.0.1"},
                                            {"name": "env", "value": "prod"}]


def test_build_vars_legacy_ci_attr_compat():
    mapping = {"var_mapping": [{"grafana_var": "instance", "ci_attr": "ip"}]}
    ci = {"ip": "10.0.0.1"}
    assert build_vars(mapping, ci, "x") == [{"name": "instance", "value": "10.0.0.1"}]


def test_build_vars_skips_empty_values():
    mapping = {"var_mapping": [
        {"grafana_var": "a", "map_type": "field", "value": "x"},
        {"grafana_var": "b", "map_type": "field", "value": "y"},
        {"grafana_var": "c", "map_type": "field", "value": "z"},
        {"grafana_var": "d", "map_type": "field", "value": "w"},
        {"grafana_var": "e", "map_type": "fixed", "value": ""},
        {"grafana_var": "f", "map_type": "fixed", "value": "keep"},
    ]}
    ci = {"x": "", "y": None, "z": [], "w": "keep"}
    assert build_vars(mapping, ci, "v") == [{"name": "d", "value": "keep"},
                                            {"name": "f", "value": "keep"}]
```

3. 新增 pick_dashboard 映射启用测试：

```python
def test_pick_dashboard_skips_disabled_mapping():
    mappings = [{"id": 1, "ci_type_id": 3, "connection_id": 2, "dashboard_name": "xyz",
                 "var_mapping": [], "enable": 0}]
    picked = pick_dashboard([CONN1, CONN2], mappings, 3, "host-01", _ok_search([DASH]))
    # 映射停用 → 视同无映射 → 全局搜索（CONN1 先命中）
    assert picked["connection"] is CONN1
    assert picked["mapping"] is None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -q`
Expected: 上述测试 FAIL

- [ ] **Step 3: 实现 grafana_client.py 改动**

3a. `get_dashboard_variables` 返回部分改为：

```python
        templating = (resp.json().get("dashboard") or {}).get("templating") or {}
        return [{"name": v.get("name"), "description": v.get("description") or ""}
                for v in (templating.get("list") or [])
                if v.get("name") and v.get("type") != "datasource"]
```

3b. `pick_dashboard` 的 mapping 查找行改为（加 enable 过滤）：

```python
    mapping = next((m for m in mappings
                    if m.get("ci_type_id") == ci_type_id and m.get("enable", 1) != 0), None)
```

3c. `build_vars` 整体替换为：

```python
def build_vars(mapping, ci, unique_value):
    """Build the template-var list for the iframe url.

    var_mapping item: {"grafana_var", "map_type": "field"|"fixed", "value", "remark"}
    旧格式 {"grafana_var", "ci_attr"} 按 field + value=ci_attr 兼容读取。
    """
    if not mapping:
        return [dict(name=DEFAULT_VAR_NAME, value=unique_value)]
    vars_ = []
    for vm in mapping.get("var_mapping") or []:
        name = vm.get("grafana_var")
        value_ref = vm.get("value", vm.get("ci_attr"))
        if not name:
            continue
        if (vm.get("map_type") or "field") == "fixed":
            if value_ref is None or value_ref == "":
                continue
            vars_.append(dict(name=name, value=value_ref))
        else:
            value = ci.get(value_ref or "")
            if value is None or value == "" or value == []:
                continue
            vars_.append(dict(name=name, value=value))
    return vars_
```

- [ ] **Step 4: 跑测试确认通过**

Run: `cd cmdb-api-fastapi && .venv/bin/python -m pytest tests/ -q`
Expected: 19 passed（18 - 2 替换 + 1 净增）

- [ ] **Step 5: Commit**

```bash
git add cmdb-api-fastapi/api/lib/common_setting/grafana_client.py cmdb-api-fastapi/tests/test_grafana_client.py
git commit -m "feat(grafana): variables with description, fixed/field var mapping, mapping enable filter"
```

---

### Task 2: 后端 CRUD + variables 端点结构

**Files:**
- Modify: `cmdb-api-fastapi/api/lib/common_setting/grafana.py`
- 说明：variables 视图端点无需改动（直接透传 `get_dashboard_variables` 的新返回）

**Interfaces:**
- Consumes: Task 1 的新 `get_dashboard_variables`。
- Produces: `_valid_var_mapping` 新校验（含源唯一）；映射 CRUD 接受/返回 `enable`。

- [ ] **Step 1: `_valid_var_mapping` 整体替换**

`cmdb-api-fastapi/api/lib/common_setting/grafana.py` 中替换为：

```python
    @staticmethod
    def _valid_var_mapping(var_mapping):
        var_mapping = var_mapping or []
        if not isinstance(var_mapping, list):
            abort(400, ErrFormat.value_is_required)
        result = []
        seen = set()
        for vm in var_mapping:
            if not isinstance(vm, dict):
                abort(400, ErrFormat.value_is_required)
            grafana_var = str(vm.get("grafana_var") or "").strip()
            map_type = str(vm.get("map_type") or "field").strip()
            value = vm.get("value", vm.get("ci_attr"))
            value = str(value or "").strip()
            remark = str(vm.get("remark") or "")
            if not grafana_var or grafana_var in seen:
                abort(400, ErrFormat.value_is_required)
            if map_type not in ("field", "fixed"):
                abort(400, ErrFormat.value_is_required)
            if not value:
                abort(400, ErrFormat.value_is_required)
            seen.add(grafana_var)
            result.append({"grafana_var": grafana_var, "map_type": map_type,
                           "value": value, "remark": remark})
        return result
```

- [ ] **Step 2: 映射 enable**

1. `create_mapping` 的 `mapping = dict(...)` 增加一行：`enable=self._to_enable(data.get("enable", 1)),`
2. `update_mapping` 在 `var_mapping` 块后增加：

```python
        if "enable" in data:
            mapping["enable"] = self._to_enable(data["enable"])
```

3. `list_mappings` 改为：

```python
    def list_mappings(self):
        result = []
        for m in self.get_config()["mappings"]:
            m = dict(m)
            m["enable"] = self._to_enable(m.get("enable", 1))
            result.append(m)
        return result
```

- [ ] **Step 3: 验证导入 + 回归测试**

Run: `cd cmdb-api-fastapi && SECRET_KEY=test-secret-key .venv/bin/python -c "from api.lib.common_setting.grafana import GrafanaConfigCRUD; print('ok')" && .venv/bin/python -m pytest tests/ -q 2>&1 | tail -1`
Expected: `ok`，19 passed

- [ ] **Step 4: Commit**

```bash
git add cmdb-api-fastapi/api/lib/common_setting/grafana.py
git commit -m "feat(grafana): var mapping schema with map_type and duplicate check, mapping enable"
```

---

### Task 3: 前端映射弹窗变量表格 + 启用 + i18n

**Files:**
- Modify: `cmdb-ui/src/views/setting/grafana/index.vue`
- Modify: `cmdb-ui/src/views/setting/lang/zh.js`、`en.js`

**Interfaces:**
- Consumes: variables 端点现在返回 `[{name, description}]`；映射记录含 `enable`；var_mapping 新结构。

- [ ] **Step 1: i18n**

`cs.grafana` 块（zh.js）新增：

```js
    source: '源',
    mapType: '映射类型',
    mapTypeField: '字段',
    mapTypeFixed: '固定值',
    target: '目标',
    remark: '说明',
    duplicateSource: '变量映射的源不能重复',
```

en.js：`source: 'Source'`, `mapType: 'Mapping Type'`, `mapTypeField: 'Field'`, `mapTypeFixed: 'Fixed Value'`, `target: 'Target'`, `remark: 'Remark'`, `duplicateSource: 'Duplicate source in variable mapping'`。

- [ ] **Step 2: 变量映射改为 a-table**

弹窗中 `var_mapping` 表单项内容替换为：

```html
        <a-form-model-item :label="$t('cs.grafana.varMapping')">
          <a-table
            :columns="varMappingColumns"
            :data-source="mappingForm.var_mapping"
            :pagination="false"
            :scroll="{ y: 240 }"
            rowKey="__idx"
            size="small"
          >
            <template slot="grafana_var" slot-scope="text, record">
              <a-auto-complete
                v-model="record.grafana_var"
                :placeholder="$t('cs.grafana.grafanaVar')"
                :filter-option="filterVariableOption"
                @change="(v) => handleVarChange(record, v)"
              >
                <template slot="dataSource">
                  <a-select-option
                    v-for="opt in variableOptions"
                    :key="opt.name"
                    :value="opt.name"
                    :disabled="isVarSelected(opt.name, record)"
                  >
                    {{ opt.name }}
                  </a-select-option>
                </template>
              </a-auto-complete>
            </template>
            <template slot="map_type" slot-scope="text, record">
              <a-select v-model="record.map_type" @change="() => { record.value = undefined }">
                <a-select-option value="field">{{ $t('cs.grafana.mapTypeField') }}</a-select-option>
                <a-select-option value="fixed">{{ $t('cs.grafana.mapTypeFixed') }}</a-select-option>
              </a-select>
            </template>
            <template slot="value" slot-scope="text, record">
              <a-select
                v-if="record.map_type !== 'fixed'"
                v-model="record.value"
                show-search
                option-filter-prop="children"
                :placeholder="$t('cs.grafana.ciAttr')"
              >
                <a-select-option v-for="a in ciAttrOptions" :key="a.name" :value="a.name">
                  {{ a.alias ? `${a.alias}(${a.name})` : a.name }}
                </a-select-option>
              </a-select>
              <a-input v-else v-model="record.value" />
            </template>
            <template slot="remark" slot-scope="text, record">
              <a-input v-model="record.remark" />
            </template>
            <template slot="var_action" slot-scope="text, record">
              <a-icon type="minus-circle" :style="{ color: '#f5222d', cursor: 'pointer' }" @click="removeVarMapping(record)" />
            </template>
          </a-table>
          <a-button type="dashed" size="small" icon="plus" :style="{ marginTop: '8px' }" @click="addVarMapping">
            {{ $t('cs.grafana.addVarMapping') }}
          </a-button>
        </a-form-model-item>
```

script 改动：

1. data 中 `variableOptions: []`（元素现为 `{name, description}`），新增：

```js
      varMappingColumns: [
        { title: this.$t('cs.grafana.source'), scopedSlots: { customRender: 'grafana_var' }, width: '24%' },
        { title: this.$t('cs.grafana.mapType'), scopedSlots: { customRender: 'map_type' }, width: '16%' },
        { title: this.$t('cs.grafana.target'), scopedSlots: { customRender: 'value' }, width: '26%' },
        { title: this.$t('cs.grafana.remark'), scopedSlots: { customRender: 'remark' } },
        { title: '', scopedSlots: { customRender: 'var_action' }, width: 40 },
      ],
```

2. `addVarMapping` 替换为：

```js
    addVarMapping() {
      this.mappingForm.var_mapping.push({ __idx: `new_${Date.now()}_${Math.random()}`, grafana_var: undefined, map_type: 'field', value: undefined, remark: '' })
    },
    removeVarMapping(record) {
      this.mappingForm.var_mapping = this.mappingForm.var_mapping.filter((i) => i !== record)
    },
```

3. `handleVarChange` 替换为（同名 CI 属性默认 + 说明自动带出）：

```js
    handleVarChange(record, value) {
      record.grafana_var = value
      if (!record.value && record.map_type !== 'fixed' && this.ciAttrOptions.some((a) => a.name === value)) {
        record.value = value
      }
      if (!record.remark) {
        const opt = this.variableOptions.find((o) => o.name === value)
        if (opt && opt.description) {
          record.remark = opt.description
        }
      }
    },
```

4. 新增：

```js
    isVarSelected(name, currentRecord) {
      return this.mappingForm.var_mapping.some((i) => i !== currentRecord && i.grafana_var === name)
    },
    filterVariableOption(input, option) {
      return (option.key || '').toLowerCase().includes(input.toLowerCase())
    },
```

5. `openMappingModal` 编辑分支的 var_mapping 映射改为（补 __idx 与新字段，兼容旧 ci_attr 行）：

```js
            var_mapping: (record.var_mapping || []).map((vm, idx) => ({
              __idx: `edit_${idx}`,
              grafana_var: vm.grafana_var,
              map_type: vm.map_type || 'field',
              value: vm.value !== undefined ? vm.value : vm.ci_attr,
              remark: vm.remark || '',
            })),
```

6. `handleSaveMapping` 的完整性校验替换为：

```js
        const rows = this.mappingForm.var_mapping
        const incomplete = rows.some((vm) => !vm.grafana_var || !vm.value)
        if (incomplete) {
          this.$message.error(this.$t('cs.grafana.varMappingIncomplete'))
          return
        }
        const names = rows.map((vm) => vm.grafana_var)
        if (new Set(names).size !== names.length) {
          this.$message.error(this.$t('cs.grafana.duplicateSource'))
          return
        }
```

且提交前剥离 `__idx`：`data.var_mapping = data.var_mapping.map(({ __idx, ...vm }) => vm)`（在 `const { id, ...data } = this.mappingForm` 之后处理）。

7. `loadVariables` 不变（`res.variables` 现在是对象数组，直接赋给 `variableOptions`）。

8. 删除旧的 `.var-mapping-row` 样式块（不再需要）。

- [ ] **Step 3: 映射启用（列表列 + 表单开关 + 摘要列更新）**

1. 映射表格启用 slot（放在 action 模板前）：

```html
        <template slot="enable" slot-scope="text, record">
          <a-switch :checked="record.enable !== 0" @change="(checked) => handleToggleMappingEnable(record, checked)" />
        </template>
```

`mappingColumns` 在 var_mapping 列后、action 列前插入：

```js
        { title: this.$t('cs.grafana.enable'), scopedSlots: { customRender: 'enable' }, width: 80 },
```

methods 增加：

```js
    async handleToggleMappingEnable(record, checked) {
      await putGrafanaMapping(record.id, { enable: checked ? 1 : 0 })
      this.$set(record, 'enable', checked ? 1 : 0)
      this.$message.success(this.$t('saveSuccess'))
    },
```

2. 映射表单：dashboard_title 表单项后增加启用开关（同连接表单的写法，绑定 `mappingForm.enable`）；`mappingForm` 初始值与 openMappingModal 两处对象增加 `enable`（新建 `1`，编辑 `record.enable === undefined ? 1 : record.enable`）。
3. var_mapping 摘要 slot 改为区分 fixed/field：

```html
        <template slot="var_mapping" slot-scope="text, record">
          {{ (record.var_mapping || []).map((vm) => `${vm.grafana_var}${vm.map_type === 'fixed' ? '=' : '←'}${vm.value !== undefined ? vm.value : vm.ci_attr}`).join(', ') || '-' }}
        </template>
```

- [ ] **Step 4: lint + 构建**

Run: `cd cmdb-ui && npx eslint src/views/setting/grafana/index.vue src/views/setting/lang/zh.js src/views/setting/lang/en.js && npx vue-cli-service build --mode development --no-clean 2>&1 | tail -2`
Expected: 无 error，Build complete

- [ ] **Step 5: Commit**

```bash
git add cmdb-ui/src/views/setting/grafana/index.vue cmdb-ui/src/views/setting/lang/zh.js cmdb-ui/src/views/setting/lang/en.js
git commit -m "feat(grafana): var mapping table with map_type and mapping enable switch"
```

---

### Task 4: E2E 验证

**Files:** 无代码改动（验证任务；如发现问题回到对应任务修复）

- [ ] **Step 1: E2E（真实 Grafana，后端自动重载）**

后端 127.0.0.1:5000，真实 Grafana 172.30.6.231:3000（连接 id=1），admin/123456 登录。

1. `GET /api/common-setting/v1/grafana/connections/1/dashboards/rYdddlPWo/variables` → 元素为 `{"name": ..., "description": ...}`，无 datasource。
2. 创建映射（bu 类型 id=1，dashboard_name=rYdddlPWo，var_mapping 两行：`{"grafana_var": "name", "map_type": "field", "value": "bu_name"}`、`{"grafana_var": "maintype", "map_type": "fixed", "value": "linux"}`）；创建 CI `bu_name=e2e-table`；resolve → `vars == [{"name": "name", "value": "e2e-table"}, {"name": "maintype", "value": "linux"}]`。
3. 重复源校验：`POST /mappings` 带两行相同 grafana_var → 400。
4. 停用映射（`PUT /mappings/{id}` `{data:{enable:0}}`）→ resolve `result == null`（无其他映射/实例兜底命中时）；恢复 enable=1。
5. 清理测试映射与 CI；回归 `pytest tests/ -q` → 19 passed。

- [ ] **Step 2: 提交（仅当有修复产生时）**

无修复则无提交。

---

## Self-Review 结论

- Spec 覆盖：变量表格+滚动（Task 3 Step 2）、map_type fixed/field（Task 1/2/3）、源唯一（Task 2 后端 + Task 3 前端禁用与校验）、说明自动带出（Task 1 description + Task 3 handleVarChange）、映射启用（Task 1 过滤 / Task 2 CRUD / Task 3 UI）、旧行兼容（Task 1 build_vars + Task 3 openMappingModal 回显）、E2E（Task 4）—— 无遗漏。
- 类型一致性：`{name, description}` 在 Task 1 生产与 Task 3 消费一致；`__idx` 仅前端行 key，提交前剥离；enable int 0/1 全链一致。
- 已知取舍：a-auto-complete 的 dataSource slot 写法在 antdv 1.x 中与 a-select-option 兼容（项目内无先例，E2E/人工点击验证兜底）；编辑回显把旧 ci_attr 行映射为 field 类型。
