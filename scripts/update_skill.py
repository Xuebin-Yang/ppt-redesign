#!/usr/bin/env python3
"""Update this Codex skill from its Git remote before use."""

from __future__ import annotations

import subprocess
from pathlib import Path

from runtime_guard import mark_update_checked, print_version


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
    print_version()

    if not (ROOT / ".git").exists():
        print("ℹ️  当前为下载版安装，跳过更新检查，继续使用本地版本。")
        return

    dirty = git("status", "--porcelain").stdout.strip()
    if dirty:
        print("ℹ️  当前 skill 目录存在本地修改，跳过远端更新检查，继续使用本地版本。")
        return

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
        mark_update_checked(upstream_ref)
        print("✅ 当前已是最新版。")
        return

    base = git("merge-base", "HEAD", upstream_ref).stdout.strip()
    if base != current:
        fail("远端与本地历史发生分叉，无法安全快进更新。请手动处理后再运行。")

    pulled = git("pull", "--ff-only", check=False)
    if pulled.returncode != 0:
        fail(f"自动更新失败：{pulled.stderr.strip() or pulled.stdout.strip()}")

    new_head = git("rev-parse", "HEAD").stdout.strip()
    mark_update_checked(upstream_ref)
    print(f"✅ 已更新 skill：{current[:7]} -> {new_head[:7]}")
    print("ℹ️  本次运行请重新读取更新后的 SKILL.md，再继续执行后续流程。")


if __name__ == "__main__":
    main()
