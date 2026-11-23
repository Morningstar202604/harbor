# -*- coding: utf-8 -*-
"""平台技能卡：把登录后的动作、限制和验收标准交给 AI。

Harbor 的适配器只负责“能不能发”，新接入的平台如果只有登录卡，AI 仍然不知道
登录后该选什么、发草稿还是直发、哪些字段平台根本不支持。这里把每个平台的
SOP 模板和适配器能力合成一张技能卡，MCP 的 ``get_platform_skill`` 直接返回全文。
"""

from pathlib import Path

from service.onboarding import (
    TEMPLATE_DIR,
    default_profiles_root,
    platform_catalog,
    profile_summaries,
)


_LIMITATIONS = {
    "update": "不支持原地更新，改稿只能删后重发或去平台后台手动改。",
    "draft": "没有草稿箱，提交即上线，发之前必须人工确认。",
    "list": "没有已发布文章列表接口，只能用发布结果 URL 或平台后台核对。",
    "tags": "标签不支持接口，发布时要在平台编辑器里手动补。",
    "cover": "封面不支持接口，发布时要在平台编辑器里手动上传。",
}

_POST_LOGIN = [
    "确认登录态：浏览器平台看账号头像/后台首页，API 平台先做一次只读请求。",
    "读本技能卡的「内容适配」和「限制」，先判断这篇是否适合该平台。",
    "优先用 publish_article 发草稿（draft_only=true）；平台没有草稿能力时先人工确认。",
    "发布/存草稿后回读公开页或后台列表，确认标题、正文首段、图片、标签真的生效。",
    "把 URL、草稿状态、缺失的后台设置、失败原因写进结果；完成写“已做完”。",
]


def _front_matter_value(text: str, key: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    if len(parts) < 3:
        return ""
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return ""


def _find_playbook(platform: str, profile: str | None, profiles_root=None) -> tuple[Path | None, str]:
    from service.profiles import active_profile_name
    root = Path(profiles_root) if profiles_root else default_profiles_root()
    profiles = profile_summaries(root)
    names = [p["name"] for p in profiles]
    active = active_profile_name(root)
    name = profile if profile in names else (active if active in names else (names[0] if names else ""))
    if name:
        p = root / name / "playbooks" / f"{platform}.md"
        if p.is_file():
            return p, name
    p = TEMPLATE_DIR / f"{platform}.md"
    if p.is_file():
        return p, ""
    return None, ""


def get_platform_skill(
    platform: str,
    *,
    profile: str = "",
    accounts: list[dict] | None = None,
    profiles_root=None,
) -> dict:
    """返回一个平台的技能卡；platform 必须是已注册适配器。"""
    row = next((r for r in platform_catalog() if r["id"] == platform), None)
    if not row:
        raise ValueError(f"没有这个平台：{platform}")

    path, profile_name = _find_playbook(platform, profile or None, profiles_root)
    if not path:
        raise ValueError(f"平台 {platform} 没有 SOP，请先补 playbooks/{platform}.md")
    text = path.read_text(encoding="utf-8")

    caps = row["capabilities"]
    limitations = [
        msg for key, msg in _LIMITATIONS.items() if not caps.get(key)
    ]
    if not caps.get("hosted_media"):
        limitations.append("正文图片不做平台图床托管，发布前在平台编辑器里逐张上传。")
    if row["needs_browser"]:
        limitations.append("依赖 Harbor 主机上的浏览器登录态；失效时任务停在 waiting_human，不反复重试。")
    else:
        limitations.append("不使用浏览器登录，凭据在 Harbor 设置/config 里；token/密码不进文章、不进仓库。")

    status = "unknown"
    if accounts:
        mine = [a for a in accounts if a.get("platform") == platform]
        if mine:
            status = "online" if any(a.get("status") == "logined" for a in mine) else "offline"

    return {
        "id": platform,
        "name": row["name"],
        "login_url": row["login_url"],
        "home_url": row["home_url"],
        "needs_browser": row["needs_browser"],
        "account_status": status,
        "profile": profile_name,
        "title": _front_matter_value(text, "title").replace("（模板）", ""),
        "schedule": _front_matter_value(text, "schedule"),
        "capabilities": caps,
        "recommended_draft": bool(caps.get("draft")),
        "limitations": limitations,
        "post_login_steps": _POST_LOGIN,
        "publish_example": {
            "tool": "publish_article",
            "args": {
                "article_id": 1,
                "platforms": [platform],
                "draft_only": bool(caps.get("draft")),
            },
        },
        "skill_markdown": text,
        "source": "profile" if profile_name else "template",
    }
