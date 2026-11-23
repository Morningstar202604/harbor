# -*- coding: utf-8 -*-
"""工作区 REST：多档案切换、表单/YAML、SOP 自定义、平台移除、API 凭据。"""

import json

import yaml


def _init(client, name="demo", platforms=("cnblogs", "juejin")):
    r = client.post("/api/v1/hub/onboarding/init", json={
        "name": name, "platforms": list(platforms),
    })
    assert r.status_code == 200, r.text
    return r.json()


def test_workspace_lists_profiles_and_active(client, monkeypatch, tmp_path):
    monkeypatch.setenv("HARBOR_PROFILES_DIR", str(tmp_path / "profiles"))
    _init(client, "demo", ["cnblogs", "juejin"])

    r = client.get("/api/v1/hub/workspace")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["active"] == "demo"
    assert body["profiles"][0]["active"] is True

    detail = client.get("/api/v1/hub/workspace/profiles/demo").json()
    assert detail["fields"]["mainline"].startswith("AI 工程")
    assert {p["id"] for p in detail["platforms"]} == {"cnblogs", "juejin"}
    assert all(p["exists"] for p in detail["playbooks"])
    assert detail["active"] is True


def test_profile_form_update_creates_backup_and_switches_active(client, monkeypatch, tmp_path):
    root = tmp_path / "profiles"
    monkeypatch.setenv("HARBOR_PROFILES_DIR", str(root))
    _init(client, "demo", ["cnblogs"])
    _init(client, "second", ["zhihu"])

    r = client.put("/api/v1/hub/workspace/profiles/demo", json={"fields": {
        "mainline": "只写 Agent 实测",
        "style": {"voice": "冷静、具体", "avoid": ["综上所述"], "min_images": 3,
                  "min_code_blocks": 2},
        "engagement": {"proactive_comments": 6, "reply_only_after": 6,
                       "max_per_author": 2, "max_follow_back": 2},
        "windows": {"active": "20:00-21:00"},
    }})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["fields"]["mainline"] == "只写 Agent 实测"
    assert body["fields"]["min_images"] == 3
    assert (root / "demo" / "profile.yaml.bak").is_file()
    data = yaml.safe_load((root / "demo" / "profile.yaml").read_text(encoding="utf-8"))
    assert data["name"] == "demo"
    assert data["mainline"] == "只写 Agent 实测"

    # 主线改了，SOP 还是旧的 -> 自检要如实报漂移，而不是假通过。
    assert body["check"]["ok"] is False
    assert any("不一致" in p for p in body["check"]["problems"])

    switched = client.put("/api/v1/hub/workspace/active", json={"name": "second"})
    assert switched.status_code == 200
    assert switched.json()["active"] == "second"
    state = client.get("/api/v1/hub/onboarding/state").json()
    assert state["active"] == "second"
    assert next(p for p in state["profiles"] if p["name"] == "second")["active"] is True


def test_profile_yaml_roundtrip_rejects_bad_name(client, monkeypatch, tmp_path):
    root = tmp_path / "profiles"
    monkeypatch.setenv("HARBOR_PROFILES_DIR", str(root))
    _init(client, "demo", ["cnblogs"])
    yaml_text = (root / "demo" / "profile.yaml").read_text(encoding="utf-8")

    r = client.put("/api/v1/hub/workspace/profiles/demo", json={
        "yaml": yaml_text.replace("name: demo", "name: hacker"), "fields": {},
    })
    assert r.status_code == 422
    assert "name" in r.json()["message"]

    ok = client.put("/api/v1/hub/workspace/profiles/demo", json={
        "yaml": yaml_text.replace("AI 工程", "AI 工程与自动化"), "fields": {},
    })
    assert ok.status_code == 200, ok.text
    assert "AI 工程与自动化" in (root / "demo" / "profile.yaml").read_text(encoding="utf-8")


def test_sop_customize_is_respected_and_can_reset(client, monkeypatch, tmp_path):
    root = tmp_path / "profiles"
    monkeypatch.setenv("HARBOR_PROFILES_DIR", str(root))
    _init(client, "demo", ["cnblogs"])

    read = client.get("/api/v1/hub/workspace/profiles/demo/playbooks/cnblogs")
    assert read.status_code == 200
    text = read.json()["markdown"]

    save = client.put("/api/v1/hub/workspace/profiles/demo/playbooks/cnblogs",
                      json={"markdown": text + "\n\n## 我的加餐\n\n只发周更实测。\n"})
    assert save.status_code == 200, save.text
    saved = save.json()
    assert saved["customized"] is True
    assert "customized: true" in saved["markdown"]

    detail = client.get("/api/v1/hub/workspace/profiles/demo").json()
    assert detail["check"]["ok"] is True          # 自定义 SOP 不算模板漂移
    assert next(p for p in detail["playbooks"] if p["platform"] == "cnblogs")["customized"] is True

    reset = client.post("/api/v1/hub/workspace/profiles/demo/playbooks/cnblogs/reset")
    assert reset.status_code == 200
    assert reset.json()["customized"] is False
    assert "我的加餐" not in reset.json()["markdown"]


def test_remove_platform_keeps_at_least_one(client, monkeypatch, tmp_path):
    root = tmp_path / "profiles"
    monkeypatch.setenv("HARBOR_PROFILES_DIR", str(root))
    _init(client, "demo", ["cnblogs", "juejin"])

    r = client.post("/api/v1/hub/workspace/profiles/demo/platforms/remove",
                    json={"platform": "juejin"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert [p["id"] for p in body["platforms"]] == ["cnblogs"]
    assert not (root / "demo" / "playbooks" / "juejin.md").exists()

    last = client.post("/api/v1/hub/workspace/profiles/demo/platforms/remove",
                       json={"platform": "cnblogs"})
    assert last.status_code == 422
    assert "至少保留一个" in last.json()["message"]


def test_platform_credentials_mask_and_write(client, monkeypatch, tmp_path):
    cfg = tmp_path / "sandbox-config.json"
    cfg.write_text(json.dumps({"platforms": {"devto": {"api_key": "old-key-123456"},
                                             "github": {"owner": "me"}}}), encoding="utf-8")
    monkeypatch.setenv("HARBOR_CONFIG_FILE", str(cfg))

    r = client.get("/api/v1/hub/platform-credentials")
    assert r.status_code == 200, r.text
    items = {p["id"]: p for p in r.json()["platforms"]}
    devto = items["devto"]
    key_field = next(f for f in devto["fields"] if f["key"] == "api_key")
    assert key_field["set"] is True
    assert key_field["value"] == ""                 # 密钥字段绝不回显
    assert "old-key" not in str(r.json())           # 摘要：全文不能出现完整密钥

    save = client.put("/api/v1/hub/platform-credentials/devto",
                      json={"fields": {"api_key": "new-key-abcdef"}})
    assert save.status_code == 200, save.text
    saved = save.json()
    key_field = next(f for f in saved["fields"] if f["key"] == "api_key")
    assert key_field["masked"].startswith("new-")
    raw = json.loads(cfg.read_text(encoding="utf-8"))
    assert raw["platforms"]["devto"]["api_key"] == "new-key-abcdef"
    assert raw["platforms"]["github"]["owner"] == "me"   # 未触及的配置原样保留

    clear = client.put("/api/v1/hub/platform-credentials/devto",
                       json={"fields": {"api_key": ""}})
    assert clear.status_code == 200
    raw = json.loads(cfg.read_text(encoding="utf-8"))
    assert "devto" not in raw["platforms"]
    assert raw["platforms"]["github"]["owner"] == "me"


def test_platform_credentials_reject_unknown_field_and_bad_endpoint(client, monkeypatch, tmp_path):
    cfg = tmp_path / "sandbox-config.json"
    cfg.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("HARBOR_CONFIG_FILE", str(cfg))

    bad = client.put("/api/v1/hub/platform-credentials/devto",
                     json={"fields": {"api_key": "x", "token": "y"}})
    assert bad.status_code == 422

    bad_url = client.put("/api/v1/hub/platform-credentials/metaweblog",
                         json={"fields": {"endpoint": "file:///etc/passwd"}})
    assert bad_url.status_code == 422
    assert "http" in bad_url.json()["message"]
