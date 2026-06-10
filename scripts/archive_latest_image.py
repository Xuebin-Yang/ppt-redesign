#!/usr/bin/env python3
"""Copy the newest Codex image_gen PNG into a deterministic workflow path."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

from runtime_guard import ensure_update_checked_for_git_install, print_version


DEFAULT_CODEX_IMAGES = Path.home() / ".codex" / "generated_images"


def default_source_root() -> Path:
    env_path = os.environ.get("CODEX_GENERATED_IMAGES_DIR") or os.environ.get("CODEX_IMAGE_GEN_DIR")
    if env_path:
        return Path(env_path).expanduser()
    return DEFAULT_CODEX_IMAGES


def newest_png(root: Path) -> Path:
    if not root.is_dir():
        sys.exit(f"❌ Codex 生图目录不存在：{root}")

    images = [path for path in root.rglob("*.png") if path.is_file()]
    if not images:
        sys.exit(f"❌ {root} 下没有找到 image_gen 生成的 PNG")

    return max(images, key=lambda path: path.stat().st_mtime_ns)


def main() -> None:
    print_version()
    ensure_update_checked_for_git_install()

    parser = argparse.ArgumentParser(description="归档最近一次 Codex image_gen 生成的 PNG")
    parser.add_argument("--output", required=True, help="目标图片路径，例如 ppt-prompts-output/style_reference/style_reference.png")
    parser.add_argument(
        "--source-root",
        default=str(default_source_root()),
        help="Codex image_gen 默认输出根目录；也可通过 CODEX_GENERATED_IMAGES_DIR 覆盖",
    )
    parser.add_argument("--min-mtime", type=float, default=None, help="可选：只接受 Unix mtime 晚于该时间的图片")
    args = parser.parse_args()

    src = newest_png(Path(args.source_root).expanduser())
    if args.min_mtime is not None and src.stat().st_mtime < args.min_mtime:
        sys.exit(f"❌ 最新图片早于本次生图开始时间，未归档：{src}")

    dst = Path(args.output)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"✅ 已归档最新 image_gen 图片：{src} → {dst}")


if __name__ == "__main__":
    main()
