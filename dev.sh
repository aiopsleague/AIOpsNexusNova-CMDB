#!/usr/bin/env bash
# dev.sh — 本地开发环境一键启停
#
# 依赖（MySQL/Redis）用 docker 在本地跑，后端和前端直接在宿主机跑。
# 后端默认是新版 FastAPI（cmdb-api-fastapi），也支持旧版 Flask（cmdb-api）。
#
# 用法：
#   ./dev.sh start                      # 启动全部服务：db + fastapi + worker + ui
#   ./dev.sh start <服务...>            # 只启动指定服务，可多个，如：
#                                       #   ./dev.sh start fastapi
#                                       #   ./dev.sh start db fastapi worker
#                                       #   ./dev.sh start flask          （旧版后端）
#                                       #   ./dev.sh start init           （只跑初始化命令）
#   ./dev.sh stop [服务...|all]         # 停止全部或指定服务（init 不是常驻进程，无 stop）
#   ./dev.sh restart [服务...|all]      # 重启全部（含 db）或指定服务
#   ./dev.sh status                     # 查看各服务状态
#   ./dev.sh logs [api|worker|ui]       # 跟踪某个服务的日志（默认 api）
#
# 服务名：db、fastapi、flask、ui、worker、init、all（all 与留空等价，= db+fastapi+worker+ui）
# 选项：
#   --flask / --fastapi  指定后端实现（同直接写 flask/fastapi 服务名；
#                        flask 需要先在 cmdb-api 里 pipenv install）
#   --init               start 全部时在启动后端前跑一遍初始化命令（首次建库时用）
#   --keep-db            stop 全部时保留 MySQL/Redis 容器
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
# api 同时匹配两种后端，保证 stop/status 不受启动时选择的是哪个后端影响。
proc_pattern() {  # $1=name
    case "$1" in
        api)    echo 'uvicorn main:app|flask run' ;;
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
FASTAPI_DIR="$ROOT/cmdb-api-fastapi"
FLASK_DIR="$ROOT/cmdb-api"

detect_flask() {  # 检测旧版后端的运行方式，结果写入全局数组 FLASK_RUN
    if [[ -x "$FLASK_DIR/.venv/bin/flask" ]]; then
        FLASK_RUN=("$FLASK_DIR/.venv/bin/flask")
    elif command -v pipenv >/dev/null && ( cd "$FLASK_DIR" && pipenv --venv ) >/dev/null 2>&1; then
        FLASK_RUN=(pipenv run flask)
    else
        c_red "旧版 cmdb-api 的依赖环境不存在，请先在 cmdb-api 目录执行 pipenv install"
        return 1
    fi
}

api_start() {
    if [[ "$BACKEND" == fastapi ]]; then
        [[ -x "$FASTAPI_DIR/.venv/bin/uvicorn" ]] || { c_red "找不到 $FASTAPI_DIR/.venv，请先创建虚拟环境安装依赖"; return 1; }
        start_proc api "$FASTAPI_DIR" .venv/bin/uvicorn main:app --host 0.0.0.0 --port "$API_PORT" --reload
    else
        detect_flask || return 1
        start_proc api "$FLASK_DIR" env FLASK_APP=autoapp.py FLASK_ENV=development \
            "${FLASK_RUN[@]}" run --host 0.0.0.0 --port "$API_PORT"
    fi
    wait_http "http://127.0.0.1:$API_PORT/api/health" "后端($BACKEND)" 60
}

api_stop() {
    stop_proc api
}

worker_start() {
    if [[ "$BACKEND" == fastapi ]]; then
        [[ -x "$FASTAPI_DIR/.venv/bin/celery" ]] || { c_red "找不到 $FASTAPI_DIR/.venv"; return 1; }
        start_proc worker "$FASTAPI_DIR" .venv/bin/celery -A celery_worker.celery worker --beat -E \
            -Q one_cmdb_async,acl_async,beat_tasks --loglevel=info
    else
        detect_flask || return 1
        # 与 flask 同一虚拟环境里的 celery
        local celery=("${FLASK_RUN[@]/flask/celery}")
        start_proc worker "$FLASK_DIR" "${celery[@]}" -A celery_worker.celery worker --beat -E \
            -Q one_cmdb_async,acl_async,beat_tasks --loglevel=info
    fi
}

worker_stop() {
    stop_proc worker
}

# 初始化命令（建表/缓存/ACL/部门等），两个后端的命令名保持一致。
# 注意：部分命令（如 cmdb-init-acl）不是幂等的，在已初始化的库上会报错，
# 这里逐条执行、失败只告警不中断。
run_init() {
    c_yellow "执行初始化命令（后端：$BACKEND）..."
    local cmds=(db-setup common-check-new-columns cmdb-init-cache cmdb-init-acl init-import-user-from-acl init-department)
    local failed=0 c old_pwd="$PWD"
    if [[ "$BACKEND" == fastapi ]]; then
        [[ -x "$FASTAPI_DIR/.venv/bin/python" ]] || { c_red "找不到 $FASTAPI_DIR/.venv"; return 1; }
        cd "$FASTAPI_DIR"
        for c in "${cmds[@]}"; do
            .venv/bin/python cli.py "$c" || { c_red "[warn] $c 执行失败（已初始化的库上属预期），跳过"; failed=1; }
        done
    else
        detect_flask || return 1
        cd "$FLASK_DIR"
        for c in "${cmds[@]}"; do
            "${FLASK_RUN[@]}" "$c" || { c_red "[warn] $c 执行失败（已初始化的库上属预期），跳过"; failed=1; }
        done
    fi
    cd "$old_pwd"
    [[ "$failed" == 1 ]] && c_yellow "初始化完成（部分命令报错已跳过，详见上方输出）" || c_green "初始化完成"
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

# ---------- 服务调度 ----------
start_one() {  # $1=服务名
    case "$1" in
        db)            db_start ;;
        fastapi|flask|api) api_start ;;
        worker)        worker_start ;;
        ui)            ui_start ;;
        init)          run_init ;;
        all)           do_start_all ;;
        *) c_red "未知服务：$1"; return 2 ;;
    esac
}

stop_one() {  # $1=服务名
    case "$1" in
        db)            db_stop ;;
        fastapi|flask|api) api_stop ;;
        worker)        worker_stop ;;
        ui)            ui_stop ;;
        init)          c_yellow "init 不是常驻进程，无需停止" ;;
        all)           do_stop_all ;;
        *) c_red "未知服务：$1"; return 2 ;;
    esac
}

do_start_all() {
    db_start
    [[ "$DO_INIT" == 1 ]] && run_init
    api_start
    worker_start
    ui_start
    echo
    c_green "全部启动完成："
    echo "  前端  http://127.0.0.1:$UI_PORT  (demo / 123456)"
    echo "  后端  http://127.0.0.1:$API_PORT  ($BACKEND)"
    do_status
}

do_stop_all() {
    ui_stop
    worker_stop
    api_stop
    [[ "$KEEP_DB" == 1 ]] || db_stop
    c_green "停止完成"
}

do_start() {
    if [[ ${#SERVICES[@]} -eq 0 ]]; then
        do_start_all
    else
        for s in "${SERVICES[@]}"; do start_one "$s"; done
    fi
}

do_stop() {
    if [[ ${#SERVICES[@]} -eq 0 ]]; then
        do_stop_all
    else
        for s in "${SERVICES[@]}"; do stop_one "$s"; done
    fi
}

do_restart() {
    if [[ ${#SERVICES[@]} -eq 0 ]]; then
        do_stop_all
        do_start_all
    else
        for s in "${SERVICES[@]}"; do
            [[ "$s" == init ]] && { c_yellow "init 不是常驻进程，直接执行"; run_init; continue; }
            stop_one "$s"
            start_one "$s"
        done
    fi
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
SERVICES=()
LOGS_NAME=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --flask)   BACKEND=flask ;;
        --fastapi) BACKEND=fastapi ;;
        --worker)  WITH_WORKER=1 ;;
        --init)    DO_INIT=1 ;;
        --keep-db) KEEP_DB=1 ;;
        db|fastapi|flask|api|ui|worker|init|all)
            if [[ "$CMD" == start || "$CMD" == stop || "$CMD" == restart ]]; then
                SERVICES+=("$1")
                # 服务名里明确写了后端实现的，以此为准
                [[ "$1" == flask ]] && BACKEND=flask
                [[ "$1" == fastapi || "$1" == api ]] && BACKEND=fastapi
            elif [[ "$CMD" == logs && -z "$LOGS_NAME" ]]; then
                LOGS_NAME="$1"
            else
                c_red "未知参数：$1"; exit 2
            fi ;;
        *) c_red "未知参数：$1"; exit 2 ;;
    esac
    shift
done

case "$CMD" in
    start)   do_start ;;
    stop)    do_stop ;;
    restart) do_restart ;;
    status)  do_status ;;
    logs)    name="${LOGS_NAME:-api}"; tail -f "$RUN_DIR/$name.log" ;;
    *)
        sed -n '2,29p' "$0"
        exit 2
        ;;
esac
