# -*- coding: utf-8 -*-
"""多档案工作区：激活档案、表单化编辑、SOP 查看/手改/恢复、平台移除。

边界：
- 仍以 ``profiles/<name>/profile.yaml`` 为唯一真源；这里不做另一套存储。
- 表单保存会重写 YAML，首次重写前留一份 ``profile.yaml.bak``。
- 手改 SOP 会在 front matter 打 ``customized: true``，自检不再按模板漂移报错；
  想回到模板时由界面显式「恢复模板」，不会偷偷覆盖。
"""

from __future__ import annotations

import os
import re
from copy import deepcopy
from pathlib import Path

import yaml

from service.onboarding import (
    OnboardingError,
    _NAME,
    _declared_platforms,
    _known_platforms,
    check_profile,
    default_profiles_root,
    load_profile,
    platform_catalog,
    render_template,
    TEMPLATE_DIR,
    profile_summaries,
)

MAX_YAML_BYTES = 256 * 1024
MAX_SOP_BYTES = 512 * 1024

_HEADER = (
    "# 本文件由 Harbor 设置页保存；账号、主线与路径只留本机，不会提交到仓库。\n"
    "# 首次在界面保存前的原文件已留档为 profile.yaml.bak。\n"
)

_FIELD_KEYS = {"timezone", "mainline", "style", "engagement", "windows", "accounts"}


def _root(profiles_root: str | Path | None = None) -> Path:
    return Path(profiles_root) if profiles_root else default_profiles_root()


def _profile_dir(name: str, profiles_root: str | Path | None = None) -> Path:
    if not _NAME.match(name or ""):
        raise OnboardingError("档案名只能用小写字母、数字、- 或 _，最长 32 个字符")
    return _root(profiles_root) / name


def _profile_path(name: str, profiles_root: str | Path | None = None) -> Path:
    path = _profile_dir(name, profiles_root) / "profile.yaml"
    if not path.is_file():
        raise OnboardingError(f"档案不存在：profiles/{name}/profile.yaml")
    return path


def list_profile_names(profiles_root: str | Path | None = None) -> list[str]:
    root = _root(profiles_root)
    if not root.is_dir():
        return []
    return [d.name for d in sorted(root.iterdir(), key=lambda p: p.name)
            if d.is_dir() and (d / "profile.yaml").is_file() and _NAME.match(d.name)]


def active_profile_name(profiles_root: str | Path | None = None) -> str:
    """当前激活档案；没有标记时退回第一个（兼容单档案老用户）。"""
    root = _root(profiles_root)
    names = list_profile_names(root)
    marker = root / ".active_profile"
    if marker.is_file():
        try:
            name = marker.read_text(encoding="utf-8").strip()
        except OSError:
            name = ""
        if name in names:
            return name
    return names[0] if names else ""


def set_active_profile(name: str, profiles_root: str | Path | None = None) -> dict:
    _profile_path(name, profiles_root)
    root = _root(profiles_root)
    root.mkdir(parents=True, exist_ok=True)
    marker = root / ".active_profile"
    tmp = marker.with_name(marker.name + ".tmp")
    tmp.write_text(name + "\n", encoding="utf-8")
    os.replace(tmp, marker)
    return {"active": name, "profiles": workspace_overview(profiles_root)["profiles"]}


def workspace_overview(profiles_root: str | Path | None = None) -> dict:
    active = active_profile_name(profiles_root)
    items = profile_summaries(profiles_root)
    for item in items:
        item["active"] = item["name"] == active
    return {"active": active, "profiles": items}


def _fmt(value) -> str:
    if isinstance(value, list):
        return "、".join(str(v) for v in value)
    if value is None:
        return ""
    return str(value)


def _public_fields(data: dict) -> dict:
    style = data.get("style") if isinstance(data.get("style"), dict) else {}
    engagement = data.get("engagement") if isinstance(data.get("engagement"), dict) else {}
    windows = data.get("windows") if isinstance(data.get("windows"), dict) else {}
    accounts = data.get("accounts") if isinstance(data.get("accounts"), dict) else {}
    content_plan = data.get("content_plan") if isinstance(data.get("content_plan"), dict) else {}
    return {
        "name": data.get("name", ""),
        "timezone": data.get("timezone", ""),
        "mainline": data.get("mainline", ""),
        "voice": style.get("voice", ""),
        "avoid": style.get("avoid") if isinstance(style.get("avoid"), list) else [],
        "min_images": style.get("min_images", 0),
        "min_code_blocks": style.get("min_code_blocks", 0),
        "engagement": {
            "proactive_comments": engagement.get("proactive_comments", 0),
            "reply_only_after": engagement.get("reply_only_after", 0),
            "max_per_author": engagement.get("max_per_author", 0),
            "max_follow_back": engagement.get("max_follow_back", 0),
        },
        "windows": {"active": windows.get("active", "")},
        "accounts": {str(k): str(v) for k, v in accounts.items()},
        "content_plan": content_plan,
    }


def _playbook_title(text: str, platform: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                meta = yaml.safe_load(parts[1]) or {}
                if isinstance(meta, dict) and meta.get("title"):
                    return str(meta["title"]).replace("（模板）", "").strip()
            except yaml.YAMLError:
                pass
    return platform


def _is_customized(text: str) -> bool:
    head = text[:800]
    if not head.startswith("---"):
        return False
    fm = head.split("---", 2)[1] if head.count("---") >= 2 else head
    return bool(re.search(r"(?m)^customized:\s*true\s*$", fm))


def _mark_customized(text: str) -> str:
    if _is_customized(text):
        return text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[:end] + "\ncustomized: true" + text[end:]
    return "---\ncustomized: true\n---\n\n" + text


def _playbook_items(name: str, profile: dict, profiles_root=None) -> list[dict]:
    target = _profile_dir(name, profiles_root)
    playbook_dir = target / "playbooks"
    declared = _declared_platforms(profile, sorted(playbook_dir.glob("*.md")) if playbook_dir.is_dir() else [])
    items = []
    for platform in declared:
        path = playbook_dir / f"{platform}.md"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        fresh = ""
        template = TEMPLATE_DIR / f"{platform}.md"
        if template.is_file():
            try:
                fresh = render_template(template.read_text(encoding="utf-8"), profile, platform=platform)
            except OnboardingError:
                fresh = ""
        items.append({
            "platform": platform,
            "exists": path.is_file(),
            "customized": _is_customized(text),
            "drifted": bool(text and fresh and not _is_customized(text) and text != fresh),
            "size": path.stat().st_size if path.is_file() else 0,
            "title": _playbook_title(text, platform) if text else platform,
            "template": template.is_file(),
        })
    return items


def profile_detail(name: str, profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    text = path.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > MAX_YAML_BYTES:
        raise OnboardingError("profile.yaml 超过 256KB，拒绝在界面里编辑")
    data = load_profile(path)
    check = check_profile(name, profiles_root)
    active = active_profile_name(profiles_root)
    platforms = platform_catalog()
    by_id = {p["id"]: p for p in platforms}
    declared = _declared_platforms(data, [])
    rows = []
    for platform in declared:
        rows.append({
            "id": platform,
            "name": by_id.get(platform, {}).get("name", platform),
            "needs_browser": by_id.get(platform, {}).get("needs_browser", True),
        })
    return {
        "name": name,
        "active": name == active,
        "profile": f"profiles/{name}/profile.yaml",
        "yaml": text,
        "fields": _public_fields(data),
        "platforms": rows,
        "playbooks": _playbook_items(name, data, profiles_root),
        "check": check,
        "backup": (path.parent / "profile.yaml.bak").is_file(),
    }


def _atomic_text(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
    try:
        from service.publishing.crypto import _restrict_key_file
        _restrict_key_file(path)
    except Exception:   # aqg: top-level boundary（权限收紧失败不阻断保存）
        pass


def _backup_once(path: Path) -> None:
    backup = path.with_name("profile.yaml.bak")
    if backup.exists():
        return
    try:
        backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            from service.publishing.crypto import _restrict_key_file
            _restrict_key_file(backup)
        except Exception:   # aqg: top-level boundary
            pass
    except OSError:
        pass


def _dump_profile(path: Path, data: dict) -> None:
    text = _HEADER + yaml.safe_dump(data, allow_unicode=True, sort_keys=False,
                                    default_flow_style=False)
    _atomic_text(path, text)


def _ensure_type(value, typ, label: str):
    if not isinstance(value, typ):
        raise OnboardingError(f"{label} 类型不对")


def _validate_fields(patch: dict) -> None:
    if not isinstance(patch, dict):
        raise OnboardingError("fields 必须是对象")
    if "timezone" in patch:
        _ensure_type(patch["timezone"], str, "timezone")
        if len(patch["timezone"]) > 64:
            raise OnboardingError("timezone 过长")
    if "mainline" in patch:
        _ensure_type(patch["mainline"], str, "mainline")
        if len(patch["mainline"]) > 500:
            raise OnboardingError("mainline 最多 500 字")
    if "style" in patch:
        _ensure_type(patch["style"], dict, "style")
        st = patch["style"]
        if "voice" in st:
            _ensure_type(st["voice"], str, "style.voice")
            if len(st["voice"]) > 500:
                raise OnboardingError("style.voice 最多 500 字")
        if "avoid" in st:
            _ensure_type(st["avoid"], list, "style.avoid")
            if len(st["avoid"]) > 50:
                raise OnboardingError("style.avoid 最多 50 条")
            for item in st["avoid"]:
                _ensure_type(item, str, "style.avoid 中的条目")
                if len(item) > 120:
                    raise OnboardingError("style.avoid 单条最多 120 字")
        for key in ("min_images", "min_code_blocks"):
            if key in st:
                _ensure_type(st[key], int, f"style.{key}")
                if not 0 <= st[key] <= 99:
                    raise OnboardingError(f"style.{key} 应在 0–99")
    if "engagement" in patch:
        _ensure_type(patch["engagement"], dict, "engagement")
        for key, value in patch["engagement"].items():
            if key not in ("proactive_comments", "reply_only_after",
                           "max_per_author", "max_follow_back"):
                raise OnboardingError(f"不支持的 engagement 字段：{key}")
            _ensure_type(value, int, f"engagement.{key}")
            if not 0 <= value <= 99:
                raise OnboardingError(f"engagement.{key} 应在 0–99")
    if "windows" in patch:
        _ensure_type(patch["windows"], dict, "windows")
        if "active" in patch["windows"]:
            _ensure_type(patch["windows"]["active"], str, "windows.active")
            if len(patch["windows"]["active"]) > 80:
                raise OnboardingError("windows.active 过长")
    if "accounts" in patch:
        _ensure_type(patch["accounts"], dict, "accounts")
        for key, value in patch["accounts"].items():
            if not isinstance(key, str) or not key.strip():
                raise OnboardingError("accounts 的平台键不能为空")
            if not isinstance(value, (str, int)):
                raise OnboardingError(f"accounts.{key} 必须是字符串")
            if len(str(value)) > 120:
                raise OnboardingError(f"accounts.{key} 过长")


def _apply_fields(data: dict, patch: dict) -> dict:
    out = deepcopy(data)
    if "timezone" in patch:
        out["timezone"] = patch["timezone"].strip()
    if "mainline" in patch:
        out["mainline"] = patch["mainline"].strip()
    if "style" in patch:
        style = out.get("style") if isinstance(out.get("style"), dict) else {}
        st = patch["style"]
        if "voice" in st:
            style["voice"] = st["voice"].strip()
        if "avoid" in st:
            style["avoid"] = [str(x).strip() for x in st["avoid"] if str(x).strip()]
        for key in ("min_images", "min_code_blocks"):
            if key in st:
                style[key] = st[key]
        out["style"] = style
    if "engagement" in patch:
        eng = out.get("engagement") if isinstance(out.get("engagement"), dict) else {}
        eng.update({k: v for k, v in patch["engagement"].items()})
        out["engagement"] = eng
    if "windows" in patch:
        win = out.get("windows") if isinstance(out.get("windows"), dict) else {}
        win.update(patch["windows"])
        out["windows"] = win
    if "accounts" in patch:
        acc = out.get("accounts") if isinstance(out.get("accounts"), dict) else {}
        for key, value in patch["accounts"].items():
            val = str(value).strip()
            if val:
                acc[key] = val
            else:
                acc.pop(key, None)
        out["accounts"] = acc
    return out


def update_profile_fields(name: str, fields: dict,
                          profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    data = load_profile(path)
    _validate_fields(fields or {})
    data = _apply_fields(data, fields or {})
    data["name"] = name
    _backup_once(path)
    _dump_profile(path, data)
    return profile_detail(name, profiles_root)


def save_profile_yaml(name: str, text: str,
                      profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    if not isinstance(text, str) or not text.strip():
        raise OnboardingError("YAML 不能为空")
    if len(text.encode("utf-8")) > MAX_YAML_BYTES:
        raise OnboardingError("profile.yaml 超过 256KB，拒绝保存")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise OnboardingError(f"YAML 解析失败：{exc}") from exc
    if not isinstance(data, dict):
        raise OnboardingError("YAML 顶层必须是映射")
    if data.get("name") != name:
        raise OnboardingError(f"YAML 里的 name 必须是 {name}，不能改档案名")
    _backup_once(path)
    _atomic_text(path, text if text.endswith("\n") else text + "\n")
    return profile_detail(name, profiles_root)


def remove_platform(name: str, platform: str,
                    profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    data = load_profile(path)
    platform = (platform or "").strip()
    if platform not in _known_platforms():
        raise OnboardingError(f"不支持的平台：{platform}")
    text = path.read_text(encoding="utf-8")
    files = sorted((path.parent / "playbooks").glob("*.md")) \
        if (path.parent / "playbooks").is_dir() else []
    current = _declared_platforms(data, files)
    if platform not in current:
        raise OnboardingError(f"档案 {name} 没有接入 {platform}")
    if len(current) <= 1:
        raise OnboardingError("至少保留一个平台；要全部停用请直接删除档案目录")
    merged = [p for p in current if p != platform]
    line = "platforms: [" + ", ".join(merged) + "]"
    block = re.compile(
        r"^platforms:[ \t]*(?:\[[^\n]*\]|[ \t]*\n(?:[ \t]+-[^\n]*\n)*)",
        re.M,
    )
    if block.search(text):
        text = block.sub(line + "\n", text, count=1)
    else:
        text = re.sub(r"^(name: .*)$", rf"\1\n{line}", text, count=1, flags=re.M)
    _atomic_text(path, text)
    sop = path.parent / "playbooks" / f"{platform}.md"
    if sop.is_file():
        sop.unlink()
    return profile_detail(name, profiles_root)


def get_playbook(name: str, platform: str,
                 profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    data = load_profile(path)
    platform = (platform or "").strip()
    if platform not in _declared_platforms(data, []):
        raise OnboardingError(f"档案 {name} 没有接入 {platform}")
    sop_path = path.parent / "playbooks" / f"{platform}.md"
    if not sop_path.is_file():
        raise OnboardingError(f"没有 {platform} 的个人 SOP，先点「重新生成」")
    text = sop_path.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > MAX_SOP_BYTES:
        raise OnboardingError("SOP 超过 512KB，拒绝在界面里编辑")
    return {
        "platform": platform,
        "markdown": text,
        "customized": _is_customized(text),
        "size": sop_path.stat().st_size,
    }


def save_playbook(name: str, platform: str, markdown: str,
                  profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    data = load_profile(path)
    platform = (platform or "").strip()
    if platform not in _declared_platforms(data, []):
        raise OnboardingError(f"档案 {name} 没有接入 {platform}")
    if not isinstance(markdown, str) or not markdown.strip():
        raise OnboardingError("SOP 不能为空")
    if "\x00" in markdown:
        raise OnboardingError("SOP 不能包含 NUL 字符")
    if len(markdown.encode("utf-8")) > MAX_SOP_BYTES:
        raise OnboardingError("SOP 超过 512KB，拒绝保存")
    sop_path = path.parent / "playbooks" / f"{platform}.md"
    sop_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_text(sop_path, _mark_customized(markdown))
    return {
        "platform": platform,
        "markdown": sop_path.read_text(encoding="utf-8"),
        "customized": True,
        "size": sop_path.stat().st_size,
    }


def reset_playbook(name: str, platform: str,
                   profiles_root: str | Path | None = None) -> dict:
    path = _profile_path(name, profiles_root)
    data = load_profile(path)
    platform = (platform or "").strip()
    if platform not in _declared_platforms(data, []):
        raise OnboardingError(f"档案 {name} 没有接入 {platform}")
    template = TEMPLATE_DIR / f"{platform}.md"
    if not template.is_file():
        raise OnboardingError(f"没有 {platform} 的模板，无法恢复")
    text = render_template(template.read_text(encoding="utf-8"), data, platform=platform)
    sop_path = path.parent / "playbooks" / f"{platform}.md"
    sop_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_text(sop_path, text)
    return {
        "platform": platform,
        "markdown": text,
        "customized": False,
        "size": sop_path.stat().st_size,
    }
