# -*- coding: utf-8 -*-
"""个人档案初始化与 playbook 模板渲染。

设计边界：
- 仓库只放模板；个人账号、报告链接、进度目录写进 ``profiles/<name>/profile.yaml``，
  该目录被 .gitignore 忽略。
- 渲染只做 ``{{profile.*}}`` 纯文本替换，不执行模板里的任何内容。
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _resource_root() -> Path:
    """只读资源目录：源码跑用仓库根，PyInstaller 单文件用 ``_MEIPASS``。"""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return REPO_ROOT


RESOURCE_ROOT = _resource_root()
TEMPLATE_DIR = RESOURCE_ROOT / "playbooks"
EXAMPLE_PROFILE = RESOURCE_ROOT / "profiles" / "example.yaml"
PROFILES_ROOT = REPO_ROOT / "profiles"


def default_profiles_root() -> Path:
    """个人档案目录：显式 env > 数据目录 > 仓库 ``profiles/``。

    桌面版由启动器设置 ``HUB_DATA_DIR``，档案自动落到可写数据目录
    （``<data>/profiles``）；升级安装目录不会覆盖用户档案。
    """
    env = os.environ.get("HARBOR_PROFILES_DIR", "").strip()
    if env:
        return Path(env).expanduser()
    data = os.environ.get("HUB_DATA_DIR", "").strip()
    if data:
        return Path(data) / "profiles"
    return PROFILES_ROOT


_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")
_PLACEHOLDER = re.compile(r"{{profile\.([a-zA-Z0-9_.]+)}}")


class OnboardingError(RuntimeError):
    """档案缺失、字段不全或模板渲染失败；调用方可直接展示给用户。"""


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "是" if value else "否"
    if isinstance(value, list):
        return "、".join(_fmt(v) for v in value)
    if isinstance(value, dict):
        return "；".join(f"{k}={_fmt(v)}" for k, v in value.items())
    return str(value)


def _lookup(profile: dict, dotted: str):
    node = profile
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise OnboardingError(f"档案缺少字段：profile.{dotted}")
        node = node[part]
    return node


def load_profile(path: str | Path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise OnboardingError(f"档案不存在：{p}")
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise OnboardingError(f"档案不是合法 YAML：{p}（{exc}）") from exc
    if not isinstance(data, dict):
        raise OnboardingError(f"档案顶层必须是映射：{p}")
    if not data.get("name"):
        raise OnboardingError(f"档案缺少 name：{p}")
    return data


def template_platforms() -> list[str]:
    """仓库里可用的模板平台 id（不含 README）。"""
    return sorted(p.stem for p in TEMPLATE_DIR.glob("*.md") if p.name != "README.md")


def render_template(text: str, profile: dict, *, platform: str = "") -> str:
    """把模板中的 ``{{profile.x.y}}`` 换成档案值。

    缺字段直接报错，避免生成一份带占位符的"半成品"却被当成正式 SOP。
    """

    def repl(match: re.Match) -> str:
        return _fmt(_lookup(profile, match.group(1)))

    out = _PLACEHOLDER.sub(repl, text)
    out = out.replace("scope: template", "scope: profile")
    out = out.replace("（模板）", "")
    out = out.replace("<name>", str(profile.get("name", "")))

    # 个人副本不再保留"复制模板"的自述，换成一次性的档案说明
    lines = [
        "> 个人副本：账号、主线、报告位置与进度路径来自 profile.yaml；本文件不入库。"
        if line.startswith("> 可复用模板") else line
        for line in out.splitlines()
    ]
    out = "\n".join(lines) + ("\n" if out.endswith("\n") else "")
    if platform:
        out = out.replace("scope: profile", f"scope: profile\nsource_template: playbooks/{platform}.md", 1)
    return out


def init_profile(
    name: str,
    platforms: list[str] | None = None,
    *,
    force: bool = False,
    profiles_root: str | Path | None = None,
) -> dict:
    """创建 ``profiles/<name>/``：档案 + 渲染后的 playbook 副本 + progress 目录。"""
    if not _NAME.match(name):
        raise OnboardingError("档案名只能用小写字母、数字、- 或 _，最长 32 个字符")
    root = Path(profiles_root) if profiles_root else default_profiles_root()
    target = root / name
    if target.exists() and not force:
        raise OnboardingError(f"档案已存在：{target}（要覆盖加 --force）")

    wanted = platforms or template_platforms()
    unknown = sorted(set(wanted) - set(template_platforms()))
    if unknown:
        raise OnboardingError(f"没有这些平台的模板：{', '.join(unknown)}")

    example = EXAMPLE_PROFILE
    if not example.is_file():
        raise OnboardingError(f"找不到档案示例：{example}")
    text = example.read_text(encoding="utf-8")
    text = re.sub(r"^name: .*$", f"name: {name}", text, count=1, flags=re.M)
    text = text.replace('"profiles/your-name/progress"', f'"profiles/{name}/progress"')
    text = text.replace('"profiles/your-name"', f'"profiles/{name}"')
    text = text.replace("# 复制为 profiles/<your-name>/profile.yaml 后填写。",
                        f"# profiles/{name}/profile.yaml（个人档案，已 gitignore，不会入库）")
    text = text.replace("# 这个文件本身入库，只放占位符；你的真实档案不要提交。",
                        "# 填真实账号与路径；不要把这个文件提交到任何仓库。")

    target.mkdir(parents=True, exist_ok=True)
    (target / "playbooks").mkdir(exist_ok=True)
    (target / "progress").mkdir(exist_ok=True)
    profile_path = target / "profile.yaml"
    profile_path.write_text(text, encoding="utf-8")

    profile = load_profile(profile_path)
    rendered: list[str] = []
    for platform in wanted:
        src = TEMPLATE_DIR / f"{platform}.md"
        dst = target / "playbooks" / f"{platform}.md"
        dst.write_text(render_template(src.read_text(encoding="utf-8"), profile,
                                       platform=platform), encoding="utf-8")
        rendered.append(platform)

    return {
        "name": name,
        "profile": str(profile_path),
        "playbooks": [str(target / "playbooks" / f"{p}.md") for p in rendered],
        "progress": str(target / "progress"),
    }


def render_platform(
    name: str,
    platform: str,
    *,
    out: str | Path | None = None,
    profiles_root: str | Path | None = None,
) -> Path:
    """按档案渲染单个平台；默认写到 ``profiles/<name>/playbooks/<platform>.md``。"""
    root = Path(profiles_root) if profiles_root else default_profiles_root()
    profile_path = root / name / "profile.yaml"
    template = TEMPLATE_DIR / f"{platform}.md"
    if not template.is_file():
        raise OnboardingError(f"没有这个平台的模板：{template}")
    profile = load_profile(profile_path)
    dst = Path(out) if out else root / name / "playbooks" / f"{platform}.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(render_template(template.read_text(encoding="utf-8"), profile,
                                   platform=platform), encoding="utf-8")
    return dst


def template_catalog() -> list[dict]:
    """模板清单（只读 front matter，用于前端勾选与展示）。"""
    items: list[dict] = []
    for path in sorted(TEMPLATE_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        meta: dict = {}
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                try:
                    loaded = yaml.safe_load(parts[1])
                    meta = loaded if isinstance(loaded, dict) else {}
                except yaml.YAMLError:
                    meta = {}
        title = str(meta.get("title") or path.stem).replace("（模板）", "").strip()
        items.append({
            "id": path.stem,
            "title": title,
            "platform": str(meta.get("platform") or path.stem),
            "schedule": str(meta.get("schedule") or ""),
        })
    return items


def profile_summaries(profiles_root: str | Path | None = None) -> list[dict]:
    """已存在的个人档案（不返回绝对路径，UI 只展示相对位置）。"""
    root = Path(profiles_root) if profiles_root else default_profiles_root()
    if not root.is_dir():
        return []
    items: list[dict] = []
    for d in sorted(root.iterdir(), key=lambda p: p.name):
        if not d.is_dir() or not (d / "profile.yaml").is_file():
            continue
        playbooks = sorted((d / "playbooks").glob("*.md")) if (d / "playbooks").is_dir() else []
        items.append({
            "name": d.name,
            "profile": f"profiles/{d.name}/profile.yaml",
            "platforms": [p.stem for p in playbooks],
            "playbooks": len(playbooks),
        })
    return items


def check_profile(name: str, profiles_root: str | Path | None = None) -> dict:
    """检查个人副本是否与模板 + 档案一致；不做写入。"""
    root = Path(profiles_root) if profiles_root else default_profiles_root()
    target = root / name
    profile_path = target / "profile.yaml"
    if not profile_path.is_file():
        raise OnboardingError(f"档案不存在：profiles/{name}/profile.yaml")
    profile = load_profile(profile_path)
    playbook_dir = target / "playbooks"
    files = sorted(playbook_dir.glob("*.md")) if playbook_dir.is_dir() else []
    problems: list[str] = []
    if not files:
        problems.append("没有 playbook 副本")
    for dst in files:
        platform = dst.stem
        template = TEMPLATE_DIR / f"{platform}.md"
        if not template.is_file():
            problems.append(f"{dst.name}：没有对应模板 playbooks/{platform}.md")
            continue
        fresh = render_template(template.read_text(encoding="utf-8"), profile, platform=platform)
        if dst.read_text(encoding="utf-8") != fresh:
            problems.append(f"{dst.name}：与档案或模板不一致，需要重新渲染")
    return {
        "name": name,
        "ok": not problems,
        "platforms": [p.stem for p in files],
        "problems": problems,
    }
