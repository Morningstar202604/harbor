# -*- coding: utf-8 -*-
"""首次使用向导 REST：建档案 → 渲染 → 自检，路径与隐私边界。"""

from pathlib import Path


def _use_tmp_profiles(monkeypatch, tmp_path):
    root = tmp_path / "profiles"
    monkeypatch.setenv("HARBOR_PROFILES_DIR", str(root))
    return root


def test_state_lists_templates_and_mcp_config(client, monkeypatch, tmp_path):
    _use_tmp_profiles(monkeypatch, tmp_path)
    r = client.get("/api/v1/hub/onboarding/state")
    assert r.status_code == 200
    body = r.json()
    ids = [t["id"] for t in body["templates"]]
    assert {"cnblogs", "zhihu", "csdn", "juejin"} <= set(ids)
    platform_ids = {p["id"] for p in body["platforms"]}
    assert {"bilibili", "toutiao", "xiaohongshu", "wechat"} <= platform_ids
    assert body["needs_setup"] is True
    assert body["profiles"] == []
    cfg = body["mcp"]["config"]["mcpServers"]["harbor"]
    assert cfg["args"][0].endswith("mcp_server.py")
    assert "HUB_DATA_DIR" in cfg["env"]


def test_init_renders_personal_profile_and_check_passes(client, monkeypatch, tmp_path):
    root = _use_tmp_profiles(monkeypatch, tmp_path)
    r = client.post("/api/v1/hub/onboarding/init", json={
        "name": "demo", "platforms": ["cnblogs", "juejin"],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "demo"
    assert body["profile"] == "profiles/demo/profile.yaml"
    assert (root / "demo" / "profile.yaml").is_file()
    assert (root / "demo" / "progress").is_dir()
    assert {Path(p).stem for p in body["playbooks"]} == {"cnblogs", "juejin"}

    state = client.get("/api/v1/hub/onboarding/state").json()
    assert state["needs_setup"] is False
    assert state["profiles"][0]["name"] == "demo"
    assert state["profiles"][0]["platforms"] == ["cnblogs", "juejin"]

    check = client.post("/api/v1/hub/onboarding/check", json={"name": "demo"})
    assert check.status_code == 200
    assert check.json()["ok"] is True


def test_init_allows_platform_without_sop_template(client, monkeypatch, tmp_path):
    root = _use_tmp_profiles(monkeypatch, tmp_path)
    r = client.post("/api/v1/hub/onboarding/init", json={
        "name": "demo", "platforms": ["cnblogs", "bilibili"],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["platforms"] == ["cnblogs", "bilibili"]
    assert [Path(p).stem for p in body["playbooks"]] == ["cnblogs"]
    assert (root / "demo" / "profile.yaml").is_file()


def test_rerender_endpoint_keeps_profile_accounts(client, monkeypatch, tmp_path):
    root = _use_tmp_profiles(monkeypatch, tmp_path)
    client.post("/api/v1/hub/onboarding/init", json={
        "name": "demo", "platforms": ["cnblogs"],
    })
    profile_path = root / "demo" / "profile.yaml"
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8").replace("your-cnblogs-id", "real-account"),
        encoding="utf-8",
    )
    (root / "demo" / "playbooks" / "cnblogs.md").write_text("坏了\n", encoding="utf-8")

    r = client.post("/api/v1/hub/onboarding/rerender", json={"name": "demo"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["check"]["ok"] is True
    assert body["platforms"] == ["cnblogs"]
    assert "real-account" in profile_path.read_text(encoding="utf-8")


def test_init_rejects_bad_name_and_duplicate(client, monkeypatch, tmp_path):
    _use_tmp_profiles(monkeypatch, tmp_path)
    bad = client.post("/api/v1/hub/onboarding/init", json={"name": "../etc"})
    assert bad.status_code == 422

    first = client.post("/api/v1/hub/onboarding/init", json={"name": "demo"})
    assert first.status_code == 200
    again = client.post("/api/v1/hub/onboarding/init", json={"name": "demo"})
    assert again.status_code == 422
    assert "已存在" in again.json()["message"]
