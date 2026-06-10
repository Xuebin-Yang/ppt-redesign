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
LANG_RE = re.compile(r"目标提示词语言\s*[:：]\s*(中文|English)")
PROMPT_LANGUAGE_LINE_RE = re.compile(r"^\s*>?\s*(?:目标提示词语言|Prompt language)\s*[:：].*$", re.MULTILINE)
POSTER_ACTION_RE = re.compile(
    r"^\s*(?:生成一张海报图像|Create a poster image|生成一张横幅幻灯片)\s*[（(]?[^\n）)]*[）)]?\s*[。.]*\s*$",
    re.MULTILINE,
)
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")

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

风格：简约风格，配色从参考图中系统性地提取，用色精简，使用 1 种主色搭配 1-2 种辅助色。

版式：[填写：只列举一个布局名称。内容页可选如左右分栏布局、核心数字布局、流程图式布局、对比分栏布局、数据看板布局等；封面页、章节页、结束页、目录页、过渡页可选封面布局、章节页布局、结束页布局、目录页布局、过渡页布局等。不要写解释句。]

内容要求：[填写：无真实图片素材时写「画面需要呈现指定文字。」；有真实图片素材时写「画面需要呈现指定文字和图片素材。」]

文字描述：图中仅包含下列文字，不添加未列出文字：
大标题：「[写出大标题具体文案]」
其他文字：[逐一写出所有副标题、小标题、正文、列表项、数据、图注、角标等具体文案；不写原稿页码]

图片描述：[填写：若页面包含真实图片/截图/照片/插画/产品图/人像等图片素材，按「图片素材一：……」逐一描述图片内容与用途；若页面没有真实图片素材，删除本段。装饰性 icon、几何形状、线条、卡片底纹不算图片素材。]

输出比例：横版 16:9。
"""

    return f"""\
# 第 {num:03d} 页提示词（共 {total} 页）

> **操作说明**：先 Read `source_pages/page-{num:03d}.png`，视觉识别整页内容（文字 + 图片 + 布局），然后填写下方所有字段。不要凭空猜测，以视觉识别结果为准。
> 详细字段写作规范请参考 SKILL.md 中的 Hard Rules 与 Step 5「字段写作规范」。
> 目标提示词语言：[待 Agent 浏览全稿后判断：中文 / English]。最终提示词必须使用该语言；原稿中的文字内容保持原文逐一列出。

## 最终提示词

{final_prompt}
"""


# ──────────────────────────── 创建工作区 ────────────────────────────


def create_workspace(pdf_path: Path, out_dir: Path, refresh: bool = False):
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "page_prompts").mkdir(exist_ok=True)
    (out_dir / "batched_prompts").mkdir(exist_ok=True)
    (out_dir / "style_reference").mkdir(exist_ok=True)

    total = render_pdf(pdf_path, out_dir, refresh)

    for i in range(1, total + 1):
        tmpl = out_dir / "page_prompts" / f"page-{i:03d}.md"
        if not tmpl.exists() or refresh:
            tmpl.write_text(page_template(i, total), encoding="utf-8")

    style_prompt = (
        "忽略此前对话中的所有上下文、图片、文件和页面截图。"
        "只依据本提示词中从下一句开始的文字内容生成一张图片，为一个名为「[待 Agent 基于整套 PPT 主题填写名称]」的幻灯片打造一套内含多页的品牌视觉手册。"
        "品牌整体气质应当基于这套幻灯片的内容主题、行业属性和受众定位重新推导，形成清晰、统一、具有设计感的视觉世界观。\n\n"
        "视觉风格需采用大胆且具有实验性的品牌语言，包括：简洁扁平风格、现代字体设计、富有动感的视觉节奏，以及略带超现实感的图像表达。"
        "整体氛围应传递出：[待 Agent 基于原 PPT 内容填写 4-6 个关键词]。\n\n"
        "品牌手册中应体现：\n"
        "- 对核心内容与关键信息的极致关注（content obsession）\n"
        "- 多样化的视觉实验（visual experimentation）\n"
        "- 版式系统探索（layout system exploration）\n"
        "- 编辑风格表达（editorial expression）\n"
        "- 沉浸式叙事体验（immersive storytelling）\n"
        "- 跨页面品牌应用（cross-page brand application）\n\n"
        "最终呈现应构建一个自信、当代、统一且完整的品牌世界观——既易于理解与接近，又具备强烈的艺术指导感（art direction），"
        "在视觉上保持高度一致性，同时展现出高端创意工作室级别的美学标准。\n"
    )
    style_file = out_dir / "deck_style_brief.md"
    if not style_file.exists() or refresh:
        style_file.write_text(style_prompt, encoding="utf-8")

    print(f"✅ 工作区就绪：{out_dir}")
    print("   下一步：完善 deck_style_brief.md；Codex 完整模式下只传 deck_style_brief.md 正文生成 style_reference/style_reference.png，再继续逐页生图")


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
        "[逐一",
        "[写出",
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
    if match:
        prompt_language = match.group(1).strip()
    else:
        # Fallback：基于全部页面正文中 CJK 与拉丁词的占比判定主语言
        body_only = "\n".join(
            raw.split("## 最终提示词", 1)[1] if "## 最终提示词" in raw else raw
            for raw in (f.read_text(encoding="utf-8") for f in files)
        )
        cjk_count = len(CJK_RE.findall(body_only))
        latin_count = len(LATIN_WORD_RE.findall(body_only))
        prompt_language = LANG_EN if latin_count > cjk_count else LANG_CN

    for batch_idx, start in enumerate(range(0, len(files), BATCH_SIZE), 1):
        group = files[start : start + BATCH_SIZE]
        if prompt_language == LANG_EN:
            lines = [
                f"Generate {len(group)} images from the following {len(group)} prompts. "
                f"Each prompt corresponds to one image. Generate each image separately and in order.\n"
            ]
        else:
            lines = [
                f"生成 {len(group)} 张图片，下面有 {len(group)} 份提示词，"
                f"每份提示词对应一张图片。每张提示词彼此独立，请按顺序逐张生成。\n"
            ]
        for j, f in enumerate(group, 1):
            raw = f.read_text(encoding="utf-8")
            body = raw.split("## 最终提示词", 1)[1].strip() if "## 最终提示词" in raw else raw.strip()
            body = PROMPT_LANGUAGE_LINE_RE.sub("", body).strip()
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
