# CONTEXT.md — 仓库事实清单（自动生成）

> 本文件由 `scripts/gen_agent_context.py` 从代码生成，**不要手改**。
> 改代码后跑 `python scripts/gen_agent_context.py`；CI 会跑 `--check`，漂了直接红。
> 机器可读版本：[`CONTEXT.json`](CONTEXT.json)

## 0. 一句话

**Harbor (内容港)** v0.15.0：自托管多平台内容发布中台。一次写作 → 多平台分发 → 原地更新 → 发布后回读确认。单机、单用户、无遥测。

| 项 | 值 |
|---|---|
| 版本 | 0.15.0 |
| 后端 | Python >=3.10 / FastAPI / 裸 sqlite3（WAL + FTS5） |
| 前端 | Vue3 + Element Plus + Pinia + Tauri 2 |
| 平台适配器 | 15 |
| REST | 100 个操作 |
| MCP | 33 个 tool |
| Python 模块 | 108（24260 行） |

## 1. 入口点

| 文件 | 作用 |
|---|---|
| `mcp_server.py` | MCP Server（stdio / streamable-http / SSE），32 个 tool |
| `backed/app/factory.py` | FastAPI 唯一装配入口 create_app() |
| `backed/cli.py` | 命令行入口 |
| `backed/desktop_sidecar.py` | Tauri 桌面端 sidecar 启动 |
| `scripts/check_all.sh` | 本地八道门禁 |
| `scripts/gen_agent_context.py` | 本文件生成器（--check 进 CI） |
| `playbooks/README.md` | 运营 SOP 模板索引；个人档案在 profiles/（gitignored） |

## 2. 运营 playbook（SOP）

共 15 份模板，位于 `playbooks/`。模板不含账号；真实档案、进度与报告链接放 `profiles/<name>/`（已 gitignore）。定时任务只负责触发，流程正文以文件为准。

| 平台 | 文件 | 触发 | 范围 | 行数 | 更新 |
|---|---|---|---|---|---|
| `51cto` 51CTO 博客发布（模板） | `playbooks/51cto.md` | 按需发布 | template | 48 | 2026-11-23 |
| `bilibili` B站专栏发布（模板） | `playbooks/bilibili.md` | 按需发布 | template | 46 | 2026-11-23 |
| `cnblogs` 博客园每日运营（模板） | `playbooks/cnblogs.md` | 建议每天 1 次（以 profile 为准） | template | 60 | 2026-11-22 |
| `csdn` CSDN 私密转公开（模板） | `playbooks/csdn.md` | 建议每天 1 次，直到清零 | template | 33 | 2026-11-22 |
| `devto` Dev.to 发布（模板） | `playbooks/devto.md` | 按需发布 | template | 48 | 2026-11-23 |
| `github` GitHub Pages 发布（模板） | `playbooks/github.md` | 按需发布 | template | 49 | 2026-11-23 |
| `juejin` 掘金每日运营（模板） | `playbooks/juejin.md` | 建议每天 1 次（以 profile 为准） | template | 34 | 2026-11-22 |
| `metaweblog` 自建博客发布（模板） | `playbooks/metaweblog.md` | 按需发布 | template | 47 | 2026-11-23 |
| `oschina` 开源中国发布（模板） | `playbooks/oschina.md` | 按需发布 | template | 47 | 2026-11-23 |
| `segmentfault` 思否发布（模板） | `playbooks/segmentfault.md` | 按需发布 | template | 45 | 2026-11-23 |
| `telegraph` Telegraph 发布（模板） | `playbooks/telegraph.md` | 按需发布 | template | 45 | 2026-11-23 |
| `toutiao` 头条号发布（模板） | `playbooks/toutiao.md` | 按需发布 | template | 46 | 2026-11-23 |
| `wechat` 微信公众号发布（模板） | `playbooks/wechat.md` | 按需发布 | template | 47 | 2026-11-23 |
| `xiaohongshu` 小红书笔记发布（模板） | `playbooks/xiaohongshu.md` | 按需发布 | template | 47 | 2026-11-23 |
| `zhihu` 知乎每日运营（模板） | `playbooks/zhihu.md` | 建议每天 1-2 次（以 profile 为准） | template | 50 | 2026-11-22 |

## 3. 模块依赖（包级计数 + 扇入 Top）

| 包 | 模块数 |
|---|---|
| `__init__` | 1 |
| `api` | 16 |
| `app` | 6 |
| `cli` | 1 |
| `config` | 4 |
| `core` | 4 |
| `desktop_sidecar` | 1 |
| `middleware` | 5 |
| `service` | 62 |
| `start` | 1 |
| `utils` | 7 |

被依赖最多（改它影响面最大）：

- `service.publishing.db` ← 32 个模块
- `service.publishing.adapters.base` ← 21 个模块
- `api.deps` ← 12 个模块
- `config` ← 12 个模块
- `utils.logger` ← 9 个模块
- `service.publishing.gate` ← 8 个模块
- `service.publishing.browser` ← 7 个模块
- `service.publishing.url_safety` ← 7 个模块
- `service.publishing.ai` ← 5 个模块
- `service.publishing.events` ← 5 个模块
- `service.publishing.versions` ← 5 个模块
- `service.publishing.ai_providers` ← 4 个模块

## 4. REST API

共 100 个操作，前缀 `/api/v1/hub`。

| 方法 | 路径 | 处理函数 | 说明 |
|---|---|---|---|
| GET | `/api/v1/hub/accounts` | `accounts` |  |
| POST | `/api/v1/hub/accounts/cnblogs/bootstrap` | `bootstrap_cnblogs` | 浏览器登录博客园并自动抠 MetaWeblog 三件套写 config.json。 |
| GET | `/api/v1/hub/accounts/cnblogs/bootstrap/{job_id}` | `bootstrap_cnblogs_job` |  |
| DELETE | `/api/v1/hub/accounts/{platform}` | `logout` | 清除登录态：删 profile + cookie 快照，账号状态置离线。 |
| POST | `/api/v1/hub/accounts/{platform}/assist` | `assist_open` | 带登录态的内置有头浏览器打开平台页（人工步骤接管）。 |
| GET | `/api/v1/hub/accounts/{platform}/check` | `check_account` |  |
| GET | `/api/v1/hub/accounts/{platform}/diagnose` | `diagnose` | 这个平台该怎么接、验证码怎么过——排查用。 |
| POST | `/api/v1/hub/accounts/{platform}/login` | `login` | 异步启动登录：提交任务，轮询 GET /tasks/{task_id}。 |
| POST | `/api/v1/hub/accounts/{platform}/solve-captcha` | `solve_captcha` | 打开页面就地处理验证码：先半自动试，不行转人工。 |
| GET | `/api/v1/hub/adapters/probe` | `adapters_probe` | 离线检查全部平台适配器：接口实现 / 能力一致性 / 选择器合法性 / DOM 漂移。 |
| POST | `/api/v1/hub/adapters/probe/{platform}/dump` | `adapters_probe_dump` | 保存一份平台 DOM 采样，供 probe 做选择器漂移比对。 |
| GET | `/api/v1/hub/ai/config` | `ai_config_get` | AI 配置全貌（密钥只回掩码，永不回显完整 key）。 |
| PUT | `/api/v1/hub/ai/config` | `ai_config_put` | 白名单写回：providers.<key> / REVIEW_MODEL / AI_DIRECT_PUBLISH。 |
| POST | `/api/v1/hub/ai/config/test` | `ai_config_test` | 真实最小调用测连通（ping→pong）。允许对未保存字段先测。 |
| GET | `/api/v1/hub/ai/gate` | `ai_gate` | AIGC 合规门禁状态：开关、审查模型、高危词数、直发开关、最近拒绝。 |
| GET | `/api/v1/hub/ai/providers` | `ai_providers` | 列出所有已配置的 AI Provider + 模型（掩码，不含明文密钥）。 |
| GET | `/api/v1/hub/ai/status` | `ai_status` |  |
| GET | `/api/v1/hub/ai/templates` | `ai_templates` | 列出所有可用写作模板。 |
| GET | `/api/v1/hub/ai/tool-providers` | `ai_tool_providers` | 平台外部工具 Provider（biliup-rs / wenyan-cli 等）安装与登录状态。 |
| POST | `/api/v1/hub/ai/write` | `ai_write` |  |
| POST | `/api/v1/hub/ai/write-template` | `ai_write_template` | 用预置模板 AI 写文章。 |
| GET | `/api/v1/hub/articles` | `list_articles` | 文章列表。默认只返回列表元信息（不含正文），避免整页正文 JSON 化。 |
| POST | `/api/v1/hub/articles` | `create_article` |  |
| POST | `/api/v1/hub/articles/import` | `import_md` | 导入文章：`path` 读本地 Markdown，`url` 抓网页转 Markdown（二选一）。 |
| GET | `/api/v1/hub/articles/page` | `articles_page` | 分页视图：返回 {items,total,has_more}，供前端「加载更多」。 |
| GET | `/api/v1/hub/articles/search/{keyword}` | `search` |  |
| DELETE | `/api/v1/hub/articles/{aid}` | `delete_article` | 删除本地文章记录。平台侧已发布的副本不会被动到。 |
| GET | `/api/v1/hub/articles/{aid}` | `get_article` |  |
| PUT | `/api/v1/hub/articles/{aid}` | `update_article` |  |
| GET | `/api/v1/hub/articles/{aid}/ai-image-prompts` | `ai_image_prompts` |  |
| GET | `/api/v1/hub/articles/{aid}/ai-outline` | `ai_outline` |  |
| POST | `/api/v1/hub/articles/{aid}/ai-polish` | `ai_polish` |  |
| POST | `/api/v1/hub/articles/{aid}/ai-rewrite` | `ai_rewrite` |  |
| GET | `/api/v1/hub/articles/{aid}/ai-seo` | `ai_seo` |  |
| POST | `/api/v1/hub/articles/{aid}/ai-translate` | `ai_translate` |  |
| POST | `/api/v1/hub/articles/{aid}/clone` | `article_clone` |  |
| GET | `/api/v1/hub/articles/{aid}/export` | `article_export` | 导出为带 YAML front-matter 的 Markdown（Hexo/Hugo/Obsidian 可直接用）。 |
| POST | `/api/v1/hub/articles/{aid}/publish` | `publish` | 异步发布：提交到统一任务引擎，立即返回 task_id。 |
| POST | `/api/v1/hub/articles/{aid}/qa` | `article_qa` |  |
| POST | `/api/v1/hub/articles/{aid}/update` | `update` | 异步原地更新：提交任务，轮询 GET /tasks/{task_id}。 |
| GET | `/api/v1/hub/articles/{aid}/versions` | `versions_list` |  |
| GET | `/api/v1/hub/articles/{aid}/versions/diff` | `versions_diff` |  |
| GET | `/api/v1/hub/articles/{aid}/versions/{vid}` | `versions_get` |  |
| POST | `/api/v1/hub/articles/{aid}/versions/{vid}/rollback` | `versions_rollback` |  |
| POST | `/api/v1/hub/browser/{platform}/fetch` | `browser_fetch` | 带平台登录态抓取页面正文（登录墙后的内容也能拿）。 |
| POST | `/api/v1/hub/browser/{platform}/screenshot` | `browser_screenshot` | 带登录态打开页面截图，落盘 data/exports/screenshots/。 |
| GET | `/api/v1/hub/events/stream` | `events_stream` | SSE 实时推送任务/发布/文章事件。前端用 EventSource 连。 |
| GET | `/api/v1/hub/health` | `health` | 桌面版 Tauri sidecar 健康检查端点。 |
| GET | `/api/v1/hub/jobs` | `jobs` |  |
| GET | `/api/v1/hub/mcp/bridge/status` | `mcp_bridge_status` | 已配置的外部 MCP Server 概览 + 能力覆盖情况。 |
| POST | `/api/v1/hub/mcp/bridge/{server}/call` | `mcp_bridge_call` | 调用外部 MCP Server 的工具（仅白名单内工具）。 |
| GET | `/api/v1/hub/mcp/bridge/{server}/tools` | `mcp_bridge_tools` | 列出某个外部 server 实际提供的工具（配白名单前先看这个）。 |
| GET | `/api/v1/hub/media` | `media_list` |  |
| POST | `/api/v1/hub/media/ingest` | `media_ingest` | 把远程图片抓取入库（SSRF 防护 + 大小上限），返回稳定 URL。 |
| GET | `/api/v1/hub/media/orphans` | `media_orphans` | 未被任何文章引用的媒体资产（预览用，不删）。 |
| POST | `/api/v1/hub/media/orphans/purge` | `media_purge_orphans` | 清理未引用的媒体资产。 |
| GET | `/api/v1/hub/media/stats` | `media_stats` | 媒体库状态 + 对外地址来源（排查"为什么图片没被改写"）。 |
| POST | `/api/v1/hub/media/upload` | `media_upload` | 上传图片入库（内容寻址去重）。返回稳定 URL。 |
| GET | `/api/v1/hub/media/{name}` | `media_file` | 本地托管的图片（内容寻址 → 可永久缓存）。 |
| GET | `/api/v1/hub/metrics` | `metrics` | 实时指标。`format=json`（默认）给调试用结构化快照； |
| GET | `/api/v1/hub/notifications` | `notifications_list` |  |
| POST | `/api/v1/hub/onboarding/check` | `onboarding_check` |  |
| POST | `/api/v1/hub/onboarding/init` | `onboarding_init` | 创建 ``profiles/<name>/``，并把选中模板渲染成个人 SOP。 |
| POST | `/api/v1/hub/onboarding/platforms` | `onboarding_add_platforms` | 给已有档案追加平台，不重写账号与主线。 |
| POST | `/api/v1/hub/onboarding/rerender` | `onboarding_rerender` | 只重渲染个人 SOP，不重写 profile.yaml（账号配置不会被冲掉）。 |
| GET | `/api/v1/hub/onboarding/state` | `onboarding_state` |  |
| GET | `/api/v1/hub/pending-human` | `pending_human` | 需要人工处理的发布实例（如掘金草稿等人点"确定并发布"）。 |
| POST | `/api/v1/hub/platform-cooldowns/clear` | `clear_cooldowns` | 手动解除平台限流冷却（平台侧确认恢复后用）。 |
| GET | `/api/v1/hub/platforms` | `platforms` | 平台清单 + 代码级能力矩阵。 |
| GET | `/api/v1/hub/publications` | `publications` |  |
| POST | `/api/v1/hub/publications/{pub_id}/verify` | `verify_publication` | 对一条已发布记录重新做回读验证（0.15.0）。 |
| POST | `/api/v1/hub/qa/analyze` | `qa_analyze` | 正文质检。JSON body 与 query 参数两种调用方式都支持。 |
| POST | `/api/v1/hub/refresh/{platform}` | `refresh` | 异步抓取平台文章入库。limit 传入 TaskManager，避免被 dispatch 硬编码为 50。 |
| GET | `/api/v1/hub/schedules` | `schedules_list` |  |
| POST | `/api/v1/hub/schedules` | `schedules_create` |  |
| DELETE | `/api/v1/hub/schedules/{sid}` | `schedules_delete` |  |
| GET | `/api/v1/hub/schedules/{sid}` | `schedules_get` |  |
| PUT | `/api/v1/hub/schedules/{sid}` | `schedules_update` |  |
| POST | `/api/v1/hub/schedules/{sid}/pause` | `schedules_pause` |  |
| POST | `/api/v1/hub/schedules/{sid}/resume` | `schedules_resume` |  |
| POST | `/api/v1/hub/schedules/{sid}/trigger` | `schedules_trigger` | 手动立即投递一次，不改调度计划。 |
| GET | `/api/v1/hub/status` | `status` |  |
| POST | `/api/v1/hub/sync/pending` | `sync_pending` | 异步同步扇出：把所有待更新实例提交一个 sync 任务。 |
| GET | `/api/v1/hub/tags` | `tags_list` |  |
| POST | `/api/v1/hub/tags/alias` | `tags_alias` | 添加标签别名：alias 出现时自动替换成 canonical。 |
| GET | `/api/v1/hub/tags/clusters` | `tags_clusters` | 近似重复标签簇：同义词治理的候选清单（一键合并前先看这个）。 |
| POST | `/api/v1/hub/tags/merge` | `tags_merge` | 合并标签：_from -> to（_from 被合并消失，to 保留）。 |
| POST | `/api/v1/hub/tags/rename` | `tags_rename` |  |
| POST | `/api/v1/hub/tags/suggest` | `tags_suggest` | 根据标题+正文推荐 3-5 个标签。JSON body 与 query 参数都支持。 |
| POST | `/api/v1/hub/tags/sync` | `tags_sync` | 从 articles 重建标签统计。 |
| GET | `/api/v1/hub/tags/trending` | `tags_trending` |  |
| GET | `/api/v1/hub/tasks` | `tasks_list` | 任务列表：按 kind/status 过滤，默认返回最近 50 条。 |
| GET | `/api/v1/hub/tasks/page` | `tasks_page` | 分页视图：返回 {items,total,has_more}。保持 /tasks 的原样返回不变。 |
| GET | `/api/v1/hub/tasks/{task_id}` | `tasks_detail` | 查询任意任务状态：pending / running / ok / failed / waiting_human。 |
| POST | `/api/v1/hub/tasks/{task_id}/resume` | `tasks_resume` | 恢复 waiting_human 任务：approved=true 重新执行；false 标记放弃。 |
| GET | `/api/v1/hub/webhooks` | `webhooks_list` |  |
| POST | `/api/v1/hub/webhooks` | `webhooks_create` |  |
| DELETE | `/api/v1/hub/webhooks/{wid}` | `webhooks_delete` |  |
| PUT | `/api/v1/hub/webhooks/{wid}` | `webhooks_update` |  |
| POST | `/api/v1/hub/webhooks/{wid}/test` | `webhooks_test` | 发送测试事件到指定 webhook。 |

## 5. MCP 工具

共 33 个，定义在 `mcp_server.py`。

| Tool | 参数 | 说明 |
|---|---|---|
| `ai_image_prompts` | article_id, n | 根据文章内容生成 n 个英文文生图 prompt（兼容 SDXL/Flux/DALL·E）。 |
| `ai_polish_article` | article_id, model | AI 润色文章：修错别字、顺语句、统一代码块语言标识。 |
| `ai_rewrite_article` | article_id, instruction, model | 按指令 AI 改写已有文章（如"更口语""补充踩坑章节""压缩到 800 字"）。 |
| `ai_translate_article` | article_id, target_lang, model | 翻译文章到目标语言（en/ja/ko/fr/de），保留代码块不动。 |
| `ai_write_article` | topic, words, tags_hint, model, publish_to, style | 让 AI 写一篇技术文章，自动入库。可选直接发布到指定平台。 |
| `analyze_text` | content_md, title, summary, tags | 对任意文本（不保存入库）运行内容质检。 |
| `browser_fetch` | platform, url, account | 带平台登录态的内置浏览器抓取页面：标题 + 正文（登录墙后的内容也能拿）。 |
| `browser_screenshot` | platform, url, full_page, account | 带平台登录态打开页面截图，落盘 data/exports/screenshots/，返回路径。 |
| `create_article` | title, content_md, summary, tags | 新建一篇文章，返回 {id, title}。 |
| `external_mcp_call` | server, tool, arguments | 调用外部 MCP Server 的工具（仅白名单内）。 |
| `external_mcp_status` | — | 已配置的外部 MCP Server（Playwright / fetch / filesystem 等）状态与能力覆盖。 |
| `external_mcp_tools` | server | 列出一个外部 MCP Server 实际提供的工具（配白名单前先看）。 |
| `get_article` | article_id | 按 ID 获取文章完整字段（标题/正文/摘要/标签/状态）。 |
| `get_platform_skill` | platform, profile | 登录后先读这张平台技能卡：内容规则、发布步骤、限制与验收标准。 |
| `get_task` | task_id | 查询任务状态（pending/running/ok/failed/waiting_human）。 |
| `import_from_url` | url, tags | 从网页抓取正文导入为文章（trafilatura 提取，需公网可访问）。 |
| `import_markdown` | path, tags | 导入本地 Markdown 文件，自动提取 front-matter 元数据。 |
| `ingest_image` | url | 把远程图片抓进本地媒体库，返回可长期引用的稳定 URL。 |
| `list_articles` | status, limit | 列出文章列表。status 可选：draft/published/review/archived。 |
| `list_media` | limit | 列出已入库的图片资产（内容寻址去重）与统计。 |
| `list_platforms` | — | 列出所有可用平台、能力、是否有技能卡和是否推荐。 |
| `list_providers` | — | 列出所有已配置的 AI Provider + 可用模型 + 价格级别。 |
| `list_tags` | limit | 列出热门标签及其出现次数。 |
| `publish_article` | article_id, platforms, draft_only, account, human_confirmed | 异步发布文章到指定平台，返回 task_id。用 get_task 查询进度。 |
| `quality_check` | article_id | 对文章运行内容质检：可读性评分 + SEO 评分 + 库内重复度 + 改进建议。 |
| `resume_task` | task_id, approved | 恢复等待人工的任务。approved=True 重跑；False 标记放弃。 |
| `search_articles` | keyword, limit | 全文检索文章库（FTS5 相关度排序），返回匹配文章列表。 |
| `suggest_tags` | title, content_md | 根据标题 + 正文推荐 3-5 个标签。 |
| `update_article` | article_id, title, content_md, summary, tags, status | 更新文章的任意字段。内容变更后会自动 pend 已发布平台的同步。 |
| `update_remote_article` | article_id, platforms, account | 原地更新（不是重发）：打开已发布平台的编辑页改内容并保存。 |
| `wechatsync_platforms` | — | 经外部执行器列出 Wechatsync 支持的平台（29+，可超出内置 10 个）。 |
| `wechatsync_publish` | article_id, platforms, title, cover, dry_run | 把文章库里的一篇交给外部执行器 Wechatsync 分发到多个平台。 |
| `wechatsync_status` | — | 查询外部执行器 Wechatsync 的就绪状态（是否安装、是否配 token）。 |

## 6. 平台适配器与能力矩阵

能力为 `true` 才算真的支持；未声明一律 false（防假成功）。

| 平台 | 浏览器 | cover | draft | hosted_media | list | publish | question | tags | update | 选择器版本 |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| `51cto` 51CTO博客 | 否 | · | ✅ | ✅ | ✅ | ✅ | · | ✅ | ✅ | 2026-09 |
| `bilibili` B站专栏 | 是 | · | ✅ | · | · | ✅ | · | ✅ | ✅ | 2026-09 |
| `cnblogs` 博客园 | 否 | · | ✅ | ✅ | ✅ | ✅ | · | ✅ | ✅ | 2026-09 |
| `csdn` CSDN | 是 | ✅ | ✅ | · | ✅ | ✅ | · | ✅ | ✅ | 2026-09 |
| `devto` Dev.to | 否 | ✅ | ✅ | ✅ | ✅ | ✅ | · | ✅ | ✅ | — |
| `github` GitHub Pages | 否 | · | · | ✅ | ✅ | ✅ | · | ✅ | ✅ | — |
| `juejin` 稀土掘金 | 是 | ✅ | ✅ | · | ✅ | ✅ | · | ✅ | ✅ | 2026-09 |
| `metaweblog` 自建博客 | 否 | · | ✅ | ✅ | ✅ | ✅ | · | ✅ | ✅ | — |
| `oschina` 开源中国 | 是 | · | ✅ | · | · | ✅ | · | · | · | 2026-09 |
| `segmentfault` 思否 | 是 | · | ✅ | · | · | ✅ | · | ✅ | ✅ | 2026-09 |
| `telegraph` Telegraph | 否 | · | · | ✅ | ✅ | ✅ | · | · | ✅ | — |
| `toutiao` 头条号 | 是 | · | ✅ | · | · | ✅ | · | · | · | 2026-09 |
| `wechat` 微信公众号 | 否 | · | ✅ | · | ✅ | ✅ | · | · | ✅ | — |
| `xiaohongshu` 小红书 | 是 | · | ✅ | · | · | ✅ | · | · | · | 2026-10-30 (未验证) |
| `zhihu` 知乎 | 是 | · | ✅ | · | · | ✅ | ✅ | ✅ | ✅ | 2026-09 |

## 7. 数据库

| 表 | 列 |
|---|---|
| `accounts` | `id`, `platform`, `name`, `profile_dir`, `status`, `last_check` |
| `articles` | `id`, `title`, `content_md`, `summary`, `tags`, `cover`, `status`, `source`, `ai_model`, `origin_url`, `ext`, `created_at`, `updated_at` |
| `publications` | `id`, `article_id`, `platform`, `account`, `post_id`, `post_url`, `edit_url`, `status`, `draft_only`, `stats`, `last_error`, `content_hash`, `published_at`, `updated_at`, `verify_state`, `verified_at`, `verify_detail` |
| `jobs` | `id`, `type`, `article_id`, `platform`, `status`, `message`, `created_at`, `finished_at` |
| `meta` | `key`, `value` |
| `tasks` | `id`, `task_id`, `kind`, `article_id`, `platforms`, `account`, `draft_only`, `status`, `message`, `result`, `error`, `attempts`, `created_at`, `updated_at`, `finished_at` |

全文检索：`articles_fts`（trigram 分词）

索引 7 个；迁移版本 3 段（`meta.schema_version` + `MIGRATIONS`）。

## 8. 测试分布

`test_*` 函数 574 个，测试代码 8695 行。parametrize 展开后的真实用例数：`uv run pytest --collect-only -q`。

| 文件 | 用例函数 | 行数 |
|---|---|---|
| `backed/tests/test_0120_automation.py` | 20 | 318 |
| `backed/tests/test_ai_readiness.py` | 9 | 87 |
| `backed/tests/test_api_integration.py` | 13 | 279 |
| `backed/tests/test_app.py` | 4 | 85 |
| `backed/tests/test_article_delete.py` | 4 | 79 |
| `backed/tests/test_article_events.py` | 3 | 50 |
| `backed/tests/test_audit_20261027.py` | 8 | 132 |
| `backed/tests/test_auth_token_bootstrap.py` | 5 | 60 |
| `backed/tests/test_backup_data.py` | 16 | 255 |
| `backed/tests/test_capability_upgrade.py` | 71 | 861 |
| `backed/tests/test_config_migration_review.py` | 1 | 15 |
| `backed/tests/test_content_qa.py` | 11 | 112 |
| `backed/tests/test_csdn_publish_settings.py` | 14 | 245 |
| `backed/tests/test_db.py` | 15 | 215 |
| `backed/tests/test_debt_round2.py` | 13 | 254 |
| `backed/tests/test_debt_round2_paging.py` | 7 | 126 |
| `backed/tests/test_docs_links.py` | 6 | 107 |
| `backed/tests/test_events.py` | 14 | 161 |
| `backed/tests/test_export.py` | 5 | 58 |
| `backed/tests/test_gate.py` | 37 | 359 |
| `backed/tests/test_health_auth_boundary.py` | 3 | 48 |
| `backed/tests/test_human_click.py` | 15 | 201 |
| `backed/tests/test_input_validation.py` | 5 | 49 |
| `backed/tests/test_mcp_wechatsync.py` | 21 | 293 |
| `backed/tests/test_media_orphans.py` | 5 | 78 |
| `backed/tests/test_module_imports.py` | 6 | 131 |
| `backed/tests/test_onboarding.py` | 16 | 195 |
| `backed/tests/test_onboarding_api.py` | 6 | 131 |
| `backed/tests/test_platform_skills.py` | 4 | 42 |
| `backed/tests/test_publish_modes.py` | 10 | 299 |
| `backed/tests/test_publish_readback.py` | 14 | 211 |
| `backed/tests/test_rate_limiter.py` | 17 | 163 |
| `backed/tests/test_real_publish_and_ai_config.py` | 15 | 314 |
| `backed/tests/test_review_20261012.py` | 21 | 377 |
| `backed/tests/test_review_20261014.py` | 8 | 135 |
| `backed/tests/test_review_shutdown_security.py` | 3 | 48 |
| `backed/tests/test_router_info.py` | 2 | 25 |
| `backed/tests/test_schedule_validation.py` | 4 | 74 |
| `backed/tests/test_scheduler.py` | 22 | 253 |
| `backed/tests/test_security_headers.py` | 3 | 38 |
| `backed/tests/test_security_regression.py` | 15 | 265 |
| `backed/tests/test_sse_replay.py` | 7 | 90 |
| `backed/tests/test_tag_suggest.py` | 5 | 49 |
| `backed/tests/test_tags.py` | 14 | 174 |
| `backed/tests/test_task_failure_propagation.py` | 7 | 74 |
| `backed/tests/test_task_pending_user.py` | 4 | 84 |
| `backed/tests/test_tasks.py` | 11 | 196 |
| `backed/tests/test_title_evidence.py` | 6 | 73 |
| `backed/tests/test_url_safety_deadline_rebinding.py` | 6 | 165 |
| `backed/tests/test_url_safety_pinning.py` | 5 | 105 |
| `backed/tests/test_versions.py` | 11 | 146 |
| `backed/tests/test_zhihu_answer_flow.py` | 7 | 161 |

## 9. CLI

- `add-platforms` — 给已有档案追加平台，不重写账号与主线
- `ai-outline` — AI 提炼文章大纲
- `ai-polish` — AI 润色文章
- `ai-prompts` — AI 生成文章配图 prompt
- `ai-rewrite` — AI 改写已有文章
- `ai-seo` — AI 生成 SEO 元数据
- `ai-translate` — AI 翻译文章
- `ai-write` — AI 写一篇并入库
- `bootstrap-cnblogs` — 浏览器登录博客园并自动抠出 MetaWeblog 令牌写进 config.json
- `check` — 检查平台登录态
- `clone` — 克隆文章（标题自动加「副本）」）
- `create` — 新建文章
- `delete` — 删除文章（平台侧已发布副本不受影响）
- `diagnose` — 查看平台接入说明与验证码处理方式
- `edit` — 修改文章标题/正文/标签/摘要/状态
- `export` — 导出文章为带 front-matter 的 Markdown
- `import-md` — 导入本地 Markdown
- `init` — 初始化个人档案：profiles/<name>/ + 渲染 playbooks
- `list` — 列出文章（默认按更新时间倒序）
- `login` — 扫码/过验证登录（首次必须，之后长期有效）
- `logout` — 清除登录态（删 profile+cookie 快照，需重新扫码）
- `publish` — 发布到平台（逗号分隔，如 juejin,csdn）
- `refresh` — 抓取平台上已有文章列表入库
- `rollback` — 回滚文章到指定版本
- `schedule-add` — 添加定时发布任务
- `schedule-del` — 删除定时任务
- `schedule-list` — 列出全部定时任务
- `schedule-trigger` — 手动立即执行一次定时任务
- `search` — 全文检索文章（SQLite FTS5）
- `serve` — 启动 REST API 服务（复用 api.hub 的 FastAPI app）
- `show` — 查看单篇文章（正文默认打印）
- `solve-captcha` — 打开页面就地处理验证码（半自动+人工）
- `status` — 中台总览：文章数、发布数、待同步数、账号状态
- `sync` — 把所有改动同步到已发布平台
- `tag-rename` — 重命名标签
- `tag-sync` — 从文章重建标签统计
- `tags` — 列出热门标签
- `update` — 原地更新已发布文章
- `versions` — 列出文章的版本历史

## 10. 配置键（config.example.json）

顶层：`AI_API_KEY`、`AI_BASE_URL`、`AI_DIRECT_PUBLISH`、`AI_MODEL`、`MCP_BRIDGE`、`REVIEW_MODEL`、`WRITING_STYLE_FILE`、`api_token`、`platforms`

平台段：`51cto`、`_平台能力矩阵`、`_浏览器类平台_列表`、`_浏览器类平台_说明`、`cnblogs`、`devto`、`github`、`metaweblog`、`wechat`

运行时真正读配置的是 `service/publishing/db.py:config_file()`（env > 数据根 > 旧位置），不是 `config_unified.py` 那套 Pydantic 类。
