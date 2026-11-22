#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""渲染个人 playbook：模板 + profiles/<name>/profile.yaml → profiles/<name>/playbooks/。

用法::

    python scripts/render_playbook.py --profile demo              # 档案声明的平台（旧档案退回全部模板）
    python scripts/render_playbook.py --profile demo --platform juejin
    python scripts/render_playbook.py --profile demo --check     # 只比对，过期退出 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "backed"))

from service.onboarding import (  # noqa: E402
    PROFILES_ROOT, TEMPLATE_DIR, load_profile, render_template, template_platforms,
)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="渲染个人 playbook")
    ap.add_argument("--profile", required=True, help="档案名或 profile.yaml 路径")
    ap.add_argument("--platform", action="append", default=[],
                    help="可重复；默认渲染档案 platforms 里声明的平台")
    ap.add_argument("--out-dir", default="", help="输出目录（默认 profiles/<name>/playbooks）")
    ap.add_argument("--check", action="store_true", help="只比对，不写文件")
    args = ap.parse_args(argv)

    raw = Path(args.profile)
    if raw.is_file():
        profile_path, name = raw, raw.parent.name
    else:
        name, profile_path = args.profile, PROFILES_ROOT / args.profile / "profile.yaml"
    profile = load_profile(profile_path)

    declared = profile.get("platforms")
    platforms = args.platform or (
        [str(p) for p in declared] if isinstance(declared, list) and declared
        else template_platforms()
    )
    out_dir = Path(args.out_dir) if args.out_dir else PROFILES_ROOT / name / "playbooks"

    missing_tpl = [p for p in platforms if not (TEMPLATE_DIR / f"{p}.md").is_file()]
    if missing_tpl:
        print(f"没有这些平台的模板：{', '.join(missing_tpl)}")
        return 2

    problems: list[str] = []
    for platform in platforms:
        fresh = render_template(
            (TEMPLATE_DIR / f"{platform}.md").read_text(encoding="utf-8"),
            profile, platform=platform,
        )
        dst = out_dir / f"{platform}.md"
        if args.check:
            if not dst.is_file():
                problems.append(f"缺失：{dst}")
            elif dst.read_text(encoding="utf-8") != fresh:
                problems.append(f"过期：{dst}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(fresh, encoding="utf-8")
        print(f"✓ {dst}")

    if args.check:
        if problems:
            print("个人 playbook 与档案/模板不一致：")
            for p in problems:
                print("  " + p)
            print("跑 `python scripts/render_playbook.py --profile <name>` 重新生成。")
            return 1
        print(f"OK  {len(platforms)} 份 playbook 与档案一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
