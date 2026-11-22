# Copilot / 其他 AI 助手的仓库说明

本仓库的智能体说明以根目录 [`AGENTS.md`](../AGENTS.md) 为准；机器抽取的事实清单见
[`docs/agent/CONTEXT.md`](../docs/agent/CONTEXT.md)。

要点：单机 FastAPI + SQLite + Patchright；路由只在 `backed/api/hub.py` 聚合；SQL 只在
`backed/service/publishing/db.py`；Playwright 只能经 `browser_thread_run`；
新增平台必须显式声明 `capabilities`；任何"发布成功"必须有回读证据。
