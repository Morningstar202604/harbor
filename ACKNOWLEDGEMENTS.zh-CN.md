# 致谢

[English](ACKNOWLEDGEMENTS.md) · **简体中文**

Harbor 是个小型的自托管项目，建立在大量开源工作上。这里只列会直接影响产品形态的直接依赖和可选 MCP Server，不做传递依赖的全量清单；精确版本见 `backed/uv.lock`、`web/pnpm-lock.yaml` 和 `web/src-tauri/Cargo.lock`。

## MCP 与发布

Harbor 自己就是一个 MCP Server。下面这些是可选的外部后端，不会被捆绑进项目；只有用户主动配置后，桥接层才会启动对应进程。

| 项目 | 在这里做什么 | 许可证 |
|---|---|---|
| [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) | MCP Server 的传输、工具 schema，以及桥接层的客户端 | MIT |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | 微软提供的可选浏览器后端 | Apache-2.0 |
| [MCP Fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | 可选的网页抓取，带 robots 约束 | MIT |
| [MCP Filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | 可选的批量文件读写 | MIT |
| [Wechatsync CLI](https://github.com/wechatsync/Wechatsync) | `wechatsync_*` 工具背后的可选外部多平台执行器 | MIT |

## 核心运行时

| 项目 | 在这里做什么 | 许可证 |
|---|---|---|
| [FastAPI](https://github.com/fastapi/fastapi) | HTTP API | MIT |
| [Starlette](https://github.com/encode/starlette) | ASGI 基础 | BSD-3-Clause |
| [Uvicorn](https://github.com/encode/uvicorn) | 本地服务 | BSD-3-Clause |
| [Pydantic](https://github.com/pydantic/pydantic) | 数据模型与配置 | MIT |
| [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) | 浏览器登录与发布；Playwright 的加固分支 | Apache-2.0 |
| [Playwright](https://github.com/microsoft/playwright) | 浏览器自动化基础 | Apache-2.0 |
| [SQLite](https://sqlite.org/) | 本地文章、任务与发布历史 | Public domain |

## 内容与数据

| 项目 | 在这里做什么 | 许可证 |
|---|---|---|
| [trafilatura](https://github.com/adbar/trafilatura) | 网页正文提取 | Apache-2.0 |
| [jieba](https://github.com/fxsjy/jieba) | 中文分词 | MIT |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | 查重与相似度匹配 | MIT |
| [PyYAML](https://github.com/yaml/pyyaml) | 档案与配置文件 | MIT |
| [python-frontmatter](https://github.com/eyeseast/python-frontmatter) | Markdown 元数据 | MIT |
| [Python-Markdown](https://github.com/Python-Markdown/markdown) | Markdown 渲染 | BSD-3-Clause |
| [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | Markdown 解析 | MIT |
| [Pillow](https://github.com/python-pillow/Pillow) | 图片处理 | MIT-CMU |
| [Telegraph](https://github.com/python273/telegraph) | Telegraph 发布 | MIT |

## 安全、调度与网络

| 项目 | 在这里做什么 | 许可证 |
|---|---|---|
| [cryptography](https://github.com/pyca/cryptography) | 凭据加密 | Apache-2.0 OR BSD-3-Clause |
| [PyJWT](https://github.com/jpadilla/pyjwt) | Token 签发与校验 | MIT |
| [bcrypt](https://github.com/pyca/bcrypt) | 密码哈希 | Apache-2.0 |
| [croniter](https://github.com/pallets-eco/croniter) | Cron 调度 | MIT |
| [tenacity](https://github.com/jd/tenacity) | 重试处理 | Apache-2.0 |
| [prometheus-client](https://github.com/prometheus/client_python) | 指标暴露 | Apache-2.0 |
| [pyahocorasick](https://github.com/WojciechMula/pyahocorasick) | 关键词匹配 | BSD-3-Clause / Public Domain |
| [requests](https://github.com/psf/requests) | 平台 HTTP 请求 | Apache-2.0 |
| [Click](https://github.com/pallets/click) | 命令行入口 | BSD-3-Clause |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | 本地环境配置 | BSD-3-Clause |
| [python-multipart](https://github.com/Kludex/python-multipart) | 文件上传 | Apache-2.0 |

## Web 界面

| 项目 | 在这里做什么 | 许可证 |
|---|---|---|
| [Vue 3](https://github.com/vuejs/core) | 用户界面 | MIT |
| [Element Plus](https://github.com/element-plus/element-plus) | UI 组件 | MIT |
| [Pinia](https://github.com/vuejs/pinia) | 状态管理 | MIT |
| [ECharts](https://github.com/apache/echarts) | 图表 | Apache-2.0 |
| [md-editor-v3](https://github.com/imzbf/md-editor-v3) | Markdown 编辑器 | MIT |
| [markdown-it](https://github.com/markdown-it/markdown-it) | Markdown 预览 | MIT |
| [Axios](https://github.com/axios/axios) | API 客户端 | MIT |

## 桌面与构建

| 项目 | 在这里做什么 | 许可证 |
|---|---|---|
| [Tauri](https://github.com/tauri-apps/tauri) | 桌面壳 | MIT OR Apache-2.0 |
| [Rust](https://www.rust-lang.org/) | 桌面运行时 | MIT OR Apache-2.0 |
| [Serde](https://github.com/serde-rs/serde) | IPC 序列化 | MIT OR Apache-2.0 |
| [Tokio](https://github.com/tokio-rs/tokio) | 异步运行时 | MIT |
| [Reqwest](https://github.com/seanmonstar/reqwest) | 桌面 HTTP 客户端 | MIT OR Apache-2.0 |
| [uv](https://github.com/astral-sh/uv) | Python 环境与依赖管理 | Apache-2.0 OR MIT |
| [pnpm](https://github.com/pnpm/pnpm) | JavaScript 包管理 | MIT |
| [Vite](https://github.com/vitejs/vite) | 前端构建 | MIT |
| [Vitest](https://github.com/vitest-dev/vitest) | 前端测试 | MIT |
| [ESLint](https://github.com/eslint/eslint) | 前端 lint | MIT |

CI 还用到 [GitHub Actions](https://github.com/actions) 以及开源的 `actions/checkout`、`actions/setup-python`、`actions/setup-node`、`pnpm/action-setup`、`dtolnay/rust-toolchain`、`actions/cache`、`actions/upload-artifact`。

如果有遗漏或署名不对，欢迎开 issue。改一行就能修，署名这件事值得认真。
