# ppt-redesign v2.0

一个面向 PPT 视觉重设计的 Codex Skill：输入从 PowerPoint/PPT/PPTX 导出的 PDF，先视觉识别每页内容，生成统一风格参考图和逐页生图提示词，再基于同一张风格参考图逐页生成全新幻灯片图片，最终合成为 `redesigned_deck.pdf`。

v2.0 是一次重要升级：默认完整流程被拆成两个阶段。第一阶段完成 PDF 拆分、页面识别、风格参考图生成和提示词合批；然后 Codex 会停下来等待用户手动回复 **“继续”**。用户回复后，才会进入第二阶段，新开一个 Codex 会话逐页生图并合成 PDF。

## 为什么分成两个阶段

- 第一阶段专注分析和提示词资产：`deck_style_brief.md`、`style_reference/style_reference.png`、`batched_prompts/batch-XX.md`。
- 中途要求用户回复 **“继续”**，让用户可以先确认风格参考图与提示词资产已经准备好。
- 第二阶段通过 `create_thread` 新开会话执行逐页生图，避免当前会话上下文过长，并强制只使用同一张 `style_reference.png` 作为视觉参考。
- 每一页都会单独调用一次生图能力，不把多页提示词合并到一次生成中。

## 安装说明

把下面的话发送给 Codex 或支持 skill 安装的 AI Agent：

```text
请用 Git clone 的方式安装这个 skill，不要用默认下载复制方式：https://github.com/Xuebin-Yang/ppt-redesign
```

推荐使用 Git clone 安装，因为这个 skill 仍在迭代。Git 安装模式下，每次运行前会检查 GitHub 上的最新版本。

## 使用方式

在 Codex 对话中上传 PDF 版 PPT，然后说明使用 `ppt-redesign` 技能进行重设计。默认完整模式会产生两次用户可见节点：

1. 第一阶段：输出风格参考图、风格参考图提示词和合批后的逐页提示词。
2. 等待用户回复：`继续`
3. 第二阶段：新会话逐页生成图片，并合成为最终 PDF。

如果只需要提示词或不需要 PDF，请在任务中明确说明“只输出提示词”或“不输出 PDF”。Codex 中仍会生成一张风格参考图，但不会逐页生图，也不会合成 PDF。

## 默认完整流程

1. 检查并更新 Git 安装版 skill。
2. 检查环境，必要时准备私有依赖。
3. 将 PDF 拆分为 `source_pages/page-###.png`。
4. 视觉识别每一页的文字和真实图片素材。
5. 生成 `deck_style_brief.md`。
6. 调用一次 `image_gen` 生成 `style_reference/style_reference.png`。
7. 完善每页提示词，并按每 8 页一组输出到 `batched_prompts/batch-XX.md`。
8. 等待用户回复 **“继续”**。
9. 通过 `create_thread` 启动第二阶段新会话。
10. 第二阶段只基于 `style_reference.png` 和每页提示词逐页生图，输出 `generated_images/page-###.png`。
11. 检查页码连续后合成为 `redesigned_deck.pdf`。

## 交付物

默认完整模式最终交付：

- `deck_style_brief.md`：品牌视觉手册参考图提示词。
- `style_reference/style_reference.png`：整套 PPT 共用的一张风格参考图。
- `batched_prompts/batch-XX.md`：每 8 页一组的最终生图提示词。
- `generated_images/page-###.png`：第二阶段逐页生成的幻灯片图片。
- `redesigned_deck.pdf`：按页码顺序合成的重设计 PDF。

只输出提示词/不输出 PDF 模式交付：

- `deck_style_brief.md`
- `style_reference/style_reference.png`（Codex 中）
- `batched_prompts/batch-XX.md`

## 关键约束

- 目前只支持 PDF 输入。
- 必须视觉识别 `source_pages/`，不能只依赖 PDF 文字层。
- 页面上的标题、副标题、正文、数字、图注等有信息价值文字必须逐一写入提示词。
- 真实图片、截图、照片、插画、产品图、人像，以及有表达意义的整页背景图，必须逐一写入「图片描述」。
- 第二阶段逐页生图时，只允许使用 `style_reference.png` 这一张参考图。
- 禁止用 PPTX、HTML、SVG、Canvas、网页截图、本地绘图或代码渲染替代生图模型补页。
- 如果无法生成或读取 `style_reference.png`，必须停止，不能跳过参考图直接逐页生图。

## English Summary

`ppt-redesign` v2.0 redesigns a PDF-exported slide deck through a two-stage Codex workflow. Stage 1 analyzes the deck, creates a single style reference image, and writes batched page prompts. The user must manually reply **"继续"** before Stage 2 starts. Stage 2 opens a new Codex thread, generates each slide image one by one using only the shared style reference image and the corresponding page prompt, then assembles the images into `redesigned_deck.pdf`.
