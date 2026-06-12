# ppt-redesign

一个面向 PPT 视觉重设计的 AI Agent Skill：输入从 PowerPoint/PPT/PPTX 导出的 PDF，自动拆分页面、逐页视觉识别内容、生成中文视觉优化建议与逐页生图提示词，并默认使用当前 AI Agent 自带的生图能力逐页生成重设计图片，最终合成为一份新的 PDF。中文 PDF 输出中文提示词，英文 PDF 输出英文提示词，中英混排时按占比更多的语言输出；如果用户只需要提示词，也可以只交付合批后的提示词集合。

An AI Agent skill for PPT visual redesign. It takes a PDF exported from PowerPoint/PPT/PPTX, splits it into pages, visually reads each page, generates deck-level visual suggestions and page-level image prompts, and by default uses the current AI Agent's built-in image generation capability to create redesigned images page by page before assembling them into a new PDF. Chinese PDFs produce Chinese prompts, English PDFs produce English prompts, and mixed-language PDFs use whichever language is more dominant. If the user only wants prompts, the skill can also return only the final batched prompt set.

## 安装说明
把下面的话发送给你的 AI Agent 即可完成安装：请用 Git clone 的方式安装这个 skill，不要用默认下载复制方式，https://github.com/Xuebin-Yang/ppt-redesign
> 因为 skill 还在迭代中，通过这个 Git clone 形式来安装后，每次运行 skill 时都会自动拉取 github 上的最新版本来运行。）

## Installation
Send this message to your AI Agent to install the skill: "Please install this skill with Git clone instead of the default download-copy mode: https://github.com/Xuebin-Yang/ppt-redesign"
> The skill is still evolving, so Git clone installation is recommended. In Git mode, the skill checks GitHub for the latest version before each run.

## 使用方式
在 AI Agent 对话中上传 PDF 版的 PPT，然后使用这个 skill。若在 Codex 中使用，生图能力对应内置 `image_gen`；其他 AI Agent 使用时，请替换为该 Agent 自带的生图能力。

## Usage
Upload the PDF version of your PPT in an AI Agent conversation and invoke this skill. In Codex, the image generation capability maps to the built-in `image_gen` tool; in other AI Agents, replace it with the agent's own image generation capability.


## 注意事项
- Skill 运行耗费的额度较大，如果只是简单初步测试，可以用只有几页的 PPT 来测试。
- 支持中文、英文和中英混排 PDF；中英混排时会做简单语言占比判断。
- 目前这个 Skill 只支持 PDF 输入，不支持其他格式输入。将来会支持其他格式输入。
- 默认完整模式需要当前 AI Agent 具备生图能力；只输出提示词模式不需要生图能力。

## Notes
- Running the skill can consume a noticeable amount of Codex usage, so for quick testing it is better to start with a small PPT that has only a few pages.
- The skill supports Chinese, English, and mixed Chinese-English PDFs. For mixed decks, it uses a simple dominant-language judgment.
- The skill currently supports PDF input only. Other input formats may be supported later.
- The default full workflow requires the current AI Agent to have image generation capability. Prompt-only mode does not require image generation.
