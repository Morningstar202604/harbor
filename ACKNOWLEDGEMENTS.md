# Acknowledgements

**English** · [简体中文](ACKNOWLEDGEMENTS.zh-CN.md)

Harbor is a small self-hosted project built on a lot of open-source work. This page names the direct dependencies and optional MCP servers that shape the product. It is not a full transitive-dependency dump; exact versions live in `backed/uv.lock`, `web/pnpm-lock.yaml` and `web/src-tauri/Cargo.lock`.

## MCP and publishing

Harbor runs its own MCP server. The servers below are optional external backends and are never bundled; the bridge starts one only when a user configures it.

| Project | What it does here | License |
|---|---|---|
| [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk) | MCP server transports, tool schemas, and the client side of the bridge | MIT |
| [Playwright MCP](https://github.com/microsoft/playwright-mcp) | Optional browser backend from Microsoft | Apache-2.0 |
| [MCP Fetch](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | Optional fetch and robots-aware retrieval | MIT |
| [MCP Filesystem](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | Optional batch file reads and writes | MIT |
| [Wechatsync CLI](https://github.com/wechatsync/Wechatsync) | Optional external multi-platform executor behind the `wechatsync_*` tools | MIT |

## Core runtime

| Project | What it does here | License |
|---|---|---|
| [FastAPI](https://github.com/fastapi/fastapi) | HTTP API | MIT |
| [Starlette](https://github.com/encode/starlette) | ASGI foundations | BSD-3-Clause |
| [Uvicorn](https://github.com/encode/uvicorn) | Local server | BSD-3-Clause |
| [Pydantic](https://github.com/pydantic/pydantic) | Schemas and settings | MIT |
| [Patchright](https://github.com/Kaliiiiiiiiii-Vinyzu/patchright-python) | Browser login and publishing; a hardened Playwright fork | Apache-2.0 |
| [Playwright](https://github.com/microsoft/playwright) | Browser automation foundation | Apache-2.0 |
| [SQLite](https://sqlite.org/) | Local articles, tasks and publication history | Public domain |

## Content and data

| Project | What it does here | License |
|---|---|---|
| [trafilatura](https://github.com/adbar/trafilatura) | Article text extraction | Apache-2.0 |
| [jieba](https://github.com/fxsjy/jieba) | Chinese text segmentation | MIT |
| [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) | Fuzzy matching for duplicate and similarity checks | MIT |
| [PyYAML](https://github.com/yaml/pyyaml) | Profile and configuration files | MIT |
| [python-frontmatter](https://github.com/eyeseast/python-frontmatter) | Markdown metadata | MIT |
| [Python-Markdown](https://github.com/Python-Markdown/markdown) | Markdown rendering | BSD-3-Clause |
| [markdown-it-py](https://github.com/executablebooks/markdown-it-py) | Markdown parsing | MIT |
| [Pillow](https://github.com/python-pillow/Pillow) | Image handling | MIT-CMU |
| [Telegraph](https://github.com/python273/telegraph) | Telegraph publishing | MIT |

## Security, scheduling and HTTP

| Project | What it does here | License |
|---|---|---|
| [cryptography](https://github.com/pyca/cryptography) | Credential encryption | Apache-2.0 OR BSD-3-Clause |
| [PyJWT](https://github.com/jpadilla/pyjwt) | Token signing and verification | MIT |
| [bcrypt](https://github.com/pyca/bcrypt) | Password hashing | Apache-2.0 |
| [croniter](https://github.com/pallets-eco/croniter) | Cron schedules | MIT |
| [tenacity](https://github.com/jd/tenacity) | Retry handling | Apache-2.0 |
| [prometheus-client](https://github.com/prometheus/client_python) | Metrics | Apache-2.0 |
| [pyahocorasick](https://github.com/WojciechMula/pyahocorasick) | Keyword matching | BSD-3-Clause / Public Domain |
| [requests](https://github.com/psf/requests) | Platform HTTP calls | Apache-2.0 |
| [Click](https://github.com/pallets/click) | Command-line interface | BSD-3-Clause |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Local environment configuration | BSD-3-Clause |
| [python-multipart](https://github.com/Kludex/python-multipart) | File uploads | Apache-2.0 |

## Web interface

| Project | What it does here | License |
|---|---|---|
| [Vue 3](https://github.com/vuejs/core) | User interface | MIT |
| [Element Plus](https://github.com/element-plus/element-plus) | UI components | MIT |
| [Pinia](https://github.com/vuejs/pinia) | State management | MIT |
| [ECharts](https://github.com/apache/echarts) | Charts | Apache-2.0 |
| [md-editor-v3](https://github.com/imzbf/md-editor-v3) | Markdown editor | MIT |
| [markdown-it](https://github.com/markdown-it/markdown-it) | Markdown preview | MIT |
| [Axios](https://github.com/axios/axios) | API client | MIT |

## Desktop and build

| Project | What it does here | License |
|---|---|---|
| [Tauri](https://github.com/tauri-apps/tauri) | Desktop shell | MIT OR Apache-2.0 |
| [Rust](https://www.rust-lang.org/) | Desktop runtime | MIT OR Apache-2.0 |
| [Serde](https://github.com/serde-rs/serde) | IPC serialization | MIT OR Apache-2.0 |
| [Tokio](https://github.com/tokio-rs/tokio) | Async runtime | MIT |
| [Reqwest](https://github.com/seanmonstar/reqwest) | Desktop HTTP client | MIT OR Apache-2.0 |
| [uv](https://github.com/astral-sh/uv) | Python environment and dependency management | Apache-2.0 OR MIT |
| [pnpm](https://github.com/pnpm/pnpm) | JavaScript package management | MIT |
| [Vite](https://github.com/vitejs/vite) | Frontend build | MIT |
| [Vitest](https://github.com/vitest-dev/vitest) | Frontend tests | MIT |
| [ESLint](https://github.com/eslint/eslint) | Frontend lint | MIT |

CI also uses [GitHub Actions](https://github.com/actions) and the open-source `actions/checkout`, `actions/setup-python`, `actions/setup-node`, `pnpm/action-setup`, `dtolnay/rust-toolchain`, `actions/cache` and `actions/upload-artifact` actions.

If something is missing or misattributed, please open an issue. The fix is a one-line change, and the credit matters.
