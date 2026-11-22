# AGENT.md — 目录级开发指南

> 面向 AI 编码助手与人类开发者的目录说明。**版本 0.15.0（2026-11-08）**，与代码同步。
> 入口先读 [`AGENTS.md`](AGENTS.md)；路由 / MCP 工具 / 适配器能力 / 表结构等**事实清单**看
> [`docs/agent/CONTEXT.md`](docs/agent/CONTEXT.md)（由 `scripts/gen_agent_context.py` 生成，勿手改）。

## 1. 目录结构

```
harbor/
├── AGENTS.md / AGENT.md       # 智能体入口 / 本文件（目录级细节）
├── mcp_server.py              # MCP Server：32 tool，stdio / streamable-http / SSE
├── backed/                    # 后端（FastAPI，uv 管理）
│   ├── app/                   # 工厂 / 中间件 / 异常 / 基础路由
│   ├── api/                   # HTTP 边界：hub.py 聚合，routers/* 按领域拆
│   ├── service/publishing/    # 业务层：Hub、任务引擎、门禁、事件、媒体、版本、适配器
│   ├── config/                # 配置（config.json 为运行时唯一口径）
│   ├── core/ middleware/      # 拟人点击、权限、限流、安全头、审计
│   ├── utils/                 # 日志、脱敏、JWT、响应码
│   ├── tests/                 # 49 个 test_*.py
│   ├── cli.py / start.py / desktop_sidecar.py
│   └── pyproject.toml / uv.lock
├── web/                       # Vue3 + Element Plus + Pinia；src-tauri/ 为 Tauri 2 壳
├── deploy/                    # Dockerfile、docker-compose.yml、nginx.conf
├── scripts/                   # 门禁、上下文生成、备份、截图、真机验证、登录诊断
└── docs/                      # 架构 / 审计 / 设计 / 验证记录 / 智能体上下文
```

### 后端关键模块（`backed/service/publishing/`）

| 文件 | 职责 |
|---|---|
| `service.py` | Hub 编排器：账号、浏览器池、生命周期，组合三个 mixin |
| `article_ops.py` / `ai_ops.py` / `publish_ops.py` | 文章 CRUD、AI 委托、发布/更新/同步编排 |
| `tasks.py` | TaskManager：tasks 表持久化，单 worker 串行消费，重试与退避 |
| `db.py` | **唯一** SQL 与 schema（6 张表 + FTS5 + 迁移） |
| `browser.py` / `browser_pool.py` | Patchright 单浏览器线程 + 实例池（LRU，per-key 互斥） |
| `gate.py` | AIGC 合规四道闸门（安全扫描 / AIGC 标识 / 双模型审查 / 人工确认） |
| `events.py` / `_sse_broker.py` / `_webhook_store.py` | 事件、SSE 重放、Webhook HMAC |
| `observability.py` | 日志 / 指标 / trace，`/metrics` 双格式（JSON + Prometheus） |
| `media.py` / `content_transform.py` / `content_qa.py` | 媒体内容寻址、平台 AST 变换、内容质检 |
| `versions.py` / `tags.py` / `scheduler.py` | 版本快照回滚、标签治理、定时发布 |
| `url_safety.py` | 出网统一校验：公网 IP 判定 / 连接钉扎 / 逐跳重定向 |
| `adapters/` | 15 个平台适配器 + `base.py` 能力矩阵与注册器 |

### 平台适配器（15 个，`adapters/*.py`）

```
adapters/wuyi_cto.py       # 51CTO · 协议（XML-RPC）
adapters/bilibili.py       # B站专栏 · 浏览器
adapters/cnblogs.py        # 博客园 · 协议（XML-RPC）
adapters/csdn.py           # CSDN · 浏览器
adapters/devto.py          # Dev.to · 协议（REST API）
adapters/github_pages.py   # GitHub Pages · 协议（Contents API）
adapters/juejin.py         # 掘金 · 浏览器
adapters/metaweblog.py     # 自建博客 WordPress/Typecho · 协议（XML-RPC）
adapters/oschina.py        # 开源中国 · 浏览器
adapters/segmentfault.py   # SegmentFault · 浏览器
adapters/telegraph.py      # Telegraph · 协议（免注册 token）
adapters/toutiao.py        # 头条号 · 浏览器
adapters/wechat.py         # 微信公众号 · 协议（AppSecret）
adapters/xiaohongshu.py    # 小红书 · 浏览器扫码
adapters/zhihu.py          # 知乎 · 浏览器
```

能力矩阵以代码声明为准（`CAPABILITIES` + 每个类的 `capabilities`），完整矩阵见
[`docs/agent/CONTEXT.md`](docs/agent/CONTEXT.md) §5。新平台接入步骤见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

### 脚本

`scripts/` 里每个都该有 `--help` 或被文档引用：

| 脚本 | 用途 |
|---|---|
| `check_all.sh` / `check_all.ps1` | 一键门禁（Linux/macOS、Windows 两版） |
| `gen_agent_context.py` | 生成 `docs/agent/CONTEXT.*`；`--check` 进 CI |
| `bump_version.py` | 六处版本清单原子更新与一致性校验 |
| `scan_secrets.py` | 密钥扫描（token 前缀 / 私钥头 / 高熵赋值） |
| `backup_data.py` | 在线一致性快照（`sqlite3.Connection.backup()` + integrity_check） |
| `verify_real_publish.py` | 真机发布验证（真 commit、真回读、原地上新、默认自动清理） |
| `capture_screenshots.py` | 重新生成 README 截图 |
| `login_probe.py` | 登录页诊断（导出二维码 / 复检登录态，不代替扫码） |
| `stage_sidecar.py` / `build_sidecar.ps1` | Tauri 桌面端 sidecar 打包 |

## 2. 数据流

```
HTTP → 鉴权中间件（X-API-Token + XFF 受信判定）→ api/hub.py（聚合 10 个子路由）
     → Hub 单例（惰性）→ TaskManager.submit()（落 tasks 表）→ worker 线程
     → gate.py（四道闸门）→ media.py（图片本地化）→ content_transform.py（平台改写）
     → adapters/<platform>.publish|update → publications 落库 + 回读 verify_state
```

- **REST 异步模型**：`submit()` 立刻返回 `task_id`，客户端轮询或走 SSE。
- **MCP 同步模型**：`mcp_server.py` 直接调 `hub.publish(...)`，同步返回结果。
- **任务状态**：`pending → running → ok / failed / waiting_human`；启动时把残留 `running` 放回 `pending`。

## 3. 开发命令

```bash
# 后端
cd backed && uv sync
uv run uvicorn app.factory:create_app --factory --host 127.0.0.1 --port 8000 --reload

# 前端（registry 必须显式指定，本机 npmmirror 会 407）
cd web && pnpm install --frozen-lockfile --registry=https://registry.npmjs.org
pnpm dev            # http://127.0.0.1:5173，代理 /api 到 8000

# 门禁 / 测试
bash scripts/check_all.sh
cd backed && uv run pytest -q
uv run ruff check .

# 版本
cd backed && uv run python ../scripts/bump_version.py x.y.z
```

## 4. 不要做的事

- 不要在 `db.py` 之外写原生 SQL（跨表查询走 `db.list_*`）
- 不要在 `browser.py` 之外直接操作 Playwright context / 另起线程
- 不要在 `api/hub.py` 之外创建 FastAPI router（端点一律进 `api/routers/*`）
- 不要绕过 TaskManager 持久化任务（MCP 同步调用与 CLI 除外）
- 不要给适配器声明没实现的能力（默认全 False 是有意的）
- 不要把"接口返回 200"当成发布成功（看 `publications.verify_state`）
- 不要手改 `docs/agent/CONTEXT.*`（改代码后跑生成器）
- 不要改 `check_all.ps1` 里 scriptblock 内的 `exit` 语义（会杀掉整个 pwsh）

## 5. 配置与环境变量

| 环境变量 | 说明 | 默认 |
|---|---|---|
| `HARBOR_API_TOKEN` | REST 鉴权 Token（优先于 config.json） | 未配置时首启生成 UUID 并落盘 |
| `HARBOR_SECRET_KEY` | 签名密钥（生产必须设） | 开发随机/空 |
| `TRUSTED_NETS` | 受信代理网段（XFF 校验） | 127.0.0.0/8, ::1/128 |
| `TRUSTED_PROXIES` | 受信反向代理 IP（限流键） | 空 |
| `CORS_ORIGINS` | 跨域白名单（逗号分隔） | 同源 |
| `DEMO=1` | 演示模式（不开浏览器、不调外部 API） | 0 |
| `AI_API_KEY` / `AI_BASE_URL` | LLM 密钥与端点 | 空 / deepseek |
| `ASSIST_ALLOW_LOCAL=1` | 允许 assist 打开 localhost（桌面调试） | 0 |
| `FERNET_KEY` | Webhook secret 加密主密钥 | 自动生成 |

用户配置的**唯一运行时口径**是 `backed/config.json`（`service/publishing/db.py:config_file()`，
env > 数据根 > 旧版位置）。`config_unified.py` 那套 Pydantic 类是大头死配置，别往上面加字段。

## 6. 登录诊断

```bash
uv run --project backed python scripts/login_probe.py --platform juejin
uv run --project backed python scripts/login_probe.py --platform csdn --headed --wait 30
uv run --project backed python scripts/login_probe.py --platform juejin --check-cookie
```

它只回答两件事：登录页是否可用、二维码/登录态是否真的生成。真实扫码走应用内
「设置 → 平台账号 → 去登录」。
