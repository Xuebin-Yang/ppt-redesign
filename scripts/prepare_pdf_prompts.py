#!/usr/bin/env python3
"""为 PDF 版 PPT 准备每页 PNG 截图 + 提示词空白模板，并按每 8 页打包。

工作流：
  1. 渲染 PDF → source_pages/page-NNN.png（Agent 通过视觉读取，无需文字提取/图片检测）
  2. 生成每页空白模板  page_prompts/page-NNN.md（Agent 填写）
  3. --finalize 后合并为  batched_prompts/batch-NN.md

不直接调用生图能力；Agent 完善提示词后逐页调用 Codex 内置生图能力。
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from runtime_guard import ensure_update_checked_for_git_install
from skill_runtime import ensure_pymupdf

BATCH_SIZE = 8
LANG_CN = "中文"
LANG_EN = "English"
LANG_RE = re.compile(r"目标提示词语言：(.+)")

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


def detect_prompt_language(pdf_path: Path) -> tuple[str, str]:
    """用 PDF 文字层做轻量语言判断；最终仍以 Agent 视觉读图为准。"""
    try:
        import fitz
    except ImportError:
        ensure_pymupdf()
        import fitz

    with fitz.open(str(pdf_path)) as doc:
        text = "\n".join(page.get_text("text") for page in doc)

    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    english = len(re.findall(r"[A-Za-z]{2,}", text))
    language = LANG_CN if chinese >= english else LANG_EN
    detail = f"中文字符 {chinese}，英文词 {english}"
    return language, detail


# ──────────────────────────── 空白模板 ────────────────────────────


def page_template(num: int, total: int, prompt_language: str) -> str:
    if prompt_language == LANG_EN:
        final_prompt = """\
Create a poster image ([describe this page's core topic, such as data display / process explanation / key message]).

Style: [Write the unified visual style statement here: overall mood + color palette with hex values + typography tone + spacing + restrained flat visual language.]

Layout: [Describe a content-driven visual structure, using one main structure with only necessary supporting elements, such as color-block sections / process flow / large-number emphasis / comparison columns / timeline. Keep it flat.]

Text overview:
Page topic: [One sentence explaining what this page is about]
Main title: "[Write the exact main title]"
Other text: [List every subtitle, section title, body line, bullet, data number, caption, and corner label exactly; do not include the original page number]

Aspect ratio: landscape 16:9.
"""
    else:
        final_prompt = """\
生成一张海报图像（[用本页核心主题关键词描述，如：数据展示/流程说明/核心观点等]）。

风格：[填写：整体视觉气质 + 配色（含色值）+ 字体风格 + 空间感 + 克制的装饰语言，扁平化。风格不必刻意极简，但画面元素应简洁]

版式（可视化 + 扁平化）：[填写：结合内容语义推导排版，只选一个核心视觉结构，辅以少量必要元素；减少装饰，不铺满背景。例如纯色色块分区/流程图/大字强调/左右对比/时间轴等，不要立体/3D/拟物]

文字概览：
页面主题：[1句话说明这页讲什么]
大标题：「[写出大标题具体文案]」
其他文字：[逐一写出所有副标题、小标题、正文、列表项、数据、图注、角标等具体文案；不写原稿页码]

输出比例：横版 16:9。
"""

    return f"""\
# 第 {num:03d} 页提示词（共 {total} 页）

> **操作说明**：先 Read `source_pages/page-{num:03d}.png`，
> 视觉识别整页内容（文字 + 图片 + 布局），然后填写下方所有字段。
> 不要凭空猜测，以视觉识别结果为准。
> 目标提示词语言：{prompt_language}。最终提示词必须使用该语言；原稿中的文字内容保持原文逐一列出。

## 最终提示词

{final_prompt}
"""


# ──────────────────────────── 创建工作区 ────────────────────────────


def create_workspace(pdf_path: Path, out_dir: Path, refresh: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "page_prompts").mkdir(exist_ok=True)
    (out_dir / "batched_prompts").mkdir(exist_ok=True)

    total = render_pdf(pdf_path, out_dir, refresh)
    prompt_language, language_detail = detect_prompt_language(pdf_path)

    for i in range(1, total + 1):
        tmpl = out_dir / "page_prompts" / f"page-{i:03d}.md"
        if not tmpl.exists() or refresh:
            tmpl.write_text(page_template(i, total, prompt_language), encoding="utf-8")

    # 整体文档占位
    for fname, placeholder in [
        (
            "deck_style_brief.md",
            f"# 统一视觉风格简报\n\n目标提示词语言：{prompt_language}（粗略判断：{language_detail}）。\n\n[待 Agent 浏览全部 source_pages/*.png 后填写]\n",
        ),
        ("visual_optimization_recommendations.md", "# 整套 PPT 视觉优化建议\n\n[待 Agent 浏览全部 source_pages/*.png 后填写]\n"),
    ]:
        f = out_dir / fname
        if not f.exists() or refresh:
            f.write_text(placeholder, encoding="utf-8")

    print(f"✅ 工作区就绪：{out_dir}")
    print(f"   目标提示词语言：{prompt_language}（粗略判断：{language_detail}）")
    print(f"   下一步：依次 Read source_pages/page-NNN.png，视觉识别后填写 page_prompts/page-NNN.md")


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
        s, e = start + 1, start + len(group)
        if prompt_language == LANG_EN:
            lines = [
                f"Here are {len(group)} prompts. Use GPT-Image to generate {len(group)} images, "
                f"corresponding to source pages {s:03d}-{e:03d}. Generate each image separately and in order.\n"
            ]
        else:
            lines = [
                f"以下是 {len(group)} 份提示词，请用 GPT-Image 一次性生成 {len(group)} 张图片，"
                f"对应原 PPT 第 {s:03d} ~ {e:03d} 页。每张提示词彼此独立，请按顺序逐张生成。\n"
            ]
        for j, f in enumerate(group, 1):
            raw = f.read_text(encoding="utf-8")
            body = raw.split("## 最终提示词", 1)[1].strip() if "## 最终提示词" in raw else raw.strip()
            if prompt_language == LANG_EN:
                lines.append(f"## Image {j} (source page {start+j:03d})\n\n{body}\n")
            else:
                lines.append(f"## 第 {j} 张（原 PPT 第 {start+j:03d} 页）\n\n{body}\n")

        out_file = batched_dir / f"batch-{batch_idx:02d}.md"
        out_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"✅ {out_file.name}（{len(group)} 页）")

    shutil.rmtree(prompts_dir)
    print("✅ 已清理 page_prompts/ 中间产物")


# ──────────────────────────── CLI ────────────────────────────


if __name__ == "__main__":
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
