# -*- coding: utf-8 -*-
"""工作区 REST：多档案切换、档案表单/YAML、SOP 查看编辑、平台移除、API 凭据。

把"登录完之后的管理"从文件层搬到界面层：档案主线/风格/互动额度、个人 SOP、
API 平台凭据都能在设置页改；个人数据仍只写 profiles/ 与 config.json，不入库。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from service.onboarding import OnboardingError
from service.profiles import (
    get_playbook,
    profile_detail,
    remove_platform,
    reset_playbook,
    save_playbook,
    save_profile_yaml,
    set_active_profile,
    update_profile_fields,
    workspace_overview,
)
from service.publishing.platform_config import (
    get_platform_credentials,
    update_platform_credentials,
)

router = APIRouter()


class ActiveIn(BaseModel):
    name: str


class ProfileUpdateIn(BaseModel):
    fields: dict = {}
    yaml: str | None = None


class PlatformRemoveIn(BaseModel):
    platform: str


class PlaybookIn(BaseModel):
    markdown: str


class CredentialsIn(BaseModel):
    fields: dict = {}


def _bad(exc: Exception) -> HTTPException:
    return HTTPException(422, str(exc))


@router.get("/workspace")
def workspace():
    return workspace_overview()


@router.put("/workspace/active")
def workspace_active(body: ActiveIn):
    try:
        return set_active_profile(body.name)
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.get("/workspace/profiles/{name}")
def workspace_profile(name: str):
    try:
        return profile_detail(name)
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.put("/workspace/profiles/{name}")
def workspace_profile_update(name: str, body: ProfileUpdateIn):
    try:
        if body.yaml is not None:
            if body.fields:
                raise OnboardingError("fields 与 yaml 只能二选一保存")
            return save_profile_yaml(name, body.yaml)
        return update_profile_fields(name, body.fields or {})
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.post("/workspace/profiles/{name}/platforms/remove")
def workspace_profile_remove_platform(name: str, body: PlatformRemoveIn):
    try:
        return remove_platform(name, body.platform)
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.get("/workspace/profiles/{name}/playbooks/{platform}")
def workspace_playbook(name: str, platform: str):
    try:
        return get_playbook(name, platform)
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.put("/workspace/profiles/{name}/playbooks/{platform}")
def workspace_playbook_save(name: str, platform: str, body: PlaybookIn):
    try:
        return save_playbook(name, platform, body.markdown)
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.post("/workspace/profiles/{name}/playbooks/{platform}/reset")
def workspace_playbook_reset(name: str, platform: str):
    try:
        return reset_playbook(name, platform)
    except OnboardingError as exc:
        raise _bad(exc) from exc


@router.get("/platform-credentials")
def platform_credentials():
    try:
        return get_platform_credentials()
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.put("/platform-credentials/{platform}")
def platform_credentials_save(platform: str, body: CredentialsIn):
    try:
        return update_platform_credentials(platform, body.fields or {})
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
