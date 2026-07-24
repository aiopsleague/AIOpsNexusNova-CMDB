# 维易 CMDB 架构图

## 部署视图（Docker Compose）

```mermaid
flowchart LR
    user["用户浏览器<br>:8000"]

    subgraph network["cmdb_network (docker bridge)"]
        subgraph ui["cmdb-ui 容器"]
            nginx["Nginx :80<br>托管 Vue SPA 静态资源<br>/api 反向代理"]
        end

        subgraph api["cmdb-api 容器"]
            gunicorn["Gunicorn ×4 workers<br>Flask autoapp:app :5000"]
            celery1["Celery Worker<br>队列 one_cmdb_async"]
            celery2["Celery Worker<br>队列 acl_async"]
            celery3["Celery Worker + Beat<br>队列 beat_tasks"]
            trigger["flask cmdb-trigger<br>属性触发器守护进程"]
        end

        subgraph db["cmdb-db 容器"]
            mysql[("MySQL :3306<br>宿主映射 23306<br>volume: db-data")]
        end

        subgraph cache["cmdb-cache 容器"]
            redis[("Redis :6379<br>volume: cache-data")]
        end
    end

    user -->|HTTP :8000| nginx
    nginx -->|/api 反代 :5000| gunicorn
    gunicorn -->|SQLAlchemy| mysql
    gunicorn -->|缓存 / 会话| redis
    celery1 --> mysql
    celery2 --> mysql
    celery3 --> mysql
    celery1 & celery2 & celery3 -->|Broker / 结果| redis
    trigger --> mysql
    trigger --> redis
```

## 后端内部模块视图（cmdb-api）

```mermaid
flowchart TB
    client["前端 / Open API 调用方"]

    subgraph views["api/views 视图层"]
        v_cmdb["views/cmdb<br>CI · 模型CIType · 属性 · 关系<br>拓扑 · 历史 · 自定义仪表盘<br>自动发现 · IPAM · DCIM"]
        v_acl["views/acl<br>用户 · 角色 · 资源<br>权限 · 审计 · 触发器"]
        v_cs["views/common_setting<br>公司/部门/员工 · 通知<br>文件管理 · 认证配置"]
    end

    subgraph lib["api/lib 业务逻辑层"]
        l_cmdb["lib/cmdb<br>CI/模型/属性/关系<br>IPAM · DCIM · 拓扑"]
        l_perm["lib/perm<br>ACL 权限控制<br>CAS / OAuth2 认证"]
        l_search["lib/cmdb/search<br>CI 搜索（DB 后端 / ES 后端）"]
        l_secrets["lib/secrets<br>inner / Vault 密钥管理"]
        l_notify["notify · mail · webhook"]
    end

    subgraph ext["api/extensions 扩展"]
        e_db["db<br>Flask-SQLAlchemy"]
        e_cache["cache / rd<br>Flask-Caching / Redis"]
        e_celery["celery<br>异步任务"]
    end

    subgraph store["数据与外部依赖"]
        mysql2[("MySQL")]
        redis2[("Redis<br>缓存 + Celery Broker")]
        es[("Elasticsearch<br>可选：CI 搜索加速")]
        vault[("Vault<br>可选：密钥托管")]
        third["邮件 / IM 通知渠道<br>第三方系统 Webhook"]
    end

    client --> views
    views --> lib
    v_cmdb --> l_cmdb
    v_cmdb --> l_search
    v_acl --> l_perm
    lib --> ext
    l_search --> es
    l_secrets --> vault
    l_notify --> third
    e_db --> mysql2
    e_cache --> redis2
    e_celery --> redis2
```

## 说明

- **cmdb-ui**：Nginx 托管 Vue.js + Ant Design Vue 单页应用，`/api` 请求反向代理到后端（见 `docs/nginx.cmdb.conf.example`）。
- **cmdb-api**：单容器内运行 Gunicorn Web 进程、3 组 Celery 队列（`one_cmdb_async`、`acl_async`、`beat_tasks` 含定时调度）和属性触发器守护进程（见 `docker-compose.yml` 启动命令）。
- **cmdb-db**：MySQL 存储全部模型与实例数据，首次启动由 `docs/cmdb.sql` 初始化。
- **cmdb-cache**：Redis 同时承担应用缓存与 Celery 消息队列。
- **可选依赖**：Elasticsearch（`settings.py` 中配置后用于 CI 全文搜索）、Vault（密钥管理）、邮件/Webhook 通知。
- **自动发现**：内置模板（如 `api/lib/cmdb/auto_discovery/templates/aws_ec2.json`），支持主机、网络设备、数据库、中间件、公有云资源采集入库。
