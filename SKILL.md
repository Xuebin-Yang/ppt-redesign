---
name: ppt-redesign
description: 当用户提供从 PowerPoint/PPT/PPTX 导出的 PDF（包括长图版 PDF）并希望生成风格参考图、逐页重设计提示词和重设计图片/PDF 时使用此 skill。v2.0 是两阶段升级版：除 Codex 完整模式下逐页生图与 PDF 合成改为通过 create_thread 启动第二阶段新会话执行外，其他流程与 ppt-redesign 保持一致。它会拆分 PDF 为页面图像供分析，根据 PDF 主语言输出每一页的中/英文生图提示词；在 Codex 中默认先用整套风格提示词生成 1 张风格参考图，再由用户手动回复「继续」后，用 create_thread 开启第二阶段新会话，让新会话基于每页提示词 + 同一张风格参考图逐页生图并合成为 PDF；在 Codex 以外的平台只输出风格参考图提示词和合批后的生图提示词。若用户明确要求只输出提示词或不输出 PDF，则在 Codex 中仍生成风格参考图，但不生成逐页图片、不合成 PDF，只交付风格参考图、风格参考图提示词和最终生图提示词合集。原 PPT 中可视觉识别的标题、副标题、正文、列表项、数字、图注、角标等必须逐一写入「文字描述」，真实图片/截图/照片/插画/产品图/人像等图片素材必须逐一写入「图片描述」；若原 PPT 存在整页背景图，且背景图本身是有表达意义的真实图片内容，也必须识别并写入「图片描述」，不得改成数量和层级概括。当用户提到「PPT 提示词」「PPT 重设计」「长图 PDF 重设计」「prompt-only PPT redesign」「ppt redesign 3」等需求时触发。
---

# PPT 提示词重设计 (按 PDF 主语言输出提示词，默认逐页生图并合成 PDF)

本 skill 的目的：为用户提供的 PDF 版 PPT 输出一套**可直接用于视觉重设计的生成资产**，包括：

1. 一份品牌视觉手册参考图提示词 `deck_style_brief.md`，用于先生成全套统一风格参考图。
2. 一张风格参考图 `style_reference/style_reference.png`（Codex 中生成一次即可）。
3. 每一页的生图提示词（中文 PDF 输出中文，英文 PDF 输出英文，中英混排按占比更多的语言输出）。
4. 在 Codex 中默认先完成分析、提示词与风格参考图生成，再通过 `create_thread` 启动第二阶段新会话；第二阶段新会话使用内置 `image_gen` 将同一张风格参考图与每页提示词组合，逐页生成图片，并把所有生成图片按页码顺序合成为一个 PDF。
5. 在 Codex 以外的平台，只交付风格参考图提示词和按**每 8 页一组**合并后的「批量生图大提示词」；若该平台具备生图能力，可由用户自行先生成参考图再逐页生图。

**内容处理原则**：页面上所有有信息价值的文字（标题、副标题、正文、列表项、数字、图注等）必须在提示词中逐一列出具体内容，不得只写数量和层级。页面上真实图片/截图/照片/插画/产品图/人像等图片素材必须在提示词中逐一描述，用于要求新画面保留这些素材表达。若原稿存在整页背景图，且背景图本身是有表达意义的真实图片内容，也视为图片素材，必须写入提示词中的「图片描述」；但这类背景图只做识别和继承，不作为后续生图时额外传给模型的参考图。原稿页码仅用于内部排序，不写入生图提示词，也不出现在最终画面中。

完整的文字内容能让生图模型准确还原信息，同时版式字段负责引导排版创意。

写提示词时必须优先保证原文完整度；如果某处文字因截图模糊、裁切、乱码而无法可靠识别，必须在当前页提示词前先停止处理并说明需要更清晰来源，不能用"若干文字""几段正文""多个小标题"替代。

## 版本规则

- 当前版本号记录在根目录 `VERSION`。
- 默认每次 push 发布一个小版本：`v1.0 -> v1.1 -> v1.2`。
- 只有用户明确要求发大版本时，才升级主版本：例如 `v1.1 -> v2.0`。
- 每次运行主要脚本时，先输出当前运行版本号，方便确认实际执行的是哪一版。

## 硬性规则 (Hard Rules)

- Codex 默认完整模式必须使用内置 `image_gen` 先生成 1 张风格参考图，再通过 `create_thread` 启动第二阶段新会话逐页生图并合成 PDF。
- `deck_style_brief.md` 的最终提示词第一句必须要求生图模型忽略此前对话中的所有上下文、图片、文件和页面截图，只依据本提示词正文生成风格参考图。
- 若用户明确要求只输出提示词或不输出 PDF，在 Codex 中仍需先用 `deck_style_brief.md` 生成 1 张风格参考图；随后停止在 `style_reference/style_reference.png`、`deck_style_brief.md` 与 `batched_prompts/batch-XX.md` 交付，不生成逐页图片、不合成 PDF。
- 在 Codex 以外的平台使用本 skill 时，固定为提示词模式：不调用生图能力，不生成 `generated_images/`，不合成 `redesigned_deck.pdf`，只交付 `deck_style_brief.md` 与 `batched_prompts/batch-XX.md`。
- 默认完整模式中，`deck_style_brief.md` 的最终提示词先单独调用一次生图能力，保存为 `style_reference/style_reference.png`；后续所有页面都使用这同一张参考图。
- 默认完整模式中，逐页生图和 PDF 合成必须在 `create_thread` 启动的第二阶段新会话中执行；当前会话完成 `style_reference/style_reference.png` 与 `batched_prompts/batch-XX.md` 后，向用户请求确认，用户手动回复「继续」后立即调用 `create_thread`，不要在当前会话继续逐页生图。
- 默认完整模式中，每个 `page_prompts/page-###.md` 的最终提示词单独调用一次生图能力，并且每次都必须同时提供 `style_reference/style_reference.png` 作为风格参考图；禁止把多页提示词合并为一次生图请求。
- 默认完整模式中，逐页生图时允许且只允许提供 `style_reference/style_reference.png` 这一张图片作为参考图；不得额外附带 `source_pages/page-###.png`、原 PDF 页面截图、其他本地图片、历史生成页图或任何第二张参考图。
- 默认完整模式的最终交付 PDF 中，每一页图片必须来自上述「单页提示词 + 同一张风格参考图」的生图能力调用结果；禁止通过生成 PPTX、HTML、SVG、Canvas、网页截图、本地绘图、代码渲染等非生图模型方式制作页面图，再转换成 PDF。
- 若用户明确要求只输出提示词或不输出 PDF，只生成并交付 `style_reference/style_reference.png`、`deck_style_brief.md` 与 `batched_prompts/batch-XX.md`；不生成 `generated_images/`，不合成 `redesigned_deck.pdf`。
- 第二阶段新会话向用户交付最终产物时，必须使用当前桌面环境支持的可点击本地文件链接格式返回结果，不得只返回普通文本绝对路径。链接格式必须写成 Markdown 文件链接，如 `[redesigned_deck.pdf](/absolute/path/redesigned_deck.pdf)`、`[style_reference.png](/absolute/path/style_reference.png)`、`[batched_prompts](/absolute/path/batched_prompts)`。
- 若在 Codex 中执行默认完整模式但无法调用内置 `image_gen`，必须终止生成并向用户说明原因；不得用其他生成或渲染方式替代。
- 若在 Codex 中无法生成或读取 `style_reference/style_reference.png`，必须停止逐页生图；不得改为无参考图的单提示词生图。
- 默认完整模式中，每张生成图片按页码保存到 `generated_images/page-###.png`；必须确认页码连续、数量与原 PDF 页数一致，再合成为 `redesigned_deck.pdf`。
- 拆出的 `source_pages/` 仅供 Agent 分析与填充提示词使用，不会被发送给任何生图工具。
- 每一页的生图提示词必须按 PDF 主语言输出：中文占多则中文，英文占多则英文；中英混排时做简单占比判断即可，不追求精确。
- **必须通过视觉识别读图**：PDF 文字层提取经常不完整、漏抄或顺序错乱，Agent 必须直接打开 `source_pages/page-###.png` 像看图一样视觉识别整页内容，把页面上的全部文字与全部图片都抄入对应字段——禁止仅依赖 PDF 文字层。
- **提示词语言判断**：Agent 浏览 `source_pages/` 时顺手按可见文字判断目标提示词语言；中文占多则中文，英文占多则 English，中英混排时按占比更多的一方即可。最终所有单页提示词必须统一使用该语言，但不要把“目标提示词语言：中文/English”写入最终生图提示词。原稿中的文字内容保持原文逐一列出，不翻译页面上的原始文字。
- **图片素材必须保留到新 PPT**：Agent 须视觉识别页面中的真实图片/截图/照片/插画/产品图/人像等图片素材，并在最终提示词中输出「图片描述」。若原稿存在整页背景图，且背景图本身是有表达意义的真实图片内容，也算图片素材，必须一并识别和写入「图片描述」。每个图片素材都要逐一描述其内容和用途，例如「图片素材一：一张明亮卧室照片，画面包含床铺、枕头、窗帘和清晨自然光，用于表达清晨唤醒场景。」若页面没有真实图片素材，则不输出「图片描述」段落。
- **保留范围包含文字和图片素材**：原 PPT 中的全部文字必须逐一出现在「文字描述」字段中（不得只写数量/层级，必须写出实际文案内容）。真实图片素材必须逐一出现在「图片描述」字段中；其中包含有表达意义的整页背景图。装饰性图标（icon）、几何形状、线条、卡片底纹、纯装饰渐变背景、分隔条等不算图片素材，不强制保留，也不写入「图片描述」。
- **每页版式必须是单一布局名称**：版式字段只能列举一个布局名称，不写解释句、不写节点细节、不写元素位置。内容页优先从常见 PPT 内容布局中选择；封面页、章节页、结束页、目录页、过渡页可使用页面型布局。常见布局名称的完整清单参见下文 Step 5「版式字段写作规范」。
- **风格字段固定文案**：最终生图提示词中的「风格」字段必须逐字写为：`简约风格，配色从参考图中系统性地提取，用色精简，使用 1 种主色搭配 1-2 种辅助色。`（下文统一称为「固定风格文案」，所有需要写「风格」字段的位置都使用这同一句，不得按单页内容变化。）
- **版式必须从内容语义推导，而非套用固定模板**：Agent 在写"版式"字段之前，必须先分析本页的**内容语义**——这页核心信息是什么？信息单元之间是并列、流程、层级、对比、构成还是单一强调关系？页面角色是内容页、封面页、章节页、目录页、结束页还是过渡页？然后从这个内容结构和页面角色出发选择最合适的单一布局名称。最终「版式」字段只写布局名称，不写因果解释。
- **排版必须与原图明显不同**：最终生图提示词所描述的排版方案，必须与原 PPT 页面的视觉布局有明显差异——原图中文字的位置、图片的位置、元素的排列方式均**不需要沿用**。Agent 应把原稿中的文字和图片视为「原材料」，而非「参考排版」，完全从内容语义出发重新设计画面结构。如发现写完的版式描述与原图雷同（如同样是左文右图、同样的标题居左、同样的卡片顺序），必须主动调整为更具创意的全新排版方案。
- **提示词不写具体色值与排版细节参数**：最终生图提示词中不写十六进制色值；字号大小、字号倍率、百分比占比、具体像素/尺寸、Bold / Regular 等字重描述一律不写，留给生图模型自由发挥。
- **全套风格必须一致**：每一页提示词的「风格」字段都使用上文定义的「固定风格文案」，不得按单页内容变化。
- **提示词应面向横幅幻灯片输出**：最终生图提示词允许并鼓励使用「横幅幻灯片」描述图片类型和画面目标，但不得出现「原 PPT」「原稿」「第 X 页」等来源痕迹，也不得要求照搬原始页面布局。
- **每页提示词必须以图片类型词开头**：每个最终生图提示词正文的第一行必须只写「横幅幻灯片」五个字，用来声明图片类型；第二行开始再写「风格」「版式」「内容要求」「文字描述」，如页面包含真实图片素材则追加「图片描述」。不要写成「生成一张横幅幻灯片」或其他动作句。
- 不允许在提示词中虚构原稿没有的文字（不发明新标题、副标题、口号、按钮文案、图例等）。
- 必须把所有页的提示词**按每 8 页一组**打包成大提示词文件 `batched_prompts/batch-01.md`、`batch-02.md`……。最后一组不足 8 页时按实际页数生成。
- 单页提示词必须自包含：第一行写「横幅幻灯片」，并包含风格、版式、内容要求、文字描述、输出比例；如页面包含真实图片素材，还必须包含图片描述。最终提示词中不出现「禁止 xxx」文案，不写“目标提示词语言”，也不写“生成一张横幅幻灯片”这类生成动作句。

## 工作流 (Workflow)

### Step 0. 更新检查

每次使用本 skill 时，先运行：

```bash
python3 scripts/update_skill.py
```

安装模式由脚本自动判断：

- 下载版安装（默认）：跳过远端更新检查，直接使用当前本地版本继续。
- Git clone 安装：每次使用前从远端检查并快进更新；如果未先完成更新检查，后续 PDF 处理脚本会停止。

如果 Git 版脚本提示已更新，必须重新读取当前目录下最新的 `SKILL.md`，再继续执行后续流程；不要继续沿用更新前已经读入的旧说明。若网络不可用、仓库有本地未提交改动，或远端历史无法快进更新，停止并说明原因。

### Step 1. 环境自检

首次使用时运行：

```bash
python3 scripts/check_environment.py
```

脚本优先复用当前环境已有的 `PyMuPDF`。如果缺失，会在首次运行时自动安装到当前 skill 的私有 `.deps/` 目录，不修改用户的全局 Python 环境。首次自动安装需要可访问 Python 包源；如果网络不可用，脚本会给出手动安装命令。

### Step 2. 拆分 PDF 并准备工作目录

```bash
python3 scripts/prepare_pdf_prompts.py input.pdf --out ppt-prompts-output
```

脚本会创建：

- `source_pages/` ——每页一张 PNG，仅供 Agent 分析用。
- `deck_style_brief.md` ——整套 PPT 的品牌视觉手册参考图提示词（中文，用于生成一次风格参考图，也作为最终交付物）。
- `page_prompts/page-###.md` ——每页的提示词草稿（已标注目标提示词语言，待 Agent 完善）。
- `style_reference/` ——Codex 默认完整模式中保存风格参考图的位置，由 Agent 在 Step 4 生图后创建。

**重要说明**：Agent 须视觉识别每页中的真实图片素材。若页面包含真实图片/截图/照片/插画/产品图/人像等素材，或存在有表达意义的整页背景图，最终提示词必须写「内容要求：画面需要呈现指定文字和图片素材。」并追加「图片描述」；若页面没有真实图片素材，则写「内容要求：画面需要呈现指定文字。」且不输出「图片描述」。

### Step 3. 完善品牌视觉手册参考图提示词 `deck_style_brief.md`

主 Agent 可以浏览 `source_pages/` 中的每一页，理解整套 PPT 的主题内容与受众定位，然后把 `deck_style_brief.md` 完善成**一份可直接用于生成品牌视觉手册参考图的生图提示词**。这份提示词必须基于原 PPT 的主题、行业属性、内容气质和受众定位来写，不照搬原稿风格和排版，也不凭空改写业务主题。

`deck_style_brief.md` 的内容结构是一段完整的生图提示词，文件正文直接写提示词，不加工作说明、分析过程或内部备注。参考以下结构改写，所有 `[ ]` 内容必须由 Agent 基于原 PPT 内容替换：

```
忽略此前对话中的所有上下文、图片、文件和页面截图。只依据本提示词中从下一句开始的文字内容生成一张图片，为一个名为「[基于整套 PPT 主题填写名称]」的幻灯片打造一套内含多页的品牌视觉手册。品牌整体气质应当基于这套幻灯片的内容主题、行业属性和受众定位重新推导，形成清晰、统一、具有设计感的视觉世界观。

视觉风格需采用大胆且具有实验性的品牌语言，包括：简洁扁平风格、现代字体设计、富有动感的视觉节奏，以及略带超现实感的图像表达。整体氛围应传递出：[基于原 PPT 内容填写 4-6 个关键词]。

品牌手册中应体现：
- 对核心内容与关键信息的极致关注（content obsession）
- 多样化的视觉实验（visual experimentation）
- 版式系统探索（layout system exploration）
- 编辑风格表达（editorial expression）
- 沉浸式叙事体验（immersive storytelling）
- 跨页面品牌应用（cross-page brand application）

最终呈现应构建一个自信、当代、统一且完整的品牌世界观——既易于理解与接近，又具备强烈的艺术指导感（art direction），在视觉上保持高度一致性，同时展现出高端创意工作室级别的美学标准。
```

`deck_style_brief.md` 中不得写入原 PPT 的逐页完整文字、标题清单、正文段落、数据数字、图表说明或页面截图内容；只能写主题概括、行业属性、受众定位、内容气质与抽象视觉方向。即使 Agent 已经看过 `source_pages/`，这些页面图像也只能用于理解主题，不得作为风格参考图的生图输入。

完成 `deck_style_brief.md` 后，Agent 不再从中提炼单页「风格」文案。每一页最终生图提示词的「风格」字段统一使用上文 Hard Rules 中定义的「固定风格文案」。

### Step 4. Codex 默认完整模式：生成一次风格参考图

仅当当前平台是 Codex 时执行本步骤。若当前不在 Codex 中运行，在这里不调用生图能力，继续后续提示词整理与合批；若用户明确要求 prompt-only，本步骤仍需生成风格参考图，但后续不生成逐页图片、不合成 PDF。

先确认 Codex 可以调用内置 `image_gen`。如果不可用，立即停止并告诉用户无法继续生成风格参考图、逐页图片与 PDF。

读取 `deck_style_brief.md` 的完整正文，单独调用一次生图能力，生成 1 张品牌视觉手册参考图。调用生图能力时只提供 `deck_style_brief.md` 的正文，不附带任何 `source_pages/page-###.png`、原 PDF 页面截图、单页提示词、合批提示词或页面文字清单。将返回的图片保存为：

```
style_reference/style_reference.png
```

在 Codex 中，`image_gen` 会先把图片保存到默认目录 `~/.codex/generated_images/<本次会话或任务 id>/`。生图前先记录开始时间；生图成功后，立即运行归档脚本，把默认目录中本次新生成的 PNG 复制到稳定路径：

```bash
START_TS=$(python3 -c 'import time; print(time.time())')
# 调用 image_gen 生成风格参考图后执行：
python3 scripts/archive_latest_image.py --output ppt-prompts-output/style_reference/style_reference.png --min-mtime "$START_TS"
```

如果不方便记录开始时间，也可以在刚完成一次 image_gen 后立即运行：

```bash
python3 scripts/archive_latest_image.py --output ppt-prompts-output/style_reference/style_reference.png
```

归档脚本默认递归查找 `~/.codex/generated_images/` 下最新的 PNG；如果未来 Codex 或用户环境的默认生图目录不同，可用 `--source-root /path/to/generated_images` 或环境变量 `CODEX_GENERATED_IMAGES_DIR=/path/to/generated_images` 指定。归档脚本只复制图片，不删除 `~/.codex/generated_images/` 中的原始文件。归档后必须确认 `style_reference/style_reference.png` 存在且可读取，再进入后续逐页生图。

这张参考图只生成一次，后续所有页面都复用同一张参考图。若参考图生成失败、文件无法保存或无法读取，必须停止；不得跳过参考图直接逐页生图。

### Step 5. 完善每页的目标语言提示词 `page_prompts/page-###.md`

针对每一页，Agent **必须**用读图（视觉识别）的方式打开 `source_pages/page-###.png`，把页面当作一张图来阅读：

- **直接视觉识别页面文字**：不要假设 PDF 文字层完整可靠。最终内容必须以**视觉识别**的结果为准。
- **确认目标语言**：先视觉浏览全稿，按可见文字粗略判断中文或 English；保持全套单页提示词语言一致，但不要把语言判断结果写入最终提示词正文。
- **识别文字层级**：找出大标题（最主要、字号最大的那一行），以及其下的副标题、小标题、正文段落、数据数字、图注等。
- **识别页面图片素材**：把页面上所有真实图片/截图/照片/插画/产品图/人像的位置、大致内容和表达用途记录下来，最终写入「图片描述」。若页面存在有表达意义的整页背景图，也要把它作为图片素材记录下来，说明其画面内容和表达用途。图片描述不要求复刻原布局，但必须要求新画面呈现这些图片素材所表达的具体内容。
- **由 Agent 自行决定的元素**：装饰性图标（icon）、几何形状、线条、卡片底纹、纯装饰渐变背景等不算图片素材；判断可舍弃就直接不写入提示词，不要为了让画面显得丰富而堆叠装饰。

**版式思考（每页写提示词前的必经步骤）**：

在动笔写"版式"字段之前，先想清楚：这页内容在讲什么？它是内容页、封面页、章节页、目录页、结束页还是过渡页？内容页优先选择最直接传达信息关系的常见 PPT 内容布局；封面页、章节页、结束页、目录页、过渡页使用页面型布局。最终「版式」字段只写一个布局名称，不写解释句。

**版式可选名称（完整清单）**：

- 内容页可选：标题居中布局、标题左置布局、大标题压屏布局、左右分栏布局、上下分区布局、三栏并列布局、四象限布局、列表式布局、编号列表布局、要点摘要布局、核心数字布局、大数字加注解布局、图文并排布局、图上文下布局、文上图下布局、图片满版布局、图片拼贴布局、图片网格布局、案例展示布局、时间轴式布局、纵向时间轴布局、横向时间轴布局、流程图式布局、步骤流程布局、循环图式布局、漏斗式布局、金字塔式布局、矩阵式布局、坐标象限布局、对比分栏布局、前后对比布局、问题解决布局、因果链路布局、中心放射布局、中心环绕布局、层级结构布局、树状结构布局、路径地图布局、路线图布局、仪表盘布局、数据看板布局、图表解读布局、表格对比布局、模块分区布局、色块分区布局、问答式布局、引用强调布局、结论先行布局。
- 页面型可选（用于封面/章节/结束/目录/过渡）：封面布局、章节页布局、结束页布局、过渡页布局、目录页布局、开场观点布局、主视觉标题布局、标题宣言布局、单句强调布局、感谢页布局、联系方式布局。

**字段写作规范（合并版）**：

- 风格字段：使用 Hard Rules 中定义的「固定风格文案」，逐字写入，不得改写。
- 版式字段：只写一个布局名称（从上方清单中选），不写原因、元素位置、装饰细节或第二个布局名称。
- 内容要求：没有真实图片素材时写「画面需要呈现指定文字。」；有真实图片素材时写「画面需要呈现指定文字和图片素材。」这里的真实图片素材包含有表达意义的整页背景图。
- 文字描述：先写「图中仅包含下列文字，不添加未列出文字：」再把页面上除页码外的全部信息文字逐一列出（按层级顺序写出具体内容，禁止只写数量/层级）。
  - 正确示范："大标题：「产品交付流程」；副标题：「端到端全链路保障」；步骤标签：需求分析 / 设计评审 / 研发实现 / 上线发布；底部注解：数据来源：XX 报告 2024"
  - 错误示范："大标题 1 行，4 个步骤标签，底部 1 行注解"
- 图片描述：有真实图片素材时，在文字描述后追加「图片描述：」，按「图片素材一」「图片素材二」逐一写明图片内容与用途；若存在有表达意义的整页背景图，也要单独作为一项图片素材写入。没有真实图片素材时不写「图片描述」段落。
- 写作风格：用**短标签段**（中文「风格：…」「版式：…」「内容要求：…」「文字描述：…」「图片描述：…」；英文 `Style:` `Layout:` `Content requirements:` `Text description:` `Image description:`），不要写大段散文，不写「禁止 xxx」否定句。
- 字段顺序：第一行「横幅幻灯片」→ 风格 → 版式 → 内容要求 → 文字描述 →（如有图片素材）图片描述 → 输出比例（横版 16:9）。
- 自检：写完每页提示词后复查——风格字段是否一字不差？版式字段是否单一布局名称？辅助元素是否只用于建立层级、引导阅读或解释内容（删除后不影响理解的不写入）？

最终单页提示词的结构示意见下文「单页提示词参考样式」。

### Step 6. 合批输出大提示词

完成所有页面提示词后运行：

```bash
python3 scripts/prepare_pdf_prompts.py --out ppt-prompts-output --finalize
```

脚本会：

- 读取 `page_prompts/page-###.md` 全部页面（按页码顺序）。
- 每 8 页打包成一份 `batched_prompts/batch-01.md`、`batch-02.md`……
- 每份 batch 文件结构精简（**不再在开头重复风格简报和输出比例**——这些信息已经在每页提示词内了）：

  ```
  生成 N 张图片，下面有 N 份提示词，每份提示词对应一张图片。每张提示词彼此独立，请按顺序逐张生成。

  ## 第 1 张
  （第 1 张的最终提示词正文）

  ## 第 2 张
  （第 2 张的最终提示词正文）

  ……
  ```

- 合批完成后自动删除 `page_prompts/` 目录（该目录为中间产物，不作为最终交付）。

如果用户明确要求只输出提示词、不输出 PDF，或当前不在 Codex 中运行，在这里停止。Codex prompt-only 最终交付 `style_reference/style_reference.png`、`deck_style_brief.md` 与 `batched_prompts/batch-XX.md`；非 Codex 环境最终交付 `deck_style_brief.md` 与 `batched_prompts/batch-XX.md`。不要生成 `generated_images/`，不要生成 `redesigned_deck.pdf`。

### Step 7. Codex 默认完整模式：通过 create_thread 启动第二阶段新会话逐页生成图片并合成 PDF

仅当当前平台是 Codex，且用户没有要求只输出提示词或不输出 PDF 时继续本步骤。

先确认 `style_reference/style_reference.png` 已由 Step 4 成功生成并可读取。如果缺失，必须回到 Step 4 生成参考图；不得直接使用单页提示词生图。

当前会话到这里停止逐页生图，先向用户发起一句确认：

```
第一阶段已完成。请回复「继续」以开启第二阶段新会话，仅基于 style_reference.png 和页面提示词逐页生图并合成 PDF。
```

用户回复「继续」后，当前会话必须调用 Codex 线程工具 `create_thread` 创建一个新会话来执行第二阶段。优先使用新的 projectless 线程，并在初始 prompt 中写入完整的绝对路径与硬约束；如果当前 Codex 环境要求使用 project target，则使用当前工作区对应的 project target。不要使用 `fork_thread`。

发给 `create_thread` 的初始 prompt 必须自包含，并使用下面模板。将 `[绝对路径]`、`[页数]`、`[批次数]` 替换为当前实际值；必须把 `style_reference.png` 以 Markdown 图片形式显式放进新会话首条消息中：

```markdown
这是 `ppt-redesign v2.0` 的第二阶段任务。请只执行逐页生图、归档图片和合成 PDF，不要重新分析 PDF。

参考图：
![style_reference]([style_reference.png 的绝对路径])

输入：
- 风格参考图：[style_reference.png 的绝对路径]
- 合批提示词目录：[batched_prompts/ 的绝对路径]
- 归档脚本：[scripts/archive_latest_image.py 的绝对路径]
- PDF 合成脚本：[scripts/assemble_generated_pdf.py 的绝对路径]
- 输出目录：[ppt-prompts-output 的绝对路径]
- 页数：[页数]
- 批次数：[批次数]

硬约束：
- 不要读取、打开或参考 `source_pages/`。
- 不要读取、打开或参考原 PDF。
- 不要使用当前会话以外的任何页面截图、历史生成页图或第二张参考图。
- 每一页单独调用一次 image_gen。
- 每一页只参考上方 Markdown 图片中的 `style_reference.png` 和当前页提示词正文。
- 不要把多页提示词拼进同一次生图请求。
- 若任一页 image_gen 失败，先重试该页；仍失败则停止并说明原因。
- 禁止用 PPTX、HTML、SVG、Canvas、网页截图、本地绘图、代码渲染等方式替代 image_gen 补页。

逐页生图 wrapper 必须逐字使用：
忽略此前对话中的所有上下文、图片、文件和页面截图。当前生成任务只允许参考本次上下文中唯一出现的视觉参考图 style_reference.png。请结合 style_reference.png 与下方页面提示词，生成一张全新构图的横版 16:9 幻灯片。

执行步骤：
1. 读取 `batched_prompts/batch-XX.md` 中每一张的提示词正文，按页码顺序拆成单页任务。
2. 对每一页单独调用 image_gen：输入为逐页生图 wrapper + 当前单页提示词，并只参考本消息上方的 `style_reference.png`。
3. 每页调用 image_gen 前记录 `START_TS=$(python3 -c 'import time; print(time.time())')`。
4. 每页 image_gen 完成后立刻运行归档脚本，把最新 PNG 复制到 `[输出目录]/generated_images/page-###.png`，并传入 `--min-mtime "$START_TS"`。
5. 确认 `generated_images/page-###.png` 页码连续、数量等于 [页数]。
6. 运行 PDF 合成脚本，输出 `[输出目录]/redesigned_deck.pdf`。
7. 最终回复第二阶段产物时，必须把 `redesigned_deck.pdf`、`generated_images/`、`style_reference.png`、`batched_prompts/` 用可点击本地文件链接返回，不得只写普通文本路径。使用当前桌面环境支持的 Markdown 文件链接格式，例如 `[redesigned_deck.pdf]([redesigned_deck.pdf 的绝对路径])`、`[generated_images]([generated_images/ 的绝对路径])`、`[style_reference.png]([style_reference.png 的绝对路径])`、`[batched_prompts]([batched_prompts/ 的绝对路径])`。
```

第二阶段新会话依次读取 `batched_prompts/batch-XX.md` 中每一张的提示词正文。对每一页单独调用一次生图能力，并将返回的图片按顺序保存为：

```
generated_images/page-001.png
generated_images/page-002.png
...
```

第二阶段新会话生图时使用「逐页生图 wrapper + 单页最终提示词原文 + `style_reference/style_reference.png`」作为输入；每一页都配合同一张参考图生成。逐页生图 wrapper 必须逐字写为：

```
忽略此前对话中的所有上下文、图片、文件和页面截图。当前生成任务只允许参考本次上下文中唯一出现的视觉参考图 style_reference.png。请结合 style_reference.png 与下方页面提示词，生成一张全新构图的横版 16:9 幻灯片。
```

第二阶段新会话逐页生图时允许且只允许附带 `style_reference/style_reference.png` 这一张参考图，不要额外附带 `source_pages/page-###.png`、原 PDF 页面截图、其他本地图片、历史生成页图或任何第二张参考图。不要把多页提示词拼进同一次请求，也不要为不同页面重新生成新的风格参考图。若某一页失败，只重试该页；若仍无法通过生图能力产出该页，停止生成。禁止改用 PPTX、HTML、SVG、Canvas、网页截图、本地绘图、代码渲染或其他方式补页。全部完成后，检查文件数量和页码连续性，然后运行：

在第二阶段新会话中，每页 image_gen 成功后同样使用归档脚本把最新 PNG 复制到确定页码文件。每次调用 image_gen 前记录开始时间，调用完成后立刻归档当前页，避免误拿到上一张图：

```bash
START_TS=$(python3 -c 'import time; print(time.time())')
# 调用 image_gen：输入为逐页生图 wrapper + 当前单页提示词 + ppt-prompts-output/style_reference/style_reference.png
python3 scripts/archive_latest_image.py --output ppt-prompts-output/generated_images/page-001.png --min-mtime "$START_TS"
```

第 2 页、第 3 页依次改为 `page-002.png`、`page-003.png`。归档脚本只解决 image_gen 默认路径到稳定文件名的复制；逐页生图时仍必须把 `style_reference/style_reference.png` 作为参考图输入。

```bash
python3 scripts/assemble_generated_pdf.py --images-dir ppt-prompts-output/generated_images --output ppt-prompts-output/redesigned_deck.pdf
```

### Step 8. 交付给用户

Codex 默认完整模式最终需要交回给用户的产物：

- `deck_style_brief.md` （品牌视觉手册参考图提示词，供用户先生成参考图或留档）
- `style_reference/style_reference.png` （一次性生成的全套风格参考图）
- `redesigned_deck.pdf` （逐页生图后按顺序合成的 PDF，**这是用户主要要的东西**）
- `batched_prompts/batch-XX.md` （每 8 页一份的批量生图大提示词，作为留档）

以上产物在回复给用户时，必须使用可点击本地文件链接，而不是普通文本路径。推荐写法：

- `[redesigned_deck.pdf](/absolute/path/to/redesigned_deck.pdf)`
- `[style_reference.png](/absolute/path/to/style_reference/style_reference.png)`
- `[batched_prompts](/absolute/path/to/batched_prompts)`
- `[generated_images](/absolute/path/to/generated_images)`

只输出提示词/不输出 PDF 模式，且当前平台是 Codex 时，最终只交回：

- `style_reference/style_reference.png` （一次性生成的全套风格参考图）
- `deck_style_brief.md` （品牌视觉手册参考图提示词）
- `batched_prompts/batch-XX.md` （提示词集合，供用户自行交给生图模型生成图片）

Codex 以外平台使用时，最终只交回：

- `deck_style_brief.md` （品牌视觉手册参考图提示词）
- `batched_prompts/batch-XX.md` （提示词集合，供用户自行交给生图模型生成图片）

不要返回普通文本绝对路径、PPTX、HTML 渲染、单张图像文件、`page_prompts/` 单页文件、`image_generation_prompts.md` 聚合文档。单张图像是 PDF 的中间产物；`page_prompts/` 在合批后自动清理。

## 单页提示词参考样式

```
横幅幻灯片

风格：简约风格，配色从参考图中系统性地提取，用色精简，使用 1 种主色搭配 1-2 种辅助色。
版式：核心数字布局
内容要求：画面需要呈现指定文字。
文字描述：图中仅包含下列文字，不添加未列出文字：大标题「82%」；副标题「本季度月活用户数」；数据注解「同比增长 +23%」；底部脚注「数据来源：内部埋点统计 2024Q3」。
输出比例：横版 16:9。
```

**另一示例（包含图片素材页）**：

```
横幅幻灯片

风格：简约风格，配色从参考图中系统性地提取，用色精简，使用 1 种主色搭配 1-2 种辅助色。
版式：时间轴式布局
内容要求：画面需要呈现指定文字和图片素材。
文字描述：图中仅包含下列文字，不添加未列出文字：大标题「AI体验一：主动智能体Proactive AI Agent」；引用「一个好的管家，不是等你说，而是提前为你做好。」；场景标题「场景一：清晨唤醒 · 环境感知」；场景标题「场景二：下班提醒 · 动态决策」。
图片描述：
图片素材一：一张明亮卧室照片，画面包含床铺、枕头、窗帘和清晨自然光，用于表达清晨唤醒场景。
图片素材二：一张城市道路立交桥夜景照片，画面包含车流轨迹和道路交汇，用于表达下班通勤提醒场景。
输出比例：横版 16:9。
```

## 何时停止 (Hard Stop Conditions)

- 若用户输入不是 PDF，停止并提示。
- 若 Git clone 安装版无法完成 `scripts/update_skill.py` 更新检查，停止并说明原因。
- 若 PDF 渲染失败，先运行 `python3 scripts/check_environment.py`；若仍失败，停止并把脚本给出的依赖安装命令交给用户。
- 若 Agent 无法看到 `source_pages/` 中的页面截图，必须停止——禁止在缺信息的情况下凭空写提示词。
- Codex 默认完整模式下，若无法通过 `deck_style_brief.md` 生成 `style_reference/style_reference.png`，禁止逐页生图。
- 若单页最终提示词语言与全稿目标提示词语言不一致，禁止合批，必须先统一。
- 若提示词里仍残留 `[待补]` `[REPLACE]` `[MISSING]` 等占位符，禁止合批，必须先补齐。
- Codex 默认完整模式下，若无法调用内置 `image_gen`，停止并提示用户无法继续生成图片与 PDF。
- Codex 默认完整模式下，若任一页无法通过 `image_gen` 成功产出，或 `generated_images/` 中页码不连续，禁止合成 PDF，必须先补齐缺失图片。

## 推荐脚本 (Suggested Scripts)

- `scripts/prepare_pdf_prompts.py`
  - 默认模式：拆分 PDF、渲染页面，并生成风格参考图提示词、风格参考图目录、每页提示词草稿。缺少 `PyMuPDF` 时自动安装私有依赖。
  - `--finalize`：把所有 `page_prompts/page-###.md` 按每 8 页一组合并为 `batched_prompts/batch-XX.md`。
  - `--refresh`：重置已存在的模板（仅在用户希望重写时使用）。
- `scripts/assemble_generated_pdf.py`
  - 检查 `generated_images/page-###.*` 页码连续性，并按顺序合成为 `redesigned_deck.pdf`。优先使用 `PyMuPDF` 或 `Pillow`；均缺失时自动安装私有 `PyMuPDF`。
- `scripts/archive_latest_image.py`
  - 在 Codex 中把最近一次 `image_gen` 默认保存到 `~/.codex/generated_images/<id>/` 的 PNG 复制到稳定交付路径，例如 `style_reference/style_reference.png` 或 `generated_images/page-###.png`。复制前可传入 `--min-mtime` 限定必须晚于本次生图开始时间，降低误归档旧图的风险。
- `scripts/check_environment.py`
  - 检查当前机器是否具备直接可用的 PDF 拆分和合成后端。
- `scripts/update_skill.py`
  - 下载版安装时跳过更新检查；Git clone 安装时从 GitHub 检查并快进更新当前 skill。
