# -*- coding: utf-8 -*-
"""API 平台凭据读写信封：设置页表单直填，不用再手改 config.json。

安全边界：
- 读取回显只给掩码，永不返回完整密钥；
- 写入只允许本文件登记的字段，其他配置键原样保留；
- 原子写 + 解析失败拒绝写，避免把 config.json 写坏；
- endpoint 只接受 http/https，且不允许 URL 内嵌账号密码。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

from service.publishing.db import config_file

_PLATFORM_KEY = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
_MAX_FIELD = 2048


def _mask(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}\u2026{value[-4:]}"


def _is_placeholder(value: str) -> bool:
    v = (value or "").strip()
    return any(token in v for token in ("你的", "填", "xxx", "<", ">"))


def _spec(key: str, label: str, *, secret=False, required=True,
          placeholder="", hint="", endpoint=False) -> dict:
    return {"key": key, "label": label, "secret": secret,
            "required": required, "placeholder": placeholder,
            "hint": hint, "endpoint": endpoint}


PLATFORM_SPECS: dict[str, dict] = {
    "cnblogs": {
        "fields": [
            _spec("endpoint", "MetaWeblog 地址", endpoint=True, required=True,
                  placeholder="https://rpc.cnblogs.com/metaweblog/<博客地址名>",
                  hint="博客园后台 → 设置 → MetaWeblog 里复制"),
            _spec("username", "登录名", required=True, placeholder="博客园登录名"),
            _spec("token", "MetaWeblog 访问令牌", secret=True, required=True,
                  placeholder="粘贴访问令牌（不是登录密码）",
                  hint="也可点卡片上的「自动抠令牌」，登录一次自动填好"),
        ],
    },
    "metaweblog": {
        "fields": [
            _spec("endpoint", "XML-RPC 地址", endpoint=True, required=True,
                  placeholder="https://你的博客域名/xmlrpc.php"),
            _spec("username", "登录名", required=True, placeholder="WordPress / Typecho 登录名"),
            _spec("password", "应用密码", secret=True, required=True,
                  placeholder="WordPress 用应用程序密码；Typecho 用登录密码"),
        ],
    },
    "51cto": {
        "fields": [
            _spec("endpoint", "XML-RPC 地址", endpoint=True, required=False,
                  placeholder="留空自动拼：https://<用户名>.blog.51cto.com/xmlrpc.php"),
            _spec("username", "博客地址名", required=True, placeholder="51CTO 博客地址名"),
            _spec("password", "登录密码", secret=True, required=True,
                  placeholder="51CTO 登录密码"),
        ],
    },
    "devto": {
        "fields": [
            _spec("api_key", "API Key", secret=True, required=True,
                  placeholder="dev.to/settings/extensions 生成"),
        ],
    },
    "github": {
        "fields": [
            _spec("token", "Personal Access Token", secret=True, required=True,
                  placeholder="ghp_…（PAT 勾 repo 权限）"),
            _spec("owner", "仓库 owner", required=True, placeholder="GitHub 用户名"),
            _spec("repo", "仓库名", required=True, placeholder="用户名.github.io"),
            _spec("branch", "分支", required=False, placeholder="main"),
            _spec("path_prefix", "文章目录", required=False, placeholder="_posts"),
            _spec("site_base", "站点域名", required=False, placeholder="用户名.github.io"),
        ],
    },
    "wechat": {
        "fields": [
            _spec("appid", "AppID", required=True, placeholder="wx…"),
            _spec("secret", "AppSecret", secret=True, required=True,
                  placeholder="公众号后台 → 设置与开发 → 基本配置"),
        ],
    },
    "telegraph": {
        "fields": [
            _spec("token", "Access Token", secret=True, required=False,
                  placeholder="可留空，首次发布自动创建"),
            _spec("author_name", "作者名", required=False, placeholder="Harbor"),
        ],
    },
}

PLATFORM_NAMES = {
    "cnblogs": "博客园", "metaweblog": "自建博客", "51cto": "51CTO博客",
    "devto": "Dev.to", "github": "GitHub Pages", "wechat": "微信公众号",
    "telegraph": "Telegraph",
}


def _config_path() -> Path:
    return config_file()


def _read(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"config.json 解析失败，拒绝读写：{exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("config.json 顶层必须是 JSON 对象")
    return data


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    try:
        from service.publishing.crypto import _restrict_key_file
        _restrict_key_file(path)
    except Exception:   # aqg: top-level boundary（权限收紧失败不阻断保存）
        pass


def _validate_endpoint(value: str) -> None:
    value = (value or "").strip()
    if not value:
        return
    if len(value) > _MAX_FIELD:
        raise ValueError("endpoint 过长")
    parsed = urlparse(value)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("endpoint 只支持 http/https")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("endpoint 不允许携带账号密码")
    if not parsed.hostname:
        raise ValueError("endpoint 缺少有效域名")


def _field_value(raw: dict, spec: dict) -> str:
    key = spec["key"]
    if key == "token" and not raw.get("token") and raw.get("password"):
        return str(raw.get("password") or "")
    return str(raw.get(key) or "")


def _item(platform: str, raw: dict) -> dict:
    spec = PLATFORM_SPECS[platform]
    fields = []
    filled = 0
    for f in spec["fields"]:
        value = _field_value(raw, f)
        if value and not _is_placeholder(value):
            filled += 1
        fields.append({
            "key": f["key"], "label": f["label"], "secret": f["secret"],
            "required": f["required"], "placeholder": f["placeholder"],
            "hint": f["hint"], "endpoint": f["endpoint"],
            "set": bool(value and not _is_placeholder(value)),
            "value": "" if f["secret"] else ("" if _is_placeholder(value) else value),
            "masked": _mask(value) if f["secret"] and value and not _is_placeholder(value) else "",
      })
    required = [f for f in fields if f["required"]]
    configured = all(f["set"] for f in required) if required else filled > 0
    if platform == "telegraph":
        configured = True  # 免注册，空 token 也能首发
    return {
        "id": platform, "name": PLATFORM_NAMES.get(platform, platform),
        "fields": fields, "configured": configured,
        "filled": filled,
    }


def get_platform_credentials() -> dict:
    cfg = _read(_config_path()) if _config_path().is_file() else {}
    raw_platforms = cfg.get("platforms") if isinstance(cfg.get("platforms"), dict) else {}
    items = []
    for platform in PLATFORM_SPECS:
        raw = raw_platforms.get(platform)
        items.append(_item(platform, raw if isinstance(raw, dict) else {}))
    return {"platforms": items, "file": "config.json"}


def update_platform_credentials(platform: str, fields: dict) -> dict:
    if platform not in PLATFORM_SPECS:
        raise ValueError(f"不支持在界面配置的平台：{platform}")
    if not isinstance(fields, dict):
        raise ValueError("fields 必须是对象")
    allowed = {f["key"]: f for f in PLATFORM_SPECS[platform]["fields"]}
    for key in fields:
        if key not in allowed:
            raise ValueError(f"{platform} 不支持字段：{key}")

    path = _config_path()
    cfg = _read(path) if path.is_file() else {}
    platforms = cfg.get("platforms")
    if not isinstance(platforms, dict):
        platforms = {}
    raw = platforms.get(platform)
    if not isinstance(raw, dict):
        raw = {}

    changed = False
    for key, value in fields.items():
        spec = allowed[key]
        if value is None:
            continue
        text = str(value).strip()
        if len(text) > _MAX_FIELD:
            raise ValueError(f"{spec['label']} 过长")
        if spec["endpoint"]:
            _validate_endpoint(text)
        if spec["secret"]:
            if text == "":
                raw.pop(key, None)
                if key == "token":
                    raw.pop("password", None)
                changed = True
            elif text.startswith("****") or "\u2026" in text:
                continue  # 回显掩码误提交时不动原值
            else:
                raw[key] = text
                if key == "token":
                    raw.pop("password", None)
                changed = True
        else:
            if text:
                raw[key] = text
            else:
                raw.pop(key, None)
            changed = True

    if changed:
        if raw:
            platforms[platform] = raw
        else:
            platforms.pop(platform, None)
        if platforms:
            cfg["platforms"] = platforms
        elif "platforms" in cfg:
            cfg.pop("platforms", None)
        _atomic_write(path, cfg)

    items = {p["id"]: p for p in get_platform_credentials()["platforms"]}
    return items[platform]
