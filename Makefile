include ./Makefile.variable

# ---- Image tags (used by docker-compose.yml) ------------------------------------
export CMDB_API_IMAGE  ?= $(REGISTRY)/cmdb-api:$(CMDB_DOCKER_VERSION)
export CMDB_UI_IMAGE   ?= $(REGISTRY)/cmdb-ui:$(CMDB_DOCKER_VERSION)
export NGINX_PORT      ?= 80

default: help
help:  ## display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
.PHONY: help

##@ Development
env: ## create a development environment
	pip install uv -i https://repo.huaweicloud.com/repository/pypi/simple && \
	npm install yarn && \
	make deps
.PHONY: env

deps: ## install dependencies
	cd cmdb-api && uv sync --dev && cd .. && \
	cd cmdb-ui && yarn install && cd ..
.PHONY: deps

init: ## initial data setup (migrate + seed + cache, same order as docker-compose)
	cd cmdb-api && \
	uv run python cli.py db-setup && \
	uv run python cli.py common-check-new-columns && \
	uv run python cli.py cmdb-init-cache && \
	uv run python cli.py cmdb-init-acl || true && \
	uv run python cli.py init-import-user-from-acl || true && \
	uv run python cli.py init-department
.PHONY: init

api: ## start API dev server (FastAPI — uvicorn)
	cd cmdb-api && uv run uvicorn main:app --host 0.0.0.0 --port 5000 --reload
.PHONY: api

worker: ## start async tasks worker (dev)
	cd cmdb-api && uv run celery -A celery_worker.celery worker -E -Q one_cmdb_async,acl_async --loglevel=warning --concurrency=4
.PHONY: worker

ui: ## start UI dev server
	cd cmdb-ui && yarn run serve
.PHONY: ui

lint: ## check style with ruff
	cd cmdb-api && uv run ruff check .
.PHONY: lint

##@ Docker Compose — Production Stack
docker-up: ## start all services (docker compose up -d)
	docker compose up -d
.PHONY: docker-up

docker-down: ## stop all services (preserves data volumes)
	docker compose down
.PHONY: docker-down

docker-down-v: ## stop all services AND delete data volumes
	docker compose down -v
.PHONY: docker-down-v

docker-restart: ## restart all services
	docker compose restart
.PHONY: docker-restart

docker-restart-api: ## restart cmdb-api only
	docker compose restart cmdb-api
.PHONY: docker-restart-api

docker-logs: ## tail logs for all services
	docker compose logs -f --tail=100
.PHONY: docker-logs

docker-logs-api: ## tail logs for cmdb-api only
	docker compose logs -f --tail=100 cmdb-api
.PHONY: docker-logs-api

docker-ps: ## show running services status
	docker compose ps
.PHONY: docker-ps

docker-pull: ## pull latest images defined in docker-compose.yml
	docker compose pull
.PHONY: docker-pull

##@ Docker Compose — One-shot helpers
docker-shell-db: ## open mysql shell in the running cmdb-db container
	docker compose exec cmdb-db mysql -u$(MYSQL_USER) -p$(MYSQL_PASSWORD) $(MYSQL_DATABASE)
.PHONY: docker-shell-db

docker-shell-api: ## open a shell in the running cmdb-api container
	docker compose exec cmdb-api /bin/sh
.PHONY: docker-shell-api

docker-cli: ## run a management CLI command (usage: make docker-cli CMD="db-setup")
	docker compose exec cmdb-api python cli.py $(CMD)
.PHONY: docker-cli

##@ Docker Image Build
docker-build: docker-build-api docker-build-ui ## build API and UI images

docker-build-api: ## build cmdb-api Docker image
	export DOCKER_CLI_EXPERIMENTAL=enabled ;\
	! ( docker buildx ls | grep multi-platform-builder ) && docker buildx create --use --platform=$(BUILD_ARCH) --name multi-platform-builder ;\
	docker buildx build \
		--builder multi-platform-builder \
		--platform=$(BUILD_ARCH) \
		--tag $(REGISTRY)/cmdb-api:$(CMDB_DOCKER_VERSION) \
		--tag $(REGISTRY)/cmdb-api:latest \
		--load \
		-f docker/Dockerfile-API \
		.
.PHONY: docker-build-api

docker-build-ui: ## build cmdb-ui Docker image
	export DOCKER_CLI_EXPERIMENTAL=enabled ;\
	! ( docker buildx ls | grep multi-platform-builder ) && docker buildx create --use --platform=$(BUILD_ARCH) --name multi-platform-builder ;\
	docker buildx build \
		--builder multi-platform-builder \
		--platform=$(BUILD_ARCH) \
		--tag $(REGISTRY)/cmdb-ui:$(CMDB_DOCKER_VERSION) \
		--tag $(REGISTRY)/cmdb-ui:latest \
		--load \
		-f docker/Dockerfile-UI \
		.
.PHONY: docker-build-ui

docker-push: docker-build-api docker-build-ui ## build and push images to registry
	docker push $(REGISTRY)/cmdb-api:$(CMDB_DOCKER_VERSION)
	docker push $(REGISTRY)/cmdb-api:latest
	docker push $(REGISTRY)/cmdb-ui:$(CMDB_DOCKER_VERSION)
	docker push $(REGISTRY)/cmdb-ui:latest
.PHONY: docker-push

##@ Cleanup
clean: ## remove unwanted files like .pyc's
	cd cmdb-api && uv run python cli.py clean
.PHONY: clean

docker-clean: docker-down ## stop services and remove dangling images/volumes
	docker system prune -f
.PHONY: docker-clean
