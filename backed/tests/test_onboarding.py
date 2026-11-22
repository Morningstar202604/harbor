# -*- coding: utf-8 -*-
"""档案初始化与模板渲染的单元测试。"""

import pytest

from service.onboarding import (
    OnboardingError, init_profile, load_profile, render_template,
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


def test_init_profile_refuses_overwrite_without_force(tmp_path):
    init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    with pytest.raises(OnboardingError, match="已存在"):
        init_profile("demo", ["cnblogs"], profiles_root=tmp_path)
    init_profile("demo", ["cnblogs"], profiles_root=tmp_path, force=True)


def test_init_profile_rejects_bad_name(tmp_path):
    with pytest.raises(OnboardingError, match="档案名"):
        init_profile("Demo Name", [], profiles_root=tmp_path)


def test_load_profile_reads_yaml(tmp_path):
    p = tmp_path / "profile.yaml"
    p.write_text("name: demo\naccounts:\n  juejin: demo-id\n", encoding="utf-8")
    data = load_profile(p)
    assert data["accounts"]["juejin"] == "demo-id"
