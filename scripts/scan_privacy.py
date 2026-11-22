#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""隐私扫描：仓库里不该出现个人账号、报告链接、本机路径。

和 scan_secrets.py 的分工：
- scan_secrets 管密钥/令牌（泄了能直接盗号）
- 本脚本管身份痕迹（账号、用户 ID、飞书文档、绝对路径、个人档案入库）

只查会被提交的文件（git ls-files + 未忽略的新文件），避免把构建产物和虚拟环境误报。

用法::

    python scripts/scan_privacy.py      # 有命中退出 1
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "node_modules", ".venv", "dist", "build", "target", "__pycache__"}
TEXT_SUFFIX = {
    ".md", ".py", ".pyi", ".toml", ".yml", ".yaml", ".json", ".txt", ".sh",
    ".js", ".ts", ".vue", ".css", ".html", ".cfg", ".ini", ".example", "",
}

RULES: list[tuple[str, re.Pattern]] = [
    ("飞书文档链接", re.compile(r"https?://[^\s)>\"]*feishu\.cn[^\s)>\"]*")),
    ("本机绝对路径", re.compile(r"/home/[A-Za-z0-9._-]+/")),
    ("Windows 用户路径", re.compile(r"[A-Za-z]:\\\\?Users\\\\?")),
    ("CSDN 用户 ID", re.compile(r"weixin_\d{5,}")),
]

# 个人档案目录：只允许说明与示例
PROFILE_ALLOW = {"profiles/README.md", "profiles/example.yaml"}


def _tracked_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=REPO, check=True, capture_output=True, text=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        out = "\n".join(str(p.relative_to(REPO)) for p in REPO.rglob("*") if p.is_file())
    files = []
    for line in out.splitlines():
        p = REPO / line
        if not line or not p.is_file():
            continue
        if set(p.relative_to(REPO).parts) & SKIP_DIRS:
            continue
        if p.suffix.lower() not in TEXT_SUFFIX:
            continue
        files.append(p)
    return sorted(files)


def _rel(p: Path) -> str:
    return str(p.relative_to(REPO))


def main() -> int:
    hits: list[str] = []
    for path in _tracked_files():
        rel = _rel(path)
        if rel == "scripts/scan_privacy.py":  # 规则本身含路径样例
            continue
        if rel.startswith("profiles/") and rel not in PROFILE_ALLOW:
            hits.append(f"{rel}: 个人档案入库（profiles/ 只允许 README.md 与 example.yaml）")
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for label, pattern in RULES:
                m = pattern.search(line)
                if m:
                    hits.append(f"{rel}:{lineno}: {label} → {m.group(0)[:80]}")

    if hits:
        print("发现个人隐私痕迹（这些内容不应进入公开仓库）：\n")
        for h in hits:
            print("  " + h)
        print(f"\n共 {len(hits)} 处。个人数据请放 profiles/<name>/（已 gitignore）。")
        return 1
    print(f"OK  已扫描 {len(_tracked_files())} 个文本文件，未发现个人隐私痕迹")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
