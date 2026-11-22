# Harbor — 常用命令入口
#
# 目的：AI 和人都不用记长命令，`make <target>` 即可。
# 注意：web 的 pnpm 必须显式指定官方 registry，本机 npmmirror 的 tarball 会 407。

.DEFAULT_GOAL := help
.PHONY: help install install-backend install-web dev web demo test check context bump clean-web

help:
	@echo "make install   安装后端+前端依赖"
	@echo "make dev       起后端（热重载，127.0.0.1:8000）"
	@echo "make web       起前端（127.0.0.1:5173，代理 /api）"
	@echo "make demo      演示模式起后端（不开浏览器/不调外部 API，端口 8011）"
	@echo "make test      后端 pytest"
	@echo "make check     一键八道门禁"
	@echo "make context   重新生成 docs/agent/CONTEXT.*（改完代码必跑）"
	@echo "make bump V=x.y.z  六处版本清单原子更新"

install: install-backend install-web

install-backend:
	cd backed && uv sync

install-web:
	cd web && pnpm install --frozen-lockfile --registry=https://registry.npmjs.org

dev:
	cd backed && uv run uvicorn app.factory:create_app --factory --host 127.0.0.1 --port 8000 --reload

web:
	cd web && pnpm dev

demo:
	cd backed && DEMO=1 HARBOR_API_TOKEN=dev uv run uvicorn app.factory:create_app --factory --port 8011

test:
	cd backed && uv run pytest -q

check:
	bash scripts/check_all.sh

context:
	cd backed && uv run python ../scripts/gen_agent_context.py

bump:
	@test -n "$(V)" || (echo "用法：make bump V=0.16.0" && exit 1)
	cd backed && uv run python ../scripts/bump_version.py "$(V)"

clean-web:
	rm -rf web/dist server/static
