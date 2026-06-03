#!/usr/bin/env python3
"""为 skill 自动准备私有 Python 依赖，不修改用户的全局环境。"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

DEPS_DIR = Path(__file__).resolve().parent.parent / ".deps"


def add_private_deps() -> None:
    if DEPS_DIR.is_dir() and str(DEPS_DIR) not in sys.path:
        sys.path.insert(0, str(DEPS_DIR))


def ensure_pymupdf() -> None:
    add_private_deps()
    try:
        importlib.import_module("fitz")
        return
    except ImportError:
        pass

    print("ℹ️  首次使用：正在为当前 skill 安装私有依赖 PyMuPDF...")
    DEPS_DIR.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--target",
        str(DEPS_DIR),
        "pymupdf",
    ]
    try:
        subprocess.run(command, check=True)
    except (OSError, subprocess.CalledProcessError):
        sys.exit(
            "❌ 无法自动安装 PyMuPDF。请确认首次运行时网络可用，"
            "或手动执行：python3 -m pip install pymupdf"
        )

    add_private_deps()
    importlib.invalidate_caches()
    try:
        importlib.import_module("fitz")
    except ImportError:
        sys.exit("❌ PyMuPDF 安装完成但仍无法导入，请检查当前 Python 环境。")


add_private_deps()
