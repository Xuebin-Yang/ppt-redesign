#!/usr/bin/env python3
"""Runtime checks shared by ppt-redesign scripts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAMP_NAME = "ppt-redesign-update-check.json"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def is_git_install() -> bool:
    return (ROOT / ".git").exists()


def git_dir() -> Path:
    raw = git("rev-parse", "--git-dir").stdout.strip()
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def current_head() -> str:
    return git("rev-parse", "HEAD").stdout.strip()


def has_local_changes() -> bool:
    return bool(git("status", "--porcelain").stdout.strip())


def mark_update_checked(upstream: str) -> None:
    if not is_git_install():
        return
    stamp = {"mode": "git", "head": current_head(), "upstream": upstream}
    (git_dir() / STAMP_NAME).write_text(json.dumps(stamp, ensure_ascii=False), encoding="utf-8")


def ensure_update_checked_for_git_install() -> None:
    if not is_git_install():
        return
    if has_local_changes():
        return

    stamp_path = git_dir() / STAMP_NAME
    try:
        stamp = json.loads(stamp_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        sys.exit("❌ Git 安装版必须先运行：python3 scripts/update_skill.py")

    if stamp.get("mode") != "git" or stamp.get("head") != current_head():
        sys.exit("❌ 当前版本尚未完成更新检查，请先运行：python3 scripts/update_skill.py")
