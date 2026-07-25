# Flask → FastAPI 视图移植规范（PORTING）

> **状态：迁移已完成。** 全部 33 个视图文件（account / acl×8 / common_setting×8 /
> cmdb×13，含 dcim×6、ipam×4）均已移植到 `api/views/`，`views_src_tmp/` 与
> `port_imports.py` 已删除。本文档保留作为移植规则的存档参考。
> CLI 命令通过 `python cli.py <command>` 调用（替代 Flask 侧的 `flask <command>`）。

目标：把 `api/views_src_tmp/**` 下的 Flask-RESTful Resource 类逐文件移植为
`api/views/**` 下的 FastAPI 模块。**只改框架交互，不改业务逻辑**，URL 与响应
格式必须与原来完全一致。

## 目录映射

- `views_src_tmp/account.py` → `views/account.py`（已完成，作为标准样例，先读它）
- `views_src_tmp/cmdb/**` → `views/cmdb/**`（含 ipam、dcim 子目录）
- `views_src_tmp/acl/**` → `views/acl/**`
- `views_src_tmp/common_setting/**` → `views/common_setting/**`

## 转换规则

1. 每个模块定义：
   ```python
   from fastapi import APIRouter
   from fastapi import Depends
   from api.lib.perm.auth import authenticate
   router = APIRouter(dependencies=[Depends(authenticate)])
   ```
2. 每个 Resource 类的每个 HTTP 方法 → 一个模块级函数。函数名用
   `类名_snake_case + '_' + 方法名`，如 `CITypeView.get` → `ci_type_view_get`。
   保留原方法上的全部装饰器（`@args_required`、`@has_perm_from_args`、
   `@auth_abandoned` 等），顺序不变。
3. `url_prefix` 元组中的每条路径 → 叠加的路由装饰器：
   - `"/ci_types/<int:type_id>"` → `@router.get("/ci_types/{type_id}")`
   - `"/ci_types/<string:type_name>"` → `@router.get("/ci_types/{type_name}")`
   - 路径参数写入函数签名并带类型与默认值（与原方法签名一致），如
     `def ci_type_view_get(type_id: int = None, type_name: str = None):`
   - 无 `url_prefix` 属性的类 → 路由路径为 `""`。
4. 除路径参数外，其余参数一律继续从 `request.values` 读取
   （`from api.core.context import request`，中间件已合并 query/form/JSON）。
5. `self.jsonify(...)` → 直接 `return dict(...)`；`return self.jsonify(a=1)` → `return dict(a=1)`。
6. `self.send_file(...)` → `from api.core.responses import send_file` 后直接 return。
7. `abort(...)` 来自 `api.core.errors`，会抛异常，`return abort(...)` 写法可保留。
8. `request.files` 中的文件对象已是同步封装（`.read()`/`.save()`/`.filename`），直接用。
9. 不要 import flask / flask_restful / flask_login / flask_babel / werkzeug；
   这些在源文件中已替换为 `api.core.*` 等价物，沿用即可。
10. 保留原有注释与业务逻辑；只做上述机械转换。

## 验证（必须执行）

在 `cmdb-api-fastapi/` 目录下：

```bash
SECRET_KEY=test-secret MYSQL_HOST=127.0.0.1 MYSQL_PORT=23306 \
CACHE_REDIS_HOST=127.0.0.1 CACHE_REDIS_PORT=6379 \
.venv/bin/python -c "
from fastapi.testclient import TestClient
from main import app
c = TestClient(app)
r = c.post('/api/login', json={'username': 'demo', 'password': '123456'})
token = r.json()['token']
h = {'Access-Token': token}
# 然后对你移植的每个路由至少跑一个 GET 冒烟，例如：
print(c.get('/api/v1/acl/users/info', headers=h).status_code)
"
```

- 模块必须能 import；整个 `main` 必须能启动。
- 至少对每个路由的一个方法做冒烟（登录后带 `Access-Token` 头），
  未认证请求应返回 401 且 body 为 `{"message": ...}`。
- 若需要登录前已种入 session，可直接用 TestClient 的 cookie 保持。
