#!/usr/bin/env bash
# =============================================================================
# CMDB — Docker 镜像构建脚本
# =============================================================================
# 用法:
#   ./build.sh              # 构建 cmdb-api:latest 和 cmdb-ui:latest
#   ./build.sh --push       # 构建并推送到 REGISTRY
#   REGISTRY=my-registry.com/cmdb ./build.sh --push
#
# 环境变量:
#   REGISTRY        镜像仓库前缀，如 registry.cn-hangzhou.aliyuncs.com/veops
#                   留空则构建为本地镜像 cmdb-api:latest / cmdb-ui:latest
#   CMDB_API_IMAGE  覆盖 API 镜像全名（设置后忽略 REGISTRY）
#   CMDB_UI_IMAGE   覆盖 UI 镜像全名（设置后忽略 REGISTRY）
#   BUILD_ARGS      额外的 docker build 参数
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

PUSH=false
case "${1:-}" in
  --push) PUSH=true ;;
  -h|--help)
    sed -n '2,15p' "$0" | sed 's/^# //'
    exit 0
    ;;
esac

# ---- 确定镜像名称 --------------------------------------------------------------
API_IMAGE="${CMDB_API_IMAGE:-${REGISTRY:+$REGISTRY/}cmdb-api:latest}"
UI_IMAGE="${CMDB_UI_IMAGE:-${REGISTRY:+$REGISTRY/}cmdb-ui:latest}"

cd "$PROJECT_DIR"

# ---- 构建 API 镜像 ------------------------------------------------------------
echo ">>> Building API image: $API_IMAGE"
# shellcheck disable=SC2086
docker build \
  -f docker/Dockerfile-API \
  -t "$API_IMAGE" \
  ${BUILD_ARGS:-} \
  .

# ---- 构建 UI 镜像 -------------------------------------------------------------
echo ">>> Building UI image: $UI_IMAGE"
# shellcheck disable=SC2086
docker build \
  -f docker/Dockerfile-UI \
  -t "$UI_IMAGE" \
  ${BUILD_ARGS:-} \
  .

echo ">>> Build complete"

# ---- 推送 --------------------------------------------------------------------
if $PUSH; then
  if [ -z "${REGISTRY:-}" ]; then
    echo "ERROR: --push requires REGISTRY to be set"
    exit 1
  fi
  echo ">>> Pushing $API_IMAGE"
  docker push "$API_IMAGE"
  echo ">>> Pushing $UI_IMAGE"
  docker push "$UI_IMAGE"
  echo ">>> Push complete"
fi
