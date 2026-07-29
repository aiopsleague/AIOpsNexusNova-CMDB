# AIOpsNexusNova-CMDB — Codebase Guide

> Auto-generated from deep codebase analysis. Last updated: 2026-07-29.

## Architecture Overview

```
nginx (:8000) → Vue SPA (static files)
              → /api → FastAPI (:5000, internal)
FastAPI        → MySQL 8.0 (:3306, internal)
              → Redis 6.2 (:6379, internal)
Celery Worker + Beat → Redis (broker/result)
```

- **Backend**: Python 3.12+ / FastAPI / SQLAlchemy 1.4 / Celery 5.3 / MySQL 8.0 / Redis 6.2
- **Frontend**: Vue 2.6.11 / Ant Design Vue 1.6.x / Vue Router 3 / Vuex 3 / Webpack (Vue CLI 4)
- **Infrastructure**: Docker Compose (6 services), Nginx reverse proxy, multi-arch builds

---

## Project Structure

```
cmdb-api/                    # Backend (FastAPI)
  main.py                    # App factory (create_app) — uvicorn entry point
  settings.py                # All config via environs (env vars)
  cli.py                     # Click CLI (migrations, cache init, seeding)
  celery_worker.py           # Celery init + beat schedules
  api/
    extensions.py            # Singletons: db, celery, cache, rd, es, inner_secrets
    core/                    # Framework: context (contextvars), database, errors, json encoder, i18n
    models/                  # SQLAlchemy ORM models (cmdb.py, acl.py, common_setting.py)
    views/                   # Route handlers (thin — delegate to lib)
      entry.py               # Root router aggregator
      account.py             # /api/login, /api/logout
      acl/                   # /api/v1/acl/*
      cmdb/                  # /api/v0.1/* (ci, ci_type, attribute, relation, topology, dcim, ipam, ...)
      common_setting/        # /api/common-setting/v1/*
    lib/                     # Business logic (the real service layer)
      cmdb/                  # CI, CI Type, Attributes, Relations, Search, DCIM, IPAM, Auto-discovery
      perm/                  # Auth (JWT, session, key, ACL token) + ACL permission system
      common_setting/        # Departments, employees, company info, Grafana, notifications
      secrets/               # Secret encryption (inner/Vault backends)
    commands/                # Click CLI subcommands
    tasks/                   # Celery async tasks
    translations/            # i18n (.po/.mo for zh)
  migrations/                # Alembic
  tests/                     # pytest

cmdb-ui/                     # Frontend (Vue 2 SPA)
  src/
    main.js                  # Vue bootstrap
    App.vue                  # Root component with antd locale provider
    guard.js                 # Vue Router navigation guards (auth + ACL)
    api/                     # Axios API client functions per domain
    router/                  # Vue Router config
    store/                   # Vuex store (global modules: app, user, routes, notice, company)
    config/                  # App settings (primaryColor, navTheme, layout, etc.)
    core/                    # Bootstrap, plugin registration, EventBus, directives
    layouts/                 # BasicLayout, BlankLayout, PageView, UserLayout
    components/              # 30+ shared components (OpsTable, CustomDrawer, SplitPane, etc.)
    views/                   # Top-level pages (user, exception, noticeCenter, setting)
    modules/                 # Feature modules (acl/, cmdb/) — each with own api/, router/, store/, views/
    lang/                    # i18n (zh.js, en.js)
    utils/                   # Utilities (request.js, axios.js, filter.js, mixin.js, util.js)
    style/                   # Global Less styles
```

---

## Backend Conventions

### Python & Framework
- **Python**: 3.12+ (requires-python >= 3.12)
- **Package manager**: `uv` (with aliyun mirror for PyPI)
- **Linter**: `ruff` (run via `make lint` or `cd cmdb-api && uv run ruff check .`)
- **Formatter**: ruff (no separate formatter configured)
- **Encoding**: `# -*- coding:utf-8 -*-` at top of every file
- **Imports**: stdlib → third-party → project (standard grouping, no blank lines between groups in practice)

### Application Architecture (3-Layer)
```
views/   → Route handlers (thin): parse request, call lib, return dict
lib/     → Business logic (thick): all domain logic lives here
models/  → SQLAlchemy ORM models: table definitions + CRUD mixins
```

**CRITICAL RULE**: Views never contain business logic. They only:
1. Extract params from `request.values`
2. Call a Manager class from `lib/`
3. Return a dict (auto-serialized to JSON via `CmdbJSONResponse`)

### Route Registration
- Routers are auto-discovered via `pkgutil.walk_packages` in `api/views/entry.py`
- Each view module exports a `router = APIRouter(...)` — it gets mounted automatically
- Route prefix mapping:
  - `api/views/cmdb/*` → `/api/v0.1`
  - `api/views/acl/*` → `/api/v1/acl`
  - `api/views/common_setting/*` → `/api/common-setting/v1`
  - `api/views/account.py` → `/api`

### Request Context (Flask Compatibility Layer)
The project migrated from Flask to FastAPI. To keep legacy code working, it emulates Flask's request context via `contextvars`:
- **`from api.core.context import request`** — emulates `flask.request` (`.values`, `.args`, `.headers`, `.method`, `.path`, etc.)
- **`from api.core.context import session`** — emulates `flask.session`
- **`from api.core.context import current_app`** — emulates `flask.current_app` (`.config`, `.logger`)
- **`from api.core.context import current_user`** — emulates `flask_login.current_user`
- **`from api.core.context import login_user, logout_user`** — auth state setters

**ALWAYS use these proxies** — never access the Starlette request object directly in view/lib code.

### Database
- **ORM**: SQLAlchemy 1.4.49 with `pymysql` driver
- **Session**: `scoped_session` keyed on request context (not thread-local)
- **Models**: Declarative base from `api.extensions.db.Model` (aliased to `Base`)
- **Model base classes** (in `api/lib/database.py`):
  - `Model` — SoftDeleteMixin + TimestampMixin + CRUDMixin + SurrogatePK (most CMDB models)
  - `Model2` — TimestampMixin2 + CRUDMixin + SurrogatePK (no soft delete)
- **CRUD operations**: Use mixin methods — `.create()`, `.update()`, `.save()`, `.delete()`, `.soft_delete()`, `.get_by_id()`, `.get_by()`
- **Query access**: `Model.query` (via `_QueryProperty` descriptor)
- **Custom query class**: `CmdbQuery` with `.paginate()`, `.get_or_404()`, `.first_or_404()`
- **Connection pool**: `pool_size=20`, `max_overflow=40`, `pool_recycle=300`
- **Migrations**: Alembic in `migrations/` (run via `python cli.py db-setup`)

### API Design (REST-like)
- **HTTP methods**: GET (read), POST (create), PUT (update), DELETE (delete)
- **URL params**: Path parameters for resource IDs (e.g., `/ci/{ci_id:int}`)
- **Query/body params**: All accessed via `request.values` (merged JSON body + query args)
- **Response format**: Always `dict` from views → JSON via `CmdbJSONResponse`
- **Error format**: `{"message": "error description"}` with appropriate HTTP status
- **Pagination**: `page` + `count` query params, handled by `get_page()` / `get_page_size()` utils
- **Multi-method routes**: Same function handles multiple methods (e.g., `@router.get("/ci")` + `@router.get("/ci/{ci_id:int}")` on same function)

### Authentication & Authorization
- **Primary**: `authenticate` FastAPI dependency (injected via `dependencies=[Depends(authenticate)]` on the router)
- **Auth chain** (tried in order): Session → API Key (_key/_secret) → JWT Bearer token → IP whitelist → ACL token
- **Permission decorators**:
  - `@args_required("param1", "param2")` — validate required request params
  - `@has_perm_from_args("arg", ResourceType, PermEnum, resolver)` — resource-level ACL check
  - `@auth_abandoned` — skip auth (public endpoint)
  - `@auth_with_app_token` — require app-level token
- **ACL System**: Role-based, with `ACLManager`, `UserCache`, `AppCache`, `RoleCache`
- **SSO Support**: CAS, OAuth2, OIDC (mounted in `register_sso()`)

### Error Handling
- **`abort(code, message)`** — raise `AbortException` (replaces `flask.abort`)
- **HTTPError subclasses**: `BadRequest(400)`, `Unauthorized(401)`, `Forbidden(403)`, `NotFound(404)`
- **Exception handlers** registered globally in `api/core/errors.py`
- **Error responses**: Always `CmdbJSONResponse({"message": str(error)}, status_code=code)`
- **Unhandled exceptions**: Caught by catch-all handler → 500 with traceback logged

### Logging
- **Logger**: `logger = logging.getLogger("cmdb")` 
- **Output**: stdout (debug mode) + rotating file (`./logs/app.log`, 1GB max, 7 backups)
- **Format**: `"%(asctime)s %(levelname)s %(pathname)s %(lineno)d - %(message)s"`
- **Log level**: `DEBUG` (configurable via `LOG_LEVEL` setting)

### Async Tasks (Celery)
- **Worker**: `celery -A celery_worker.celery worker -Q one_cmdb_async,acl_async`
- **Beat**: Celery Beat for scheduled tasks (CI cache refresh, etc.)
- **Task modules**: `api/tasks/cmdb.py`, `api/tasks/acl.py`, `api/tasks/common_setting.py`
- **Celery config**: broker=Redis, result_backend=Redis, `celery-once` for deduplication
- **Task context**: Uses `current_app.test_request_context().push()` to emulate request context

### i18n
- **Framework**: Python-Babel
- **Supported locales**: zh (Chinese), en (English)
- **Usage**: `from api.core.i18n import lazy_gettext as _l`
- **Error messages**: All in `api/lib/resp_format.py` and `api/lib/*/resp_format.py` using `_l()`
- **Translations**: Compiled `.mo` files in `api/translations/zh/LC_MESSAGES/`

### Testing
- **Framework**: pytest with httpx for async HTTP testing
- **Fixtures**: `tests/conftest.py` (currently minimal — adds project root to sys.path)
- **Factories**: factory-boy listed in dev deps
- **Run**: `cd cmdb-api && uv run pytest`

### Naming Conventions
- **Files**: `snake_case` (e.g., `ci_type.py`, `auto_discovery.py`)
- **Classes**: `PascalCase` (e.g., `CIManager`, `CITypeCache`, `ACLManager`)
- **Functions/methods**: `snake_case` (e.g., `get_cis_by_type`, `handle_arg_list`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `REDIS_PREFIX_CI`, `CMDB_QUEUE`)
- **View functions**: `snake_case` with `_view_get`/`_view_post`/`_view_put`/`_view_delete` suffix
- **Private members**: `_leading_underscore` (e.g., `_wrap_ci_dict`, `_auth_with_session`)
- **Module-level routers**: Always named `router`

---

## Frontend Conventions

### Framework & Build
- **Vue**: 2.6.11 (Options API — no Composition API usage in existing code)
- **Build tool**: Vue CLI 4 (`vue-cli-service serve` / `build`)
- **Package manager**: Yarn (>=1.22)
- **Node**: >=16.0.0 <17.0.0
- **Linter**: ESLint 5 with `plugin:vue/strongly-recommended` + `@vue/standard`
- **Code style**: Single quotes, no semicolons, 2-space indent (implied by standard)

### Component Libraries
- **Primary**: Ant Design Vue 1.6.5 (`ant-design-vue`) — forms, tables, modals, menus, layouts
- **Secondary**: Element UI 2.15.10 — specific components (date pickers, time pickers, autocomplete, etc.)
- **Data tables**: Vxe-table 3.7.10 (editable, exportable tables with XLSX export plugin)
- **Charts**: ECharts 5 + viser-vue wrapper
- **Code editor**: Monaco Editor 0.28 + monaco-vim
- **Tree select**: @riophae/vue-treeselect
- **Rich text**: @wangeditor/editor 5.x
- **Topology**: relation-graph + butterfly-dag
- **Drag & drop**: vuedraggable + sortablejs
- **Clipboard**: vue-clipboard2
- **Icons**: Ant Design Icons + custom iconfont (ops-icon component)

### Styling
- **Preprocessor**: Less (with `javascriptEnabled: true`)
- **Theme**: Ant Design custom theme — primary color `#2f54eb`
- **Global styles**: `src/style/` (index.less, global.less, static.less)
- **Style resources loader**: Auto-imports `static.less` into every component
- **Scoped styles**: Use `<style scoped lang="less">` in components
- **CSS modules**: Not used — relies on scoped styles and global Less variables

### Project Structure Pattern
```
src/
  api/          # API client functions (thin wrappers around axios calls)
  router/       # Route definitions
  store/        # Vuex store modules
  views/        # Page-level components (top-level only)
  modules/      # Feature modules (each is a mini-app)
    <module>/
      index.js      # Exports { name, route, store }
      api/          # Module-specific API clients
      router/       # Module routes (dynamically registered)
      store/        # Module Vuex store (dynamically registered)
      views/        # Module page components
      components/   # Module-specific components
      lang/         # Module-specific i18n
      constants/    # Module constants
      utils/        # Module utilities
  components/   # Shared/generic components
  config/       # App settings (theme, layout, colors)
  core/         # Bootstrap, plugin setup, directives
  lang/         # Global i18n
  utils/        # Utilities (request, axios, filters, mixins)
```

### API Calls
- **HTTP client**: Axios 0.18 via `src/utils/request.js`
- **Base URL**: `process.env.VUE_APP_API_BASE_URL` (empty in dev — proxied by Vue CLI to :5000)
- **Request interceptor**: Attaches `Access-Token` header + `Accept-Language` header
- **Response interceptor**: Unwraps `response.data` automatically
- **Error handling**: 5xx → message.error, 412 → countdown notification, 401 → redirect to logout
- **API module pattern**:
  ```js
  // src/api/cmdb.js
  import { axios } from '@/utils/request'
  export function searchCI(params) {
    return axios({ url: '/v0.1/ci/s', method: 'GET', params })
  }
  ```
- **isShowMessage**: Pass `false` to suppress automatic error messages

### State Management (Vuex)
- **Store structure**: `store/global/` has modules: `app`, `user`, `routes`, `notice`, `company`
- **Module registration**: Feature modules register their stores dynamically in `store/index.js`
- **Pattern**: `mapState`, `mapActions`, `mapMutations` in components
- **Persistence**: `Vue.ls` (vue-ls) for localStorage (ACCESS_TOKEN, theme, layout settings)
- **Getters**: Centralized in `store/global/getters.js`

### Routing
- **Mode**: HTML5 history mode
- **Base**: `process.env.BASE_URL`
- **Route guards** (`src/guard.js`):
  - White-listed paths: `/user/login`, `/user/logout`, `/user/register`, SSO paths
  - Auth check: `Vue.ls.get(ACCESS_TOKEN)` + store roles
  - Dynamic route generation: `store.dispatch('GenerateRoutes', { roles })` → `router.addRoutes()`
  - NProgress bar on navigation
  - Document title updates from route meta

### i18n
- **Library**: Vue I18n 8.28.2
- **Locales**: `zh` (default), `en`
- **Global messages**: `src/lang/zh.js`, `src/lang/en.js`
- **Module messages**: Each module can have its own `lang/` directory
- **Table i18n**: Vxe-table uses shared i18n instance
- **Usage in templates**: `{{ $t('key.path') }}`

### Component Patterns
- **Component naming**: PascalCase for imported components, kebab-case in templates
- **Props**: Defined as objects with `type`, `default`, `required`
- **Events**: `this.$emit('event-name', data)` — kebab-case
- **v-model**: Supported via `value` prop + `input` event
- **Slots**: Named slots for composable layouts (e.g., SplitPane's `#one` / `#two`)
- **Mixins**: Used for shared logic (e.g., `AppDeviceEnquire` in `utils/mixin.js`)
- **Custom directives**: `v-action` (permission-based show/hide), `v-highlight`, `v-waves`
- **Event bus**: `this.$bus` (global EventBus on Vue prototype)

### Development Proxy
- Vue CLI dev server proxies `/api` → `http://localhost:5000`
- Sets `X-Real-IP: 127.0.0.1` header (so IP whitelist auth works locally)
- Dev port: `DEV_PORT` env or 8000

### Testing
- **Framework**: Jest with `@vue/test-utils`
- **Config**: `jest.config.js`
- **Run**: `yarn test:unit`

---

## Infrastructure & DevOps

### Local Development
```bash
make deps          # Install all dependencies (uv sync + yarn install)
make api           # Start FastAPI dev server on :5000 (hot reload)
make ui            # Start Vue dev server on :8000 (hot reload)
make worker        # Start Celery worker
make init          # Initialize DB + seed data + cache
make lint          # Run ruff linter on backend
```

### Docker Compose (Production)
```bash
docker compose up -d     # Start all 6 services
docker compose down      # Stop (preserves volumes)
docker compose down -v   # Stop + delete volumes
```

### Docker Images
```bash
make docker-build       # Build API + UI images (multi-arch)
make docker-push        # Build + push to registry
```

### Environment Variables
All configuration via `.env` file (copy from `.env.example`):
- `SECRET_KEY` — Flask/FastAPI secret (required)
- `MYSQL_ROOT_PASSWORD`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- `CACHE_REDIS_HOST`, `CACHE_REDIS_PORT`
- `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- `CMDB_API_IMAGE`, `CMDB_UI_IMAGE` — Docker image tags
- `NGINX_PORT` — external port (default 80)

---

## Key Business Domains

### CMDB (Configuration Management Database)
- **CI (Configuration Item)**: Core entity — any managed resource (server, app, device, etc.)
- **CI Type**: Schema/template defining what attributes a CI has
- **Attribute**: Typed field definition (text, int, float, date, choice, reference, etc.)
- **CI Relation**: Directed relationship between two CIs (parent → child with a relation type)
- **CI Type Relation**: Schema defining allowed relations between CI types
- **DCIM**: Data Center Infrastructure Management (regions, server rooms, racks, IDCs)
- **IPAM**: IP Address Management (subnets, IP addresses)
- **Auto Discovery**: Automated CI discovery via SNMP/HTTP agents

### ACL (Access Control List)
- **Users**: With roles and permissions
- **Roles**: Hierarchical (parent/child roles)
- **Resources**: Protected items with resource types
- **Permissions**: CRUD operations on resources
- **Apps**: Application-level API tokens

### Common Settings
- **Departments**: Organizational hierarchy
- **Employees**: User-to-department mapping
- **Company Info**: Global company configuration
- **Grafana**: Dashboard integration
- **Notifications**: Email/webhook notification config

---

## Migration Notes (Flask → FastAPI)

The backend is actively being migrated from Flask to FastAPI. Key compatibility layers:
1. `api/core/context.py` — Request context emulation (contextvars instead of Flask globals)
2. `api/extensions.py` — `_DBShim` emulates Flask-SQLAlchemy API on top of raw SQLAlchemy
3. `api/core/database.py` — `CmdbQuery` with `.paginate()` matches Flask-SQLAlchemy
4. `api/core/errors.py` — `AbortException` + `abort()` replace `flask.abort`
5. View decorators (`@args_required`, `@has_perm_from_args`) work unchanged
6. Legacy code in `api/lib/` is preserved with minimal changes via the compatibility layer

See `cmdb-api/PORTING.md` for detailed porting rules and directory mapping.
