# AGENTS.md — 给 AI 编码助手的入口

> 读完这一份 + [`docs/agent/CONTEXT.md`](docs/agent/CONTEXT.md)，就够开工，不需要再喂背景。
> 本文件手写；**事实清单**（路由 / MCP 工具 / 适配器能力 / 表结构 / 测试分布）在 CONTEXT 里，由代码生成，不会漂。

## 1. 这是什么

Harbor（内容港）：自托管的多平台内容发布中台。一次写作 → 多平台分发 → 原地更新 → **发布后回读确认**。
Python 3.12 + FastAPI + 裸 sqlite3（WAL / FTS5）+ Patchright（Playwright 反检测分支）；Vue3 + Element Plus + Pinia + Tauri 2。
单机、单用户、无遥测。不是 CMS，不是 SaaS，不做验证码破解。

## 2. 十分钟跑起来

```bash
# 后端
cd backed && uv sync
uv run uvicorn app.factory:create_app --factory --host 127.0.0.1 --port 8000 --reload
uv run python -m cli init --name <name> --platforms cnblogs,juejin   # 个人档案，留在本机

# 前端（本机 npmmirror 的 tarball 会 407，必须显式指定官方 registry）
cd web && pnpm install --frozen-lockfile --registry=https://registry.npmjs.org && pnpm dev

# 演示模式：不开浏览器、不调外部 API，只跑任务引擎与前端全链路
DEMO=1 HARBOR_API_TOKEN=dev uv run uvicorn app.factory:create_app --factory --port 8011
```

或 `make install` / `make dev` / `make test` / `make check` / `make context`。

## 3. 开工前按顺序读

1. 本文件
2. [`docs/agent/CONTEXT.md`](docs/agent/CONTEXT.md) — 模块、99 个 REST 操作、32 个 MCP tool、15 个适配器能力矩阵、6 张表、测试分布（**代码生成**）
3. [`AGENT.md`](AGENT.md) — 目录级细节与历史约定（改哪块查哪块）
4. [`docs/PROJECT_MANAGEMENT.md`](docs/PROJECT_MANAGEMENT.md) — 分支模型、完成定义、五仓同步
5. [`docs/VERSIONING.md`](docs/VERSIONING.md) — 版本与发布清单

做运营/定时任务时，另读 [`playbooks/README.md`](playbooks/README.md)。`playbooks/` 是**模板**，不含账号；个人副本放 `profiles/<name>/playbooks/`（已 gitignore）。**cron 里只有触发和指针，流程正文在文件里**。

## 4. 代码地图（一层一句话）

| 路径 | 职责 | 规矩 |
|---|---|---|
| `backed/api` | HTTP 边界 | 端点只写 `api/routers/*`；装配只在 `api/hub.py` |
| `backed/service/publishing` | 业务：Hub / TaskManager / 门禁 / 事件 / 媒体 / 版本 | 不碰 HTTP 细节 |
| `backed/service/publishing/adapters` | 15 个平台适配器 | 每个必须显式声明 `capabilities`，默认全 False |
| `backed/service/publishing/db.py` | **唯一** SQL 与 schema | 别在别处写原生 SQL |
| `backed/app` | 工厂 / 中间件 / 异常 / 路由 | 中间件开关默认：安全头开，限流与审计关 |
| `mcp_server.py` | 32 个 MCP tool，stdio / streamable-http / SSE | 对外传输非 loopback 必须带 bearer token |
| `web/` | Vue3 表现层 + Tauri 壳 | 不放业务规则 |
| `deploy/` | Dockerfile / compose / nginx | 从仓库根上下文构建 |
| `scripts/` | 门禁、生成、备份、真机验证 | 每个脚本带 `--help` 或被文档引用 |
| `playbooks/` | 4 份运营 SOP 模板（博客园/知乎/CSDN/掘金）；向导可接 15 个适配器，没模板的平台也能登录/发布 | 模板不含账号；个人副本放 `profiles/<name>/`，不回写 cron |
| `profiles/` | 个人档案约定（账号/主线/报告/进度） | 只提交 `README.md` 与 `example.yaml`，真实档案不入库 |

## 5. 三条主链（改之前先认路）

**发布**：`POST /api/v1/hub/articles/{aid}/publish` → `Hub.publish` → `TaskManager.submit`（落 tasks 表）→ 单 worker 线程 →
平台门禁 `gate.py` → 媒体本地化 `media.py` → 平台结构变换 `content_transform.py` → `adapter.publish/update` →
`publications` 落库 + 回读 `verify_state`。

**任务状态机**：`pending → running → ok / failed / waiting_human`。重启时残留 `running` 会被放回 `pending`；
`pending_user`（assist/manual 模式）是"等你操作"，不是失败；`waiting_human` 只能走 `resume`。

**事件**：事件表 → SSE broker（单调 id + 256 条重放，`Last-Event-ID` 补洞）→ 站内通知 / webhook（HMAC 签名）。

## 6. 硬规则（违反会被测试或 CI 抓）

- 路由只在 `api/hub.py` 聚合；端点写进 `api/routers/*`
- SQL 只在 `db.py`；跨表查询走 `db.list_*` 系列
- Playwright 只能经 `browser_thread_run`；不要自己起线程、不要跨线程用实例（greenlet 会炸）
- 不要绕过 TaskManager 建任务（MCP 同步调用与 CLI 除外）
- 新增平台必须声明能力矩阵，**没做过的能力不许写 True**；前端按矩阵置灰
- 任何"成功"必须有证据：接口 200 ≠ 发布成功，回读才算；`verify_state` 默认必须是 `unverified`
- 文档不许比代码宽：README 每条能力必须有测试，或 `docs/verification/` 里一条带日期的真机记录
- 事实清单进生成物：加完端点/工具/适配器，跑 `python scripts/gen_agent_context.py` 再提交
- 运营流程进 `playbooks/`：cron 的 query 只留触发 + 指针，不把 SOP 写回定时任务
- 个人数据不进仓库：账号、平台用户 ID、文章 ID、报告链接、本机路径一律放 `profiles/<name>/`；提交前跑 `python scripts/scan_privacy.py`
- 登录只在 Harbor 主机完成：Agent 不接管账号密码/cookie；未登录置 `waiting_human`，由前端提示人接管（见 `docs/guides/login.md`）

## 7. 已知陷阱（踩过，别再踩）

- **Patchright 线程模型**：进程级共享 driver + 单浏览器线程。跨线程调用必炸。
- **SQLite**：单共享连接 + 锁；别自己再开第二个写入连接，`busy_timeout` 也别乱改小。
- **假成功史**：0.8→0.14 的事故全在"接口成功 ≠ 平台真有这篇"。先看 `publications.verify_state`。
- **平台改版**：选择器失效看 `selector_version` / `key_selectors`，跑 `/adapters/probe` 与 `dump-dom`。
- **前端 lint**：`--max-warnings=999` 等于关掉，现有 200+ warning 不要当正常。
- **依赖**：Dependabot 目前红着（Pillow 分叉），升级走手动；`uv.lock` 是唯一锁。
- **本机 pnpm**：npmmirror tarball 走代理 407，用 §2 里的命令。

## 8. 测试与门禁

```bash
bash scripts/check_all.sh          # 一键八道（含智能体上下文新鲜度）
cd backed && uv run pytest -q      # 单跑（展开后的用例数以命令输出为准，分布见 CONTEXT.md）
uv run ruff check .                # 静态（E4/E7/E9/F，E402 故意放行）
```

- 测试数、路由数这类会变的东西一律看 `docs/agent/CONTEXT.md`，不要写死在别的文档里
- 改代码的顺序：先复现/先写测试 → 再改实现 → 跑门禁 → 重生成 CONTEXT

## 9. 提交与推送

- trunk-based：只有 `main`；短分支 ≤3 天；squash 合并
- commit：`type(scope): 中文一句话`，body 写"为什么"和"怎么验的"
- 多仓镜像：按本机 remote 配置逐个推 `main`；凭据放 credential helper，不写进仓库、不进 commit
- 版本：SemVer + 六处清单，`uv run python scripts/bump_version.py x.y.z`；不要手改单处

## 10. 给 AI 的任务模板（越短越好，细节都在仓库里）

- 修 bug：`读 AGENTS.md，按 §5 定位「现象」，先复现再改，跑 check_all`
- 加平台：`按 §6 新增适配器 + capabilities + 契约测试，最后重生成 CONTEXT`
- 重构：`只动 <目录>，行为不变，全部测试必须全绿`
- 每日运营：`读 profiles/<name>/playbooks/<platform>.md 执行，登录失效即停，结束写“已做完”`
- 发版：`按 docs/VERSIONING.md 的清单走，CHANGELOG 用 Keep a Changelog 单块`
