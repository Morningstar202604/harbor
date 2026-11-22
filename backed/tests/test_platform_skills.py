# -*- coding: utf-8 -*-
"""平台技能卡：登录后 AI 必须拿得到动作说明。"""

import pytest

from service.onboarding import TEMPLATE_DIR, template_platforms
from service.platform_skills import get_platform_skill


def test_every_platform_has_a_skill_card():
    ids = template_platforms()
    assert len(ids) == 15
    for pid in ids:
        assert (TEMPLATE_DIR / f"{pid}.md").is_file()
        skill = get_platform_skill(pid, accounts=[])
        assert skill["id"] == pid
        assert skill["skill_markdown"].startswith("---")
        assert len(skill["skill_markdown"]) > 500
        assert skill["post_login_steps"]
        assert skill["limitations"]


def test_bilibili_skill_reports_draft_requirement_and_login_state():
    skill = get_platform_skill("bilibili", accounts=[
        {"platform": "bilibili", "account": "default", "status": "logined"},
    ])
    assert skill["account_status"] == "online"
    assert skill["recommended_draft"] is True
    assert any("没有已发布文章列表接口" in item for item in skill["limitations"])
    assert "分区" in skill["skill_markdown"]


def test_github_skill_says_no_draft():
    skill = get_platform_skill("github", accounts=[])
    assert skill["recommended_draft"] is False
    assert any("没有草稿箱" in item for item in skill["limitations"])


def test_unknown_platform_raises():
    with pytest.raises(ValueError, match="没有这个平台"):
        get_platform_skill("not-a-real-platform")
