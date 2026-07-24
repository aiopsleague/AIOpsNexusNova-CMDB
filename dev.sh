#!/usr/bin/env bash
# dev.sh — 本地开发环境一键启停
#
# 依赖（MySQL/Redis）用 docker 在本地跑，后端和前端直接在宿主机跑。
# 后端默认是新版 FastAPI（cmdb-api-fastapi），也支持旧版 Flask（cmdb-api）。
#
# 用法：
#   ./dev.sh start [--flask] [--worker] [--init]   # 启动（默认 fastapi 后端）
#   ./dev.sh stop [--keep-db]                      # 停止（默认连 db 容器一起停）
#   ./dev.sh restart [--flask] [--worker] [--init]
#   ./dev.sh status                                # 查看各服务状态
#   ./dev.sh logs <api|worker|ui>                  # 跟踪某个服务的日志
#
# 选项：
#   --flask      后端用旧版 cmdb-api（Flask），需要先在 cmdb-api 里 pipenv install
#   --worker     同时启动 celery worker + beat（自动发现/定时任务需要，仅 fastapi）
#   --init       启动后端前跑一遍初始化命令（cli.py db-setup 等，首次建库时用）
#   --keep-db    stop 时保留 MySQL/Redis 容器
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT/.dev"
mkdir -p "$RUN_DIR"

BACKEND=fastapi
WITH_WORKER=0
DO_INIT=0
KEEP_DB=0

# 颜色输出
c_green() { printf '\033[32m%s\033[0m\n' "$*"; }
c_red()   { printf '\033[31m%s\033[0m\n' "$*"; }
c_yellow(){ printf '\033[33m%s\033[0m\n' "$*"; }

# 后端/前端共用的本地连接参数（docker 把 3306 映射到 23306，6379 直接暴露）
export TZ=UTC   # 容器/本机若是东八区，JWT iat 会落到未来导致 token 全部失效
export SECRET_KEY="${SECRET_KEY:-dev-secret-key}"
export MYSQL_HOST=127.0.0.1
export MYSQL_PORT=23306
export CACHE_REDIS_HOST=127.0.0.1
export CACHE_REDIS_PORT=6379

API_PORT=5000
UI_PORT=8000

pid_file() { echo "$RUN_DIR/$1.pid"; }
log_file() { echo "$RUN_DIR/$1.log"; }

# 进程识别用命令行模式而不是 pid 文件：uvicorn --reload / celery 会 fork 子
# 进程，pid 文件容易漂移；模式匹配对 stop/status 都可靠。
proc_pattern() {  # $1=name
    case "$1" in
        api)    [[ "$BACKEND" == flask ]] && echo 'flask run' || echo 'uvicorn main:app' ;;
        worker) echo 'celery_worker.celery worker' ;;
        ui)     echo 'vue-cli-service serve' ;;
    esac
}

is_running() { pgrep -f "$(proc_pattern "$1")" >/dev/null 2>&1; }

start_proc() {  # $1=name $2=工作目录 $3...=命令
    local name="$1" dir="$2"; shift 2
    if is_running "$name"; then
        c_yellow "$name 已在运行，跳过"
        return 0
    fi
    nohup bash -c 'cd "$1" && shift && exec "$@"' _ "$dir" "$@" >>"$(log_file "$name")" 2>&1 &
    echo $! >"$(pid_file "$name")"
    c_green "$name 已启动，日志：.dev/$name.log"
}

stop_proc() {  # $1=name
    local name="$1" pattern
    pattern="$(proc_pattern "$1")"
    if ! pgrep -f "$pattern" >/dev/null 2>&1; then
        rm -f "$(pid_file "$name")"
        c_yellow "$name 未在运行"
        return 0
    fi
    pkill -f "$pattern" 2>/dev/null || true
    for _ in $(seq 1 10); do pgrep -f "$pattern" >/dev/null 2>&1 || break; sleep 1; done
    pkill -9 -f "$pattern" 2>/dev/null || true
    rm -f "$(pid_file "$name")"
    c_green "$name 已停止"
}

wait_http() {  # $1=url $2=名字 $3=超时秒
    local url="$1" name="$2" timeout="${3:-60}" i
    for i in $(seq 1 "$timeout"); do
        if curl -sf -o /dev/null "$url" 2>/dev/null; then
            c_green "$name 就绪：$url"
            return 0
        fi
        sleep 1
    done
    c_red "$name 等待超时（$url），请查看 .dev/ 下的日志"
    return 1
}

# ---------- docker 依赖 ----------
db_start() {
    c_yellow "启动 MySQL / Redis 容器..."
    ( cd "$ROOT" && docker compose up -d cmdb-db cmdb-cache )
    c_yellow "等待数据库 healthy（首次导入 cmdb.sql 需要几分钟）..."
    for name in cmdb-db cmdb-cache; do
        for _ in $(seq 1 90); do
            status="$(docker inspect -f '{{.State.Health.Status}}' "$name" 2>/dev/null || echo missing)"
            [[ "$status" == healthy ]] && break
            sleep 2
        done
        if [[ "$status" == healthy ]]; then
            c_green "$name healthy"
        else
            c_red "$name 状态异常：$status"
            return 1
        fi
    done
}

db_stop() {
    c_yellow "停止 MySQL / Redis 容器（数据保留在卷 cmdb_db-data / cmdb_cache-data）..."
    ( cd "$ROOT" && docker compose stop cmdb-db cmdb-cache )
}

# ---------- 后端 ----------
api_start() {
    if [[ "$BACKEND" == fastapi ]]; then
        local dir="$ROOT/cmdb-api-fastapi"
        [[ -x "$dir/.venv/bin/uvicorn" ]] || { c_red "找不到 $dir/.venv，请先创建虚拟环境安装依赖"; return 1; }
        if [[ "$DO_INIT" == 1 ]]; then
            c_yellow "执行初始化命令（cli.py）..."
            ( cd "$dir" && .venv/bin/python cli.py db-setup \
                && .venv/bin/python cli.py common-check-new-columns \
                && .venv/bin/python cli.py cmdb-init-cache \
                && .venv/bin/python cli.py cmdb-init-acl \
                && .venv/bin/python cli.py init-import-user-from-acl \
                && .venv/bin/python cli.py init-department )
        fi
        start_proc api "$dir" .venv/bin/uvicorn main:app --host 0.0.0.0 --port "$API_PORT" --reload
        if [[ "$WITH_WORKER" == 1 ]]; then
            start_proc worker "$dir" .venv/bin/celery -A celery_worker.celery worker --beat -E \
                -Q one_cmdb_async,acl_async,beat_tasks --loglevel=info
        fi
    else
        local dir="$ROOT/cmdb-api"
        if [[ -x "$dir/.venv/bin/flask" ]]; then
            start_proc api "$dir" env FLASK_APP=autoapp.py FLASK_ENV=development \
                .venv/bin/flask run --host 0.0.0.0 --port "$API_PORT"
        elif command -v pipenv >/dev/null && ( cd "$dir" && pipenv --venv ) >/dev/null 2>&1; then
            start_proc api "$dir" env FLASK_APP=autoapp.py FLASK_ENV=development \
                pipenv run flask run --host 0.0.0.0 --port "$API_PORT"
        else
            c_red "旧版 cmdb-api 的依赖环境不存在，请先在 cmdb-api 目录执行 pipenv install"
            return 1
        fi
    fi
    wait_http "http://127.0.0.1:$API_PORT/api/health" "后端($BACKEND)" 60
}

api_stop() {
    stop_proc worker
    stop_proc api
}

# ---------- 前端 ----------
pick_node() {  # 优先 node 16（package.json engines），退化到 node 14（实测可用），同主版本取最新
    local d best=""
    for d in "$HOME"/.nvm/versions/node/v16*/bin "$HOME"/.nvm/versions/node/v14*/bin; do
        [[ -x "$d/node" ]] && best="$d"
    done
    [[ -n "$best" ]] && { echo "$best"; return 0; }
    if command -v node >/dev/null; then dirname "$(command -v node)"; return 0; fi
    return 1
}

ui_start() {
    local dir="$ROOT/cmdb-ui" node_bin
    node_bin="$(pick_node)" || { c_red "找不到可用的 Node.js"; return 1; }
    c_yellow "前端使用 Node：$("$node_bin/node" -v)"
    if [[ ! -d "$dir/node_modules" ]]; then
        c_yellow "首次运行，安装前端依赖（需要几分钟）..."
        ( cd "$dir" && PATH="$node_bin:$PATH" yarn install --ignore-engines --network-timeout 1000000 )
    fi
    # yarn run 会校验 engines（要求 node 16），直接调 vue-cli-service 绕开
    start_proc ui "$dir" env PATH="$node_bin:$PATH" ./node_modules/.bin/vue-cli-service serve
    wait_http "http://127.0.0.1:$UI_PORT/" "前端" 240
}

ui_stop() {
    stop_proc ui
}

# ---------- 子命令 ----------
do_start() {
    db_start
    api_start
    ui_start
    echo
    c_green "全部启动完成："
    echo "  前端  http://127.0.0.1:$UI_PORT  (demo / 123456)"
    echo "  后端  http://127.0.0.1:$API_PORT  ($BACKEND)"
    do_status
}

do_stop() {
    ui_stop
    api_stop
    [[ "$KEEP_DB" == 1 ]] || db_stop
    c_green "停止完成"
}

do_status() {
    echo
    for name in api worker ui; do
        if is_running "$name"; then
            c_green "  $name      running (pid $(pgrep -f "$(proc_pattern "$name")" | tr '\n' ' '))"
        else
            echo "  $name      stopped"
        fi
    done
    for name in cmdb-db cmdb-cache; do
        s="$(docker inspect -f '{{.State.Status}}/{{.State.Health.Status}}' "$name" 2>/dev/null || echo stopped)"
        echo "  $name  $s"
    done
}

# ---------- 参数解析 ----------
CMD="${1:-}"; shift || true
LOGS_NAME=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --flask)   BACKEND=flask ;;
        --fastapi) BACKEND=fastapi ;;
        --worker)  WITH_WORKER=1 ;;
        --init)    DO_INIT=1 ;;
        --keep-db) KEEP_DB=1 ;;
        *) if [[ "$CMD" == logs && -z "$LOGS_NAME" ]]; then
               LOGS_NAME="$1"
           else
               c_red "未知参数：$1"; exit 2
           fi ;;
    esac
    shift
done

case "$CMD" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_stop; KEEP_DB=1; do_start ;;  # restart 不动数据库
    status)  do_status ;;
    logs)    name="${LOGS_NAME:-api}"; tail -f "$RUN_DIR/$name.log" ;;
    *)
        sed -n '2,22p' "$0"
        exit 2
        ;;
esac
