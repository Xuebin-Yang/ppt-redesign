#!/usr/bin/env python3
"""按 page-NNN 文件名顺序将逐页生成图片合成为 PDF。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from runtime_guard import ensure_update_checked_for_git_install
from skill_runtime import ensure_pymupdf

PAGE_RE = re.compile(r"^page-(\d{3})\.(png|jpg|jpeg|webp)$", re.IGNORECASE)


def collect_images(images_dir: Path) -> list[Path]:
    if not images_dir.is_dir():
        sys.exit(f"❌ 图片目录不存在：{images_dir}")

    numbered: list[tuple[int, Path]] = []
    for path in images_dir.iterdir():
        match = PAGE_RE.match(path.name)
        if match:
            numbered.append((int(match.group(1)), path))

    numbered.sort()
    if not numbered:
        sys.exit(f"❌ {images_dir} 中没有找到 page-NNN.png/jpg/jpeg/webp")

    numbers = [num for num, _ in numbered]
    expected = list(range(1, len(numbers) + 1))
    if numbers != expected:
        sys.exit(f"❌ 页码不连续：找到 {numbers}，预期 {expected}")

    return [path for _, path in numbered]


def assemble(images: list[Path], output: Path) -> None:
    try:
        import fitz
    except ImportError:
        assemble_with_pillow(images, output)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open()
    for image in images:
        pix = fitz.Pixmap(str(image))
        width, height = pix.width, pix.height
        page = doc.new_page(width=width, height=height)
        page.insert_image(page.rect, filename=str(image))
    doc.save(str(output), deflate=True)
    doc.close()


def assemble_with_pillow(images: list[Path], output: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        ensure_pymupdf()
        assemble(images, output)
        return

    output.parent.mkdir(parents=True, exist_ok=True)
    pages = []
    for image in images:
        with Image.open(image) as opened:
            pages.append(opened.convert("RGB"))

    first, *rest = pages
    first.save(output, "PDF", save_all=True, append_images=rest, resolution=144)


def main() -> None:
    ensure_update_checked_for_git_install()

    parser = argparse.ArgumentParser(description="按页码顺序将生成图片合成为 PDF")
    parser.add_argument("--images-dir", required=True, help="包含 page-NNN 图片的目录")
    parser.add_argument("--output", required=True, help="输出 PDF 路径")
    args = parser.parse_args()

    images = collect_images(Path(args.images_dir))
    assemble(images, Path(args.output))
    print(f"✅ 已合成 {len(images)} 页 → {args.output}")


if __name__ == "__main__":
    main()
