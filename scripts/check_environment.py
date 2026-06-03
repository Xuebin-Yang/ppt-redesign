#!/usr/bin/env python3
"""检查 skill 所需的本地 PDF 处理能力。"""

from __future__ import annotations

import importlib.util
import sys

from runtime_guard import ensure_update_checked_for_git_install
from skill_runtime import add_private_deps, ensure_pymupdf


def has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> None:
    ensure_update_checked_for_git_install()
    add_private_deps()
    has_fitz = has_module("fitz")
    has_pillow = has_module("PIL")

    print("PPT 重设计 skill 环境自检")
    print(f"- Python: {sys.executable}")
    print(f"- PyMuPDF: {'可用' if has_fitz else '未安装'}")
    print(f"- Pillow: {'可用' if has_pillow else '未安装'}")

    if has_fitz:
        print("✅ 本地 PDF 拆分与合成能力已就绪，无需额外安装。")
        return

    print("ℹ️  正在自动准备缺失依赖...")
    ensure_pymupdf()
    print("✅ 私有依赖已安装到当前 skill 目录，本地 PDF 拆分与合成能力已就绪。")


if __name__ == "__main__":
    main()
