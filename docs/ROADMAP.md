# Roadmap

Living document. Reviewed monthly; every item states the user-visible outcome, not the
implementation. See [`VERSIONING.md`](VERSIONING.md) for how a version gets cut.

Legend: `[x]` shipped · `[ ]` planned · `[~]` in progress · `[!]` blocked

---

## Shipped

### 0.15.1 — post-login management space (current)

Logged in, then what? The settings UI now covers the files users previously had to hand-edit.

- [x] Content profile tab: switch active profile, edit mainline / voice / quotas / windows,
      advanced YAML with validation and backup
- [x] Personal SOP: view, edit (marked `customized`), reset to template, platform add/remove
- [x] API platform credentials form with masked secrets and atomic writes; no hand-editing `config.json`
- [x] Publish rail ready-count fixed to real login state; empty-body guard
- [x] Multi-profile active marker used by MCP `get_platform_skill`

### 0.15.0 — read-back verification

"Success" now means the copy exists on the platform, not that an API returned 201.

- [x] Post-publish read-back for every publication record
      (`publications.verify_state`: verified / failed / unsupported / unverified)
- [x] Protocol read-back: Dev.to (article API) and GitHub Pages (contents API)
- [x] Page read-back: open the published URL, compare title and body against the source
- [x] `POST /publications/{id}/verify` to re-check on demand
- [x] Publish centre shows the read-back state with a "re-check" action
- [x] Real publish verification script + dated record in `docs/verification/`
- [x] CI: docker-smoke and Windows desktop-build jobs added
- [x] MSI + NSIS installers built, installed, launched and uninstalled on Windows

Four real defects were found by running this against a live account, none of which any
mock had caught: future-dated front-matter silently dropped by Jekyll, read-back
recomputing the URL instead of reusing the published one, site suffixes breaking title
comparison, and the editor-only "append detection" rule rejecting valid published pages.

### 0.14.0 — full-loop verification

Every item below was driven by running the product, not by reading the code.

- [x] Rest and CLI coverage: 91 REST endpoints, 33 MCP tools, 35 CLI commands exercised
- [x] SSE reliability: monotonic event ids, 256-event replay ring, `Last-Event-ID` gap
      fill, `resync` when the gap exceeds the window
- [x] Article CRUD now emits SSE events (previously only tasks/publish did)
- [x] MCP `streamable-http` transport (supersedes HTTP+SSE since 2025-03-26)
- [x] Markdown export with YAML front-matter (API + CLI + editor menu)
- [x] Offline tag suggestions with synonym de-duplication
- [x] Real Prometheus histograms (were all zeros)
- [x] Security headers on by default; verified in a real browser with zero CSP violations
- [x] Single-file executable built and smoke-tested (7/7 checks)
- [x] Defect sweep: `/api/info` empty routes, fake AI-ready state, hardcoded editor
      theme, PIL excluded from the bundle, webhook test false success

### 0.12.x — hardening

- [x] Network boundary: public-IP validation, connection pinning, redirect revalidation
- [x] Browser fetch/screenshot restored with Chromium DNS pinning (was disabled)
- [x] MCP SSE loopback default, remote requires bearer token
- [x] Graceful shutdown ordering with connection preservation on failure
- [x] Unified data root for config, database, media, profiles
- [x] Documentation claims aligned with verified behaviour

### 0.10 – 0.11 — platform coverage

- [x] WeChat, GitHub Pages, Dev.to
- [x] Telegraph, Xiaohongshu
- [x] 15 adapters with capability matrix

### 0.8 – 0.9 — foundation

- [x] Media pipeline with content-addressed dedupe
- [x] SQLite FTS5 full-text search
- [x] Platform rate-limit cooldowns
- [x] External MCP bridge
- [x] Service split into mixins

---

## Next

一个版本号只出现一次；`Shipped` 里是已完成的历史，`Next` 是还没做的。

### 0.16.0 — 工程收敛（不新增用户可见功能）

先补齐"看得懂、改得动"，再谈功能。验收：六处版本一致、`/docs` 版本等于清单版本、
测试全绿、CI 五 job 绿、`sys.path.insert` 只剩测试与脚本。

- [ ] 文档与代码对齐：AGENT.md / ARCHITECTURE.md 的版本与 15 个适配器；ROADMAP 单一版本号
- [ ] 配置收敛：`config_unified.py` 删掉 Redis / 连接池 / JWT / 密码策略等死字段；CORS 默认收紧
- [ ] 包结构：`backed` → `backend`，顶层散包收成单根包（行为不变，测试兜底）
- [ ] 依赖自动化：修好 Dependabot 或改月度手更（Pillow 分叉目前每天红）
- [ ] 适配器契约测试：segmentfault / telegraph / 51cto / 小红书（当前测试零引用）

### 0.17.0 — 并发与失败取证

"一次写作发 15 平台"不该是分钟级排队。

- [ ] 平台级子任务 + 有界并发（同账号串行、跨账号并行），人工延迟只约束同账号
- [ ] 发布失败落 Playwright trace + 截图 + DOM 快照，按 task_id 归档
- [ ] `adapter_probe` 进 CI：选择器漂移在合并前就红
- [ ] 前端 eslint warning 清零，`--max-warnings` 999 → 0

### 0.18.0 — 编辑工作流

- [ ] 发布前 diff 预览：同步前展示每个平台会改什么
- [ ] 批量操作：按筛选集重打标签、重排期、重发
- [ ] RSS / JSON Feed：文章库可订阅，不只是可导出

---

## Backlog (unscheduled)

- [ ] Additional adapters: 只扩国内平台（掘金 API channel 等）；国外平台按既定策略不再新增
- [ ] Image generation integration for cover art
- [ ] Multi-user mode with per-account permissions
- [ ] Webhook delivery retry with exponential backoff and dead-letter queue
- [ ] Content calendar heatmap

---

## Explicitly out of scope

| Item | Why not |
|---|---|
| SaaS hosting | The product's value is self-hosting; a hosted tier would fork the architecture |
| CAPTCHA solving | Account-ban risk and ToS violation; the product pauses for a human instead |
| Bulk scraping of arbitrary sites | Turns a publishing tool into a scraping proxy; SSRF surface never closes |
| Plugin marketplace | Adds a supply-chain risk surface without solving a user problem yet |
