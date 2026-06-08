#!/usr/bin/env python3
"""为 PDF 版 PPT 准备每页 PNG 截图 + 提示词空白模板，并按每 8 页打包。

工作流：
  1. 渲染 PDF → source_pages/page-NNN.png（Agent 通过视觉读取，无需文字提取/图片检测）
  2. 生成每页空白模板  page_prompts/page-NNN.md（Agent 填写）
  3. --finalize 后合并为  batched_prompts/batch-NN.md

不直接调用生图能力；Agent 完善提示词后可逐页调用当前 Agent 自带生图能力。
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from runtime_guard import ensure_update_checked_for_git_install, print_version
from skill_runtime import ensure_pymupdf

BATCH_SIZE = 8
LANG_CN = "中文"
LANG_EN = "English"
LANG_RE = re.compile(r"目标提示词语言：(.+)")
PROMPT_LANGUAGE_LINE_RE = re.compile(r"^\s*(?:目标提示词语言|Prompt language)\s*[:：].*$", re.MULTILINE)
POSTER_ACTION_RE = re.compile(
    r"^\s*(?:生成一张海报图像|Create a poster image)\s*[（(][^）)]*[）)]\s*[。.]*\s*$",
    re.MULTILINE,
)

# ──────────────────────────── PDF 渲染 ────────────────────────────


def render_pdf(pdf_path: Path, out_dir: Path, refresh: bool = False) -> int:
    """将 PDF 每页渲染为 2× PNG，返回总页数。"""
    try:
        import fitz
    except ImportError:
        ensure_pymupdf()
        import fitz

    pages_dir = out_dir / "source_pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    total = len(doc)
    mat = fitz.Matrix(2, 2)

    for i, page in enumerate(doc):
        png = pages_dir / f"page-{i+1:03d}.png"
        if not png.exists() or refresh:
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(str(png))

    doc.close()
    print(f"✅ 渲染完成：{total} 页 → {pages_dir}")
    return total


# ──────────────────────────── 空白模板 ────────────────────────────


def page_template(num: int, total: int) -> str:
    final_prompt = """\
横幅幻灯片

风格：[填写：只给大方向。整体气质 + 字体情绪 + 结构母题 + 2-4 个核心颜色名称与色彩角色，例如深蓝作为主色、米白作为背景色、金橙作为强调色。中文输出，不写十六进制色值，不把颜色写成冗长色表。不写纹理、材质、阴影、具体图标、线条类型、背景图案等细节装饰。]

版式：[填写：只给大方向。一个核心视觉结构 + 主要元素大致位置 + 色彩分区，整体采用简洁扁平的横版幻灯片布局；优先时间轴、金字塔、流程图、对比分栏、循环图等清晰图形化结构。不写节点细节、图标类型、装饰线、渐变、阴影、纹理等元素级装饰。]

文字概览：
仅呈现下列明确文字，不添加未列出的文字。
大标题：「[写出大标题具体文案]」
其他文字：[逐一写出所有副标题、小标题、正文、列表项、数据、图注、角标等具体文案；不写原稿页码]

输出比例：横版 16:9。
"""

    return f"""\
# 第 {num:03d} 页提示词（共 {total} 页）

> **操作说明**：先 Read `source_pages/page-{num:03d}.png`，
> 视觉识别整页内容（文字 + 图片 + 布局），然后填写下方所有字段。
> 不要凭空猜测，以视觉识别结果为准。
> 最终提示词正文第一行必须只写「横幅幻灯片」五个字，用来声明图片类型。
> 写最终提示词前先做版式审查：风格与版式都只给大方向；版式必须是简洁图形化的横版幻灯片布局，例如时间轴、金字塔、流程图、对比分栏、循环图等。
> 目标提示词语言：[待 Agent 浏览全稿后判断：中文 / English]。最终提示词必须使用该语言；原稿中的文字内容保持原文逐一列出。

## 最终提示词

{final_prompt}
"""


# ──────────────────────────── 创建工作区 ────────────────────────────


def create_workspace(pdf_path: Path, out_dir: Path, refresh: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "page_prompts").mkdir(exist_ok=True)
    (out_dir / "batched_prompts").mkdir(exist_ok=True)

    total = render_pdf(pdf_path, out_dir, refresh)

    for i in range(1, total + 1):
        tmpl = out_dir / "page_prompts" / f"page-{i:03d}.md"
        if not tmpl.exists() or refresh:
            tmpl.write_text(page_template(i, total), encoding="utf-8")

    # 整体文档占位
    for fname, placeholder in [
        (
            "deck_style_brief.md",
            "# 统一视觉风格简报\n\n目标提示词语言：[待 Agent 浏览全部 source_pages/*.png 后判断：中文 / English]\n\n[待 Agent 浏览全部 source_pages/*.png 后填写]\n",
        ),
        ("visual_optimization_recommendations.md", "# 整套 PPT 视觉优化建议\n\n[待 Agent 浏览全部 source_pages/*.png 后填写]\n"),
    ]:
        f = out_dir / fname
        if not f.exists() or refresh:
            f.write_text(placeholder, encoding="utf-8")

    print(f"✅ 工作区就绪：{out_dir}")
    print("   下一步：浏览 source_pages 判断目标提示词语言，再依次 Read page-NNN.png 填写 page_prompts/page-NNN.md")


# ──────────────────────────── 合批 ────────────────────────────


def finalize(out_dir: Path):
    prompts_dir = out_dir / "page_prompts"
    batched_dir = out_dir / "batched_prompts"
    batched_dir.mkdir(exist_ok=True)

    files = sorted(prompts_dir.glob("page-*.md"))
    if not files:
        sys.exit(f"❌ {prompts_dir} 中没有找到 page-*.md 文件")

    # 检查是否有未填写的占位符
    placeholders = [
        "[填写",
        "[待 Agent",
        "[列举",
        "[写出",
        "[1句话",
        "[describe",
        "[Write",
        "[List",
        "[One sentence",
    ]
    incomplete = []
    for f in files:
        content = f.read_text(encoding="utf-8")
        if any(p in content for p in placeholders):
            incomplete.append(f.name)
    if incomplete:
        print(f"⚠️  以下文件还有未填写的占位符，请补全后再合批：")
        for name in incomplete:
            print(f"   · {name}")
        sys.exit(1)

    first_content = files[0].read_text(encoding="utf-8")
    match = LANG_RE.search(first_content)
    prompt_language = match.group(1).strip() if match else LANG_CN

    for batch_idx, start in enumerate(range(0, len(files), BATCH_SIZE), 1):
        group = files[start : start + BATCH_SIZE]
        if prompt_language == LANG_EN:
            lines = [
                f"Here are {len(group)} prompts. Use an available image generation model, such as GPT-Image, to generate {len(group)} images, "
                f"one image per prompt. Generate each image separately and in order.\n"
            ]
        else:
            lines = [
                f"以下是 {len(group)} 份提示词，请用可用的生图模型（如 GPT-Image）生成 {len(group)} 张图片，"
                f"每份提示词对应一张图片。每张提示词彼此独立，请按顺序逐张生成。\n"
            ]
        for j, f in enumerate(group, 1):
            raw = f.read_text(encoding="utf-8")
            body = raw.split("## 最终提示词", 1)[1].strip() if "## 最终提示词" in raw else raw.strip()
            body = PROMPT_LANGUAGE_LINE_RE.sub("", body)
            body = POSTER_ACTION_RE.sub("", body).strip()
            if prompt_language == LANG_EN:
                lines.append(f"## Image {j}\n\n{body}\n")
            else:
                lines.append(f"## 第 {j} 张\n\n{body}\n")

        out_file = batched_dir / f"batch-{batch_idx:02d}.md"
        out_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"✅ {out_file.name}（{len(group)} 页）")

    shutil.rmtree(prompts_dir)
    print("✅ 已清理 page_prompts/ 中间产物")


# ──────────────────────────── CLI ────────────────────────────


if __name__ == "__main__":
    print_version()
    ensure_update_checked_for_git_install()

    parser = argparse.ArgumentParser(description="PPT 提示词重设计工具（仅输出提示词）")
    parser.add_argument("pdf", nargs="?", help="输入 PDF 路径（--finalize 时可省略）")
    parser.add_argument("--out", required=True, help="输出目录")
    parser.add_argument("--refresh", action="store_true", help="强制重新渲染并覆盖已有模板")
    parser.add_argument("--finalize", action="store_true", help="将所有 page_prompts/ 合批为 batched_prompts/")
    args = parser.parse_args()

    if args.finalize:
        finalize(Path(args.out))
    else:
        if not args.pdf:
            sys.exit("❌ 请提供 PDF 文件路径")
        create_workspace(Path(args.pdf), Path(args.out), args.refresh)
