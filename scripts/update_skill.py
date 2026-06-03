#!/usr/bin/env python3
"""Update this Codex skill from its Git remote before use."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def fail(message: str, code: int = 1) -> None:
    print(f"❌ {message}")
    raise SystemExit(code)


def main() -> None:
    if not (ROOT / ".git").exists():
        fail(
            "当前 skill 不是通过 Git 仓库安装，无法自动更新。"
            "请使用 git clone https://github.com/Xuebin-Yang/ppt-redesign.git "
            "~/.codex/skills/ppt-redesign 重新安装。"
        )

    dirty = git("status", "--porcelain").stdout.strip()
    if dirty:
        fail("当前 skill 目录存在本地未提交改动，为避免覆盖，已停止自动更新。")

    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", check=False)
    if upstream.returncode != 0:
        fail("当前分支没有上游远端，请设置 origin/main 后再自动更新。")

    current = git("rev-parse", "HEAD").stdout.strip()
    print("ℹ️  正在检查 ppt-redesign skill 是否有更新...")
    fetched = git("fetch", "--prune", check=False)
    if fetched.returncode != 0:
        fail(f"无法连接远端仓库检查更新：{fetched.stderr.strip() or fetched.stdout.strip()}")

    upstream_ref = upstream.stdout.strip()
    remote = git("rev-parse", upstream_ref).stdout.strip()
    if current == remote:
        print("✅ 当前已是最新版。")
        return

    base = git("merge-base", "HEAD", upstream_ref).stdout.strip()
    if base != current:
        fail("远端与本地历史发生分叉，无法安全快进更新。请手动处理后再运行。")

    pulled = git("pull", "--ff-only", check=False)
    if pulled.returncode != 0:
        fail(f"自动更新失败：{pulled.stderr.strip() or pulled.stdout.strip()}")

    new_head = git("rev-parse", "HEAD").stdout.strip()
    print(f"✅ 已更新 skill：{current[:7]} -> {new_head[:7]}")
    print("ℹ️  本次运行请重新读取更新后的 SKILL.md，再继续执行后续流程。")


if __name__ == "__main__":
    main()
