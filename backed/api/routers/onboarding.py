# -*- coding: utf-8 -*-
"""首次使用向导：建个人档案、渲染 SOP、给出 MCP 接入配置。"""

import json
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from service.onboarding import (
    OnboardingError,
    REPO_ROOT,
    add_platforms,
    check_profile,
    init_profile,
    platform_catalog,
    profile_summaries,
    rerender_profile,
    template_catalog,
)
from service.profiles import active_profile_name
from service.publishing import db

router = APIRouter()


class InitIn(BaseModel):
    name: str
    platforms: list[str] = []
    force: bool = False


class CheckIn(BaseModel):
    name: str


class AddPlatformsIn(BaseModel):
    name: str
    platforms: list[str]


class RerenderIn(BaseModel):
    name: str


def _mcp_payload() -> dict:
    """给本机 MCP 客户端直接可粘贴的配置（stdio）。

    源码部署用 ``python mcp_server.py``；PyInstaller 桌面版没有仓库文件，
    改为同一个 sidecar 可执行文件加 ``--mcp``。
    """
    data_dir = str(db.data_root())
    if getattr(sys, "frozen", False):
        command, args = sys.executable, ["--mcp"]
    else:
        command, args = sys.executable, [str(REPO_ROOT / "mcp_server.py")]
    cfg = {
        "mcpServers": {
            "harbor": {
                "command": command,
                "args": args,
                "env": {"HUB_DATA_DIR": data_dir},
            }
        }
    }
    return {
        "transport": "stdio",
        "config": cfg,
        "json": json.dumps(cfg, ensure_ascii=False, indent=2),
        "data_dir": data_dir,
    }


@router.get("/onboarding/state")
def onboarding_state():
    profiles = profile_summaries()
    active = active_profile_name()
    for item in profiles:
        item["active"] = item["name"] == active
    return {
        "profiles": profiles,
        "active": active,
        "templates": template_catalog(),
        "platforms": platform_catalog(),
        "needs_setup": not profiles,
        "mcp": _mcp_payload(),
    }


@router.post("/onboarding/init")
def onboarding_init(body: InitIn):
    """创建 ``profiles/<name>/``，并把选中模板渲染成个人 SOP。"""
    try:
        result = init_profile(body.name, body.platforms or None, force=body.force)
    except OnboardingError as exc:
        raise HTTPException(422, str(exc)) from exc

    platforms = result["platforms"]
    sop_platforms = result.get("sop_platforms", [Path(p).stem for p in result["playbooks"]])
    return {
        "name": result["name"],
        "profile": f"profiles/{body.name}/profile.yaml",
        "platforms": platforms,
        "playbooks": [f"profiles/{body.name}/playbooks/{p}.md" for p in sop_platforms],
        "progress": f"profiles/{body.name}/progress",
    }


@router.post("/onboarding/platforms")
def onboarding_add_platforms(body: AddPlatformsIn):
    """给已有档案追加平台，不重写账号与主线。"""
    try:
        result = add_platforms(body.name, body.platforms)
        check = check_profile(body.name)
    except OnboardingError as exc:
        raise HTTPException(422, str(exc)) from exc
    return {
        "name": result["name"],
        "profile": f"profiles/{body.name}/profile.yaml",
        "platforms": result["platforms"],
        "playbooks": [f"profiles/{body.name}/playbooks/{Path(p).stem}.md"
                      for p in result["playbooks"]],
        "added": result["added"],
        "progress": f"profiles/{body.name}/progress",
        "check": check,
    }


@router.post("/onboarding/check")
def onboarding_check(body: CheckIn):
    try:
        return check_profile(body.name)
    except OnboardingError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post("/onboarding/rerender")
def onboarding_rerender(body: RerenderIn):
    """只重渲染个人 SOP，不重写 profile.yaml（账号配置不会被冲掉）。"""
    try:
        result = rerender_profile(body.name)
        check = check_profile(body.name)
    except OnboardingError as exc:
        raise HTTPException(422, str(exc)) from exc
    platforms = result["platforms"]
    sop_platforms = result.get("sop_platforms", platforms)
    return {
        "name": result["name"],
        "profile": f"profiles/{body.name}/profile.yaml",
        "platforms": platforms,
        "playbooks": [f"profiles/{body.name}/playbooks/{p}.md" for p in sop_platforms],
        "progress": f"profiles/{body.name}/progress",
        "check": check,
    }
