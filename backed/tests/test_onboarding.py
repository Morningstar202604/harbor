# -*- coding: utf-8 -*-
"""档案初始化与模板渲染的单元测试。"""

from pathlib import Path

import pytest

from service.onboarding import (
    OnboardingError, add_platforms, check_profile, init_profile, load_profile,
    platform_catalog, profile_summaries, render_template, rerender_profile,
)


def test_render_substitutes_nested_values():
    profile = {
        "name": "demo",
        "accounts": {"cnblogs": "demo-id"},
        "style": {"voice": "短句", "avoid": ["首先", "其次"]},
        "engagement": {"proactive_comments": 4},
    }
    out = render_template(
        "账号 {{profile.accounts.cnblogs}}｜风格 {{profile.style}}｜额度 {{profile.engagement.proactive_comments}}",
        profile, platform="cnblogs",
    )
    assert "账号 demo-id" in out
    assert "voice=短句" in out
    assert "avoid=首先、其次" in out
    assert "额度 4" in out
    assert "{{profile." not in out


def test_render_missing_field_is_loud():
    with pytest.raises(OnboardingError, match="profile.accounts.zhihu"):
        render_template("{{profile.accounts.zhihu}}", {"name": "demo"})


def test_init_profile_creates_private_tree(tmp_path):
    result = init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    profile_path = tmp_path / "demo" / "profile.yaml"
    playbook = tmp_path / "demo" / "playbooks" / "cnblogs.md"
    assert profile_path.is_file()
    assert playbook.is_file()
    assert (tmp_path / "demo" / "progress").is_dir()
    assert "profiles/demo" in profile_path.read_text(encoding="utf-8")
    assert "{{profile." not in playbook.read_text(encoding="utf-8")
    assert result["name"] == "demo"
    assert load_profile(profile_path)["platforms"] == ["cnblogs"]


def test_init_profile_refuses_overwrite_without_force(tmp_path):
    init_profile("demo", ["cnblogs", "juejin"], profiles_root=tmp_path)
    with pytest.raises(OnboardingError, match="已存在"):
        init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    init_profile("demo", ["cnblogs"], profiles_root=tmp_path, force=True)
    # 覆盖重建只保留这次勾选的平台，旧副本不能残留。
    assert not (tmp_path / "demo" / "playbooks" / "juejin.md").exists()
    assert load_profile(tmp_path / "demo" / "profile.yaml")["platforms"] == ["cnblogs"]


def test_add_platforms_keeps_accounts_and_renders_new_sop(tmp_path):
    """给旧档案加平台只改 platforms 行，账号与已有 SOP 不能被冲掉。"""
    init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    profile_path = tmp_path / "demo" / "profile.yaml"
    before = profile_path.read_text(encoding="utf-8")
    assert "platforms: [cnblogs]" in before
    assert "your-cnblogs-id" in before

    result = add_platforms("demo", ["bilibili", "csdn"], profiles_root=tmp_path)
    after = profile_path.read_text(encoding="utf-8")
    assert result["platforms"] == ["cnblogs", "bilibili", "csdn"]
    assert result["added"] == ["bilibili", "csdn"]
    assert result["sop_platforms"] == ["cnblogs", "bilibili", "csdn"]
    assert "platforms: [cnblogs, bilibili, csdn]" in after
    assert "your-cnblogs-id" in after
    assert (tmp_path / "demo" / "playbooks" / "csdn.md").is_file()
    assert (tmp_path / "demo" / "playbooks" / "bilibili.md").is_file()
    assert check_profile("demo", profiles_root=tmp_path)["ok"] is True

    # 重复添加不产生重复项，也不重写已有 SOP。
    again = add_platforms("demo", ["csdn"], profiles_root=tmp_path)
    assert again["added"] == []
    assert again["platforms"] == ["cnblogs", "bilibili", "csdn"]


def test_add_platforms_handles_block_style_and_unknown(tmp_path):
    init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    profile_path = tmp_path / "demo" / "profile.yaml"
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8").replace(
            "platforms: [cnblogs]", "platforms:\n  - cnblogs\n"),
        encoding="utf-8",
    )
    result = add_platforms("demo", ["juejin"], profiles_root=tmp_path)
    assert result["platforms"] == ["cnblogs", "juejin"]
    assert "platforms: [cnblogs, juejin]" in profile_path.read_text(encoding="utf-8")

    with pytest.raises(OnboardingError, match="不支持的平台"):
        add_platforms("demo", ["not-a-real-platform"], profiles_root=tmp_path)


def test_check_flags_missing_and_stale_copies(tmp_path):
    init_profile("demo", ["cnblogs", "juejin"], profiles_root=tmp_path)
    (tmp_path / "demo" / "playbooks" / "cnblogs.md").unlink()
    with open(tmp_path / "demo" / "playbooks" / "juejin.md", "a", encoding="utf-8") as f:
        f.write("\n手改的一行\n")
    result = check_profile("demo", profiles_root=tmp_path)
    assert result["ok"] is False
    assert any("cnblogs.md" in p and "缺少" in p for p in result["problems"])
    assert any("juejin.md" in p and "不一致" in p for p in result["problems"])
    assert result["platforms"] == ["cnblogs", "juejin"]


def test_rerender_repairs_sops_without_touching_profile(tmp_path):
    init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    profile_path = tmp_path / "demo" / "profile.yaml"
    text = profile_path.read_text(encoding="utf-8")
    profile_path.write_text(text.replace("your-cnblogs-id", "real-account"),
                            encoding="utf-8")
    (tmp_path / "demo" / "playbooks" / "cnblogs.md").write_text("坏了\n", encoding="utf-8")

    result = rerender_profile("demo", profiles_root=tmp_path)
    assert result["platforms"] == ["cnblogs"]
    assert check_profile("demo", profiles_root=tmp_path)["ok"] is True
    assert "real-account" in profile_path.read_text(encoding="utf-8")
    assert "real-account" in (tmp_path / "demo" / "playbooks" / "cnblogs.md").read_text(encoding="utf-8")


def test_profile_summaries_keeps_declared_platform_when_copy_missing(tmp_path):
    init_profile("demo", ["cnblogs", "juejin"], profiles_root=tmp_path)
    (tmp_path / "demo" / "playbooks" / "juejin.md").unlink()
    summary = profile_summaries(profiles_root=tmp_path)[0]
    assert summary["platforms"] == ["cnblogs", "juejin"]


def test_init_profile_rejects_bad_name(tmp_path):
    with pytest.raises(OnboardingError, match="档案名"):
        init_profile("Demo Name", [], profiles_root=tmp_path)


def test_platform_catalog_covers_all_adapters():
    """向导平台清单来自适配器注册表，15 个平台都带一份可读 SOP。"""
    rows = platform_catalog()
    ids = {r["id"] for r in rows}
    assert len(ids) >= 15
    assert {"bilibili", "toutiao", "xiaohongshu", "wechat", "oschina"} <= ids
    by_id = {r["id"]: r for r in rows}
    assert all(r["has_template"] is True for r in rows)
    assert by_id["cnblogs"]["recommended"] is True
    assert by_id["bilibili"]["recommended"] is False
    assert by_id["bilibili"]["needs_browser"] is True
    assert by_id["cnblogs"]["capabilities"]["publish"] is True


def test_init_renders_sop_for_every_selected_platform(tmp_path):
    """B站这类后接入平台也要有自己的 SOP，不能只有登录卡没有动作说明。"""
    result = init_profile("demo", ["cnblogs", "bilibili"], profiles_root=tmp_path)
    assert result["platforms"] == ["cnblogs", "bilibili"]
    assert result["sop_platforms"] == ["cnblogs", "bilibili"]
    assert [Path(p).stem for p in result["playbooks"]] == ["cnblogs", "bilibili"]
    profile = load_profile(tmp_path / "demo" / "profile.yaml")
    assert profile["platforms"] == ["cnblogs", "bilibili"]
    assert profile_summaries(profiles_root=tmp_path)[0]["platforms"] == ["cnblogs", "bilibili"]
    assert check_profile("demo", profiles_root=tmp_path)["ok"] is True


def test_all_15_templates_render_and_self_check(tmp_path):
    """不能只给 4 个平台写 SOP；15 个都要能渲染、能自检。"""
    from service.onboarding import template_platforms
    wanted = template_platforms()
    assert len(wanted) == 15
    result = init_profile("all15", wanted, profiles_root=tmp_path)
    assert result["platforms"] == wanted
    assert result["sop_platforms"] == wanted
    assert len(result["playbooks"]) == 15
    assert check_profile("all15", profiles_root=tmp_path)["ok"] is True


def test_init_rejects_unknown_non_template_platform(tmp_path):
    with pytest.raises(OnboardingError, match="不支持的平台"):
        init_profile("demo", ["not-a-real-platform"], profiles_root=tmp_path)


def test_load_profile_reads_yaml(tmp_path):
    p = tmp_path / "profile.yaml"
    p.write_text("name: demo\naccounts:\n  juejin: demo-id\n", encoding="utf-8")
    data = load_profile(p)
    assert data["accounts"]["juejin"] == "demo-id"

def test_profiles_root_follows_data_dir(monkeypatch, tmp_path):
    """桌面版只设 HUB_DATA_DIR 时，档案必须落可写数据目录，不能写安装目录。"""
    from service.onboarding import default_profiles_root
    monkeypatch.delenv("HARBOR_PROFILES_DIR", raising=False)
    monkeypatch.setenv("HUB_DATA_DIR", str(tmp_path / "appdata"))
    assert default_profiles_root() == tmp_path / "appdata" / "profiles"
