#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成智能体上下文：docs/agent/CONTEXT.json + docs/agent/CONTEXT.md

原则：**事实从代码里读，不从散文里抄。**

- 路由：import ``api.hub.hub_router`` 的真实 APIRoute（路径/方法/处理函数/首行说明）
- MCP 工具：AST 解析 ``mcp_server.py`` 的 ``@mcp.tool()``
- 平台适配器：import 注册表 + ``capability_of()``（能力矩阵是代码级声明）
- 数据库：``db.SCHEMA`` 的 CREATE TABLE / 索引 / FTS
- 模块依赖：AST 解析 backed 内部 import 关系
- 测试分布、CLI 命令、配置键也一并抽取

用法::

    python scripts/gen_agent_context.py          # 写入 docs/agent/
    python scripts/gen_agent_context.py --check  # 只比对，漂了就退出 1（CI/门禁用）

输出不含时间戳，保证同一份代码生成同一份文件（--check 才有意义）。
"""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import Counter
from difflib import unified_diff
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BACKED = REPO / "backed"
OUT_DIR = REPO / "docs" / "agent"
OUT_JSON = OUT_DIR / "CONTEXT.json"
OUT_MD = OUT_DIR / "CONTEXT.md"

SKIP_PARTS = {".venv", "node_modules", "__pycache__", ".git", "dist", "build", "target"}


# --------------------------------------------------------------------------- #
# 通用
# --------------------------------------------------------------------------- #
def _py_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.py")
        if not (set(p.parts) & SKIP_PARTS)
    )


def _first_doc_line(node) -> str:
    doc = ast.get_docstring(node) or ""
    for line in doc.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line[:160]
    return ""


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


# --------------------------------------------------------------------------- #
# 模块与依赖图
# --------------------------------------------------------------------------- #
def scan_modules() -> tuple[list[dict], list[dict], dict]:
    files = [p for p in _py_files(BACKED) if "tests" not in p.relative_to(BACKED).parts]
    names: dict[str, Path] = {}
    for p in files:
        mod = ".".join(p.relative_to(BACKED).with_suffix("").parts)
        if mod.endswith(".__init__"):
            mod = mod[: -len(".__init__")]
        names[mod] = p

    modules: list[dict] = []
    for mod, path in sorted(names.items()):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        classes = [
            n.name for n in tree.body
            if isinstance(n, ast.ClassDef) and not n.name.startswith("_")
        ]
        funcs = [
            n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        loc = path.read_text(encoding="utf-8").count("\n") + 1
        modules.append({
            "module": mod,
            "path": _rel(path),
            "loc": loc,
            "doc": _first_doc_line(tree),
            "classes": classes,
            "functions": funcs,
        })

    edges: list[dict] = []
    known = set(names)
    for mod, path in sorted(names.items()):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        pkg_parts = mod.split(".")
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:  # 相对 import
                    base_parts = pkg_parts[: len(pkg_parts) - node.level]
                    base = ".".join(base_parts + ([base] if base else []))
                for alias in node.names:
                    targets.append(f"{base}.{alias.name}" if base else alias.name)
                if base:
                    targets.append(base)
            elif isinstance(node, ast.Import):
                targets.extend(a.name for a in node.names)
            for t in targets:
                t = t.strip(".")
                if t in known and t != mod:
                    edges.append({"src": mod, "dst": t})
                else:
                    prefix = ".".join(t.split(".")[:-1])
                    if prefix in known and prefix != mod:
                        edges.append({"src": mod, "dst": prefix})

    # 去重
    seen = set()
    uniq = []
    for e in edges:
        key = (e["src"], e["dst"])
        if key not in seen:
            seen.add(key)
            uniq.append(e)

    stats = {
        "module_count": len(modules),
        "total_loc": sum(m["loc"] for m in modules),
        "packages": dict(sorted(
            Counter(m["module"].split(".")[0] for m in modules).items()
        )),
        "top_fan_in": sorted(
            ((dst, sum(1 for e in uniq if e["dst"] == dst)) for dst in known),
            key=lambda x: (-x[1], x[0]),
        )[:12],
        "top_fan_out": sorted(
            ((src, sum(1 for e in uniq if e["src"] == src)) for src in known),
            key=lambda x: (-x[1], x[0]),
        )[:12],
    }
    stats["top_fan_in"] = [{"module": m, "importers": n} for m, n in stats["top_fan_in"] if n]
    stats["top_fan_out"] = [{"module": m, "deps": n} for m, n in stats["top_fan_out"] if n]
    return modules, uniq, stats


# --------------------------------------------------------------------------- #
# REST 路由
# --------------------------------------------------------------------------- #
def _walk_routes(router, prefix: str = ""):
    """递归展开 include_router。

    新版 FastAPI 把 include_router 存成 ``_IncludedRouter`` 节点，不再拍平成
    APIRoute；前缀挂在 ``include_context.prefix`` 上，子路由在
    ``include_context.included_router``。直接数 app.routes 会得到 0 条。
    """
    for r in getattr(router, "routes", []):
        if type(r).__name__ == "_IncludedRouter":
            ctx = getattr(r, "include_context", None)
            sub = getattr(ctx, "included_router", None) or getattr(r, "original_router", None)
            sub_prefix = getattr(ctx, "prefix", "") or ""
            if sub is not None:
                yield from _walk_routes(sub, prefix + sub_prefix)
            continue
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None)
        if path is None or not methods:
            continue
        yield prefix + path, sorted(methods - {"HEAD", "OPTIONS"}), r


def scan_routes() -> list[dict]:
    sys.path.insert(0, str(BACKED))
    from app.factory import create_app

    routes: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for path, methods, r in _walk_routes(create_app().router):
        if not path.startswith("/api/v1/hub"):
            continue
        endpoint = getattr(r, "endpoint", None)
        doc = ""
        if endpoint is not None:
            lines = (endpoint.__doc__ or "").strip().splitlines()
            doc = lines[0].strip()[:120] if lines else ""
        for m in methods:
            key = (path, m)
            if key in seen:  # 同一 path+method 被挂两次：只记一次，别在文档里造重复
                continue
            seen.add(key)
            routes.append({
                "path": path,
                "methods": [m],
                "name": getattr(r, "name", ""),
                "doc": doc,
            })
    routes.sort(key=lambda x: (x["path"], x["methods"]))
    return routes


# --------------------------------------------------------------------------- #
# MCP 工具
# --------------------------------------------------------------------------- #
def scan_mcp_tools() -> list[dict]:
    path = REPO / "mcp_server.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    tools = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorated = False
        for d in node.decorator_list:
            target = d.func if isinstance(d, ast.Call) else d
            if isinstance(target, ast.Attribute) and target.attr == "tool":
                decorated = True
        if not decorated:
            continue
        args = [
            a.arg for a in node.args.args
            if a.arg not in ("self", "cls")
        ]
        tools.append({
            "name": node.name,
            "args": args,
            "doc": _first_doc_line(node),
        })
    return sorted(tools, key=lambda x: x["name"])


# --------------------------------------------------------------------------- #
# 平台适配器
# --------------------------------------------------------------------------- #
def scan_adapters() -> list[dict]:
    sys.path.insert(0, str(BACKED))
    import service.publishing.adapters  # noqa: F401  (导入即注册)
    from service.publishing.adapters.base import ADAPTERS, capability_of

    out = []
    for pid, inst in sorted(ADAPTERS.items()):
        caps = capability_of(pid)
        out.append({
            "id": pid,
            "name": inst.name,
            "needs_browser": bool(inst.needs_browser),
            "login_url": inst.login_url,
            "selector_version": inst.selector_version,
            "key_selectors": sorted(inst.key_selectors.keys()) if inst.key_selectors else [],
            "capabilities": {k: bool(v) for k, v in sorted(caps.items())},
        })
    return out


# --------------------------------------------------------------------------- #
# 数据库
# --------------------------------------------------------------------------- #
def scan_schema() -> dict:
    sys.path.insert(0, str(BACKED))
    from service.publishing import db

    sql = db.SCHEMA + "\n" + getattr(db, "FTS_SCHEMA", "")
    tables = []
    for name in re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", db.SCHEMA):
        block = re.search(
            rf"CREATE TABLE IF NOT EXISTS {name} \((.*?)\n\);", db.SCHEMA, re.S
        )
        cols = []
        if block:
            for line in block.group(1).splitlines():
                m = re.match(r"\s*(\w+)\s+([A-Za-z0-9_()]+)", line)
                if m and m.group(1).upper() not in {"UNIQUE", "PRIMARY", "FOREIGN"}:
                    cols.append({"name": m.group(1), "type": m.group(2)})
        tables.append({"table": name, "columns": cols})

    indexes = sorted(re.findall(r"CREATE INDEX IF NOT EXISTS (\w+)", db.SCHEMA))
    virtual = sorted(re.findall(r"CREATE VIRTUAL TABLE IF NOT EXISTS (\w+)", sql))
    migrations = getattr(db, "MIGRATIONS", [])
    return {
        "tables": tables,
        "indexes": indexes,
        "fts_tables": virtual,
        "migrations": [{"version": v} for v, _ in migrations] if migrations else [],
    }


# --------------------------------------------------------------------------- #
# 测试 / CLI / 配置
# --------------------------------------------------------------------------- #
def scan_tests() -> dict:
    files = sorted((BACKED / "tests").rglob("*.py"))
    per_file = []
    total = 0
    for p in files:
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        n = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        )
        total += n
        per_file.append({
            "file": _rel(p),
            "tests": n,
            "loc": p.read_text(encoding="utf-8").count("\n") + 1,
        })
    return {
        "files": per_file,
        "test_functions": total,
        "total_loc": sum(x["loc"] for x in per_file),
        "note": "parametrize 展开后的实际用例数以此为准：uv run pytest --collect-only -q",
    }


def scan_cli() -> list[dict]:
    path = BACKED / "cli.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in node.decorator_list:
            target = d.func if isinstance(d, ast.Call) else d
            name = getattr(target, "attr", getattr(target, "id", ""))
            if "command" not in name:
                continue
            cmd = ""
            help_text = ""
            if isinstance(d, ast.Call):
                for kw in d.keywords:
                    if kw.arg == "help" and isinstance(kw.value, ast.Constant):
                        help_text = str(kw.value.value)
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        cmd = str(kw.value.value)
                if not cmd and d.args and isinstance(d.args[0], ast.Constant):
                    cmd = str(d.args[0].value)
            if not cmd:
                cmd = node.name[:-4] if node.name.endswith("_cmd") else node.name
            first = _first_doc_line(node)
            if not first and help_text:
                first = help_text.splitlines()[0]
            out.append({"command": cmd.replace("_", "-"), "doc": first[:140]})
            break
    return sorted(out, key=lambda x: x["command"])


def scan_config() -> dict:
    path = BACKED / "config.example.json"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"keys": [], "platforms": []}
    keys = [k for k in raw if not k.startswith("_")]
    platforms = sorted((raw.get("platforms") or {}).keys())
    return {"keys": sorted(keys), "platforms": platforms}


# --------------------------------------------------------------------------- #
# 组装
# --------------------------------------------------------------------------- #
def build() -> dict:
    pyproject = (BACKED / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    package = json.loads((REPO / "web/package.json").read_text(encoding="utf-8"))

    modules, edges, graph_stats = scan_modules()
    ctx = {
        "project": {
            "name": "Harbor (内容港)",
            "version": version.group(1) if version else "",
            "backend_python": ">=3.10",
            "web_node": package.get("packageManager", ""),
            "stack": [
                "FastAPI", "SQLite(WAL/FTS5)", "Patchright(Chromium)",
                "Vue3 + Element Plus + Pinia", "Tauri 2", "MCP",
            ],
        },
        "stats": {
            "python_modules": graph_stats["module_count"],
            "python_loc": graph_stats["total_loc"],
            "rest_routes": len(routes := scan_routes()),
            "mcp_tools": len(mcp := scan_mcp_tools()),
            "adapters": len(adapters := scan_adapters()),
            "cli_commands": len(cli := scan_cli()),
        },
        "graph": graph_stats,
        "modules": modules,
        "routes": routes,
        "mcp_tools": mcp,
        "adapters": adapters,
        "schema": scan_schema(),
        "tests": scan_tests(),
        "cli": cli,
        "config": scan_config(),
        "dependencies": edges,
        "entrypoints": [
            {"path": "mcp_server.py", "role": "MCP Server（stdio / streamable-http / SSE），32 个 tool"},
            {"path": "backed/app/factory.py", "role": "FastAPI 唯一装配入口 create_app()"},
            {"path": "backed/cli.py", "role": "命令行入口"},
            {"path": "backed/desktop_sidecar.py", "role": "Tauri 桌面端 sidecar 启动"},
            {"path": "scripts/check_all.sh", "role": "本地八道门禁"},
            {"path": "scripts/gen_agent_context.py", "role": "本文件生成器（--check 进 CI）"},
        ],
    }
    return ctx


def render_md(ctx: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# CONTEXT.md — 仓库事实清单（自动生成）")
    a("")
    a("> 本文件由 `scripts/gen_agent_context.py` 从代码生成，**不要手改**。")
    a("> 改代码后跑 `python scripts/gen_agent_context.py`；CI 会跑 `--check`，漂了直接红。")
    a("> 机器可读版本：[`CONTEXT.json`](CONTEXT.json)")
    a("")
    p = ctx["project"]
    a("## 0. 一句话")
    a("")
    a(f"**{p['name']}** v{p['version']}：自托管多平台内容发布中台。一次写作 → 多平台分发 → "
      "原地更新 → 发布后回读确认。单机、单用户、无遥测。")
    a("")
    a("| 项 | 值 |")
    a("|---|---|")
    a(f"| 版本 | {p['version']} |")
    a(f"| 后端 | Python {p['backend_python']} / FastAPI / 裸 sqlite3（WAL + FTS5） |")
    a(f"| 前端 | Vue3 + Element Plus + Pinia + Tauri 2 |")
    a(f"| 平台适配器 | {ctx['stats']['adapters']} |")
    a(f"| REST | {ctx['stats']['rest_routes']} 个操作 |")
    a(f"| MCP | {ctx['stats']['mcp_tools']} 个 tool |")
    a(f"| Python 模块 | {ctx['stats']['python_modules']}（{ctx['stats']['python_loc']} 行） |")
    a("")

    a("## 1. 入口点")
    a("")
    a("| 文件 | 作用 |")
    a("|---|---|")
    for e in ctx["entrypoints"]:
        a(f"| `{e['path']}` | {e['role']} |")
    a("")

    a("## 2. 模块依赖（包级计数 + 扇入 Top）")
    a("")
    a("| 包 | 模块数 |")
    a("|---|---|")
    for k, v in ctx["graph"]["packages"].items():
        a(f"| `{k}` | {v} |")
    a("")
    a("被依赖最多（改它影响面最大）：")
    a("")
    for x in ctx["graph"]["top_fan_in"]:
        a(f"- `{x['module']}` ← {x['importers']} 个模块")
    a("")

    a("## 3. REST API")
    a("")
    a(f"共 {ctx['stats']['rest_routes']} 个操作，前缀 `/api/v1/hub`。")
    a("")
    a("| 方法 | 路径 | 处理函数 | 说明 |")
    a("|---|---|---|---|")
    for r in ctx["routes"]:
        a(f"| {'/'.join(r['methods'])} | `{r['path']}` | `{r['name']}` | {r['doc']} |")
    a("")

    a("## 4. MCP 工具")
    a("")
    a(f"共 {ctx['stats']['mcp_tools']} 个，定义在 `mcp_server.py`。")
    a("")
    a("| Tool | 参数 | 说明 |")
    a("|---|---|---|")
    for t in ctx["mcp_tools"]:
        a(f"| `{t['name']}` | {', '.join(t['args']) or '—'} | {t['doc']} |")
    a("")

    a("## 5. 平台适配器与能力矩阵")
    a("")
    a("能力为 `true` 才算真的支持；未声明一律 false（防假成功）。")
    a("")
    cap_keys = sorted(ctx["adapters"][0]["capabilities"]) if ctx["adapters"] else []
    a("| 平台 | 浏览器 | " + " | ".join(cap_keys) + " | 选择器版本 |")
    a("|---|:--:|" + "|".join([":--:"] * len(cap_keys)) + "|---|")
    for ad in ctx["adapters"]:
        marks = ["✅" if ad["capabilities"].get(k) else "·" for k in cap_keys]
        a(f"| `{ad['id']}` {ad['name']} | {'是' if ad['needs_browser'] else '否'} | "
          + " | ".join(marks) + f" | {ad['selector_version'] or '—'} |")
    a("")

    a("## 6. 数据库")
    a("")
    a("| 表 | 列 |")
    a("|---|---|")
    for t in ctx["schema"]["tables"]:
        cols = ", ".join(f"`{c['name']}`" for c in t["columns"])
        a(f"| `{t['table']}` | {cols} |")
    a("")
    if ctx["schema"]["fts_tables"]:
        a("全文检索：" + "、".join(f"`{x}`" for x in ctx["schema"]["fts_tables"]) + "（trigram 分词）")
        a("")
    a(f"索引 {len(ctx['schema']['indexes'])} 个；迁移版本 "
      f"{len(ctx['schema']['migrations'])} 段（`meta.schema_version` + `MIGRATIONS`）。")
    a("")

    a("## 7. 测试分布")
    a("")
    t = ctx["tests"]
    a(f"`test_*` 函数 {t['test_functions']} 个，测试代码 {t['total_loc']} 行。"
      "parametrize 展开后的真实用例数：" + "`uv run pytest --collect-only -q`。")
    a("")
    a("| 文件 | 用例函数 | 行数 |")
    a("|---|---|---|")
    for f in t["files"]:
        if f["tests"]:
            a(f"| `{f['file']}` | {f['tests']} | {f['loc']} |")
    a("")

    a("## 8. CLI")
    a("")
    for c in ctx["cli"]:
        a(f"- `{c['command']}` — {c['doc']}")
    a("")

    a("## 9. 配置键（config.example.json）")
    a("")
    a("顶层：" + "、".join(f"`{k}`" for k in ctx["config"]["keys"]))
    a("")
    a("平台段：" + "、".join(f"`{k}`" for k in ctx["config"]["platforms"]))
    a("")
    a("运行时真正读配置的是 `service/publishing/db.py:config_file()`（env > 数据根 > 旧位置），"
      "不是 `config_unified.py` 那套 Pydantic 类。")
    a("")
    return "\n".join(L)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    ctx = build()
    md = render_md(ctx)
    js = json.dumps(ctx, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if check:
        problems = []
        for path, fresh in ((OUT_JSON, js), (OUT_MD, md)):
            if not path.is_file():
                problems.append(f"缺失：{_rel(path)}")
                continue
            old = path.read_text(encoding="utf-8")
            if old != fresh:
                diff = "".join(
                    list(unified_diff(
                        old.splitlines(keepends=True), fresh.splitlines(keepends=True),
                        fromfile=f"{_rel(path)}（已提交）",
                        tofile=f"{_rel(path)}（当前代码生成）",
                        n=2,
                    ))[:40]
                )
                problems.append(diff)
        if problems:
            print("智能体上下文已过期，跑 `python scripts/gen_agent_context.py` 后重提交：\n")
            print("\n".join(problems))
            return 1
        print("OK  智能体上下文与代码一致")
        return 0

    OUT_JSON.write_text(js, encoding="utf-8")
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"OK  已写入 {_rel(OUT_MD)} / {_rel(OUT_JSON)}")
    print(f"    路由 {ctx['stats']['rest_routes']} · MCP {ctx['stats']['mcp_tools']} · "
          f"适配器 {ctx['stats']['adapters']} · 模块 {ctx['stats']['python_modules']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
