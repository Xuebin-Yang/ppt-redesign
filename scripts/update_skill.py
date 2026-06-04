#!/usr/bin/env python3
"""Update this Codex skill from its Git remote before use."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from runtime_guard import mark_update_checked, print_version


ROOT = Path(__file__).resolve().parents[1]
REPO_URL = "https://github.com/Xuebin-Yang/ppt-redesign.git"
MAIN_BRANCH = "main"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def git_bytes(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        capture_output=True,
    )


def fail(message: str, code: int = 1) -> None:
    print(f"❌ {message}")
    raise SystemExit(code)


def remote_tree_matches_local(remote_ref: str) -> bool:
    files = git("ls-tree", "-r", "--name-only", remote_ref, check=False)
    if files.returncode != 0:
        return False

    for rel_path in files.stdout.splitlines():
        local_file = ROOT / rel_path
        if not local_file.is_file():
            return False
        remote_file = git_bytes("show", f"{remote_ref}:{rel_path}", check=False)
        if remote_file.returncode != 0 or local_file.read_bytes() != remote_file.stdout:
            return False
    return True


def bootstrap_git_install() -> bool:
    print("ℹ️  当前 skill 没有 Git 元数据，尝试初始化以支持后续自动更新...")
    git_dir = ROOT / ".git"

    try:
        if git("init", check=False).returncode != 0:
            return False
        if git("remote", "get-url", "origin", check=False).returncode != 0:
            if git("remote", "add", "origin", REPO_URL, check=False).returncode != 0:
                return False

        fetched = git("fetch", "--depth", "1", "origin", MAIN_BRANCH, check=False)
        if fetched.returncode != 0:
            return False

        remote_ref = f"origin/{MAIN_BRANCH}"
        if not remote_tree_matches_local(remote_ref):
            print("⚠️  当前目录内容与远端版本不同，无法安全自动转为 Git 安装版。")
            print("   本次继续使用本地版本；若需要自动更新，请手动重新安装 Git clone 版。")
            return False

        if git("checkout", "-B", MAIN_BRANCH, remote_ref, check=False).returncode != 0:
            return False
        git("branch", "--set-upstream-to", remote_ref, MAIN_BRANCH, check=False)
        print("✅ 已将当前 skill 安全转换为 Git 安装版，后续可自动检查更新。")
        return True
    finally:
        if git_dir.exists() and git("rev-parse", "--verify", "HEAD", check=False).returncode != 0:
            shutil.rmtree(git_dir, ignore_errors=True)


def main() -> None:
    print_version()

    if not (ROOT / ".git").exists():
        if not bootstrap_git_install():
            print("ℹ️  当前为下载版安装，跳过更新检查，继续使用本地版本。")
            return

    dirty = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
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
