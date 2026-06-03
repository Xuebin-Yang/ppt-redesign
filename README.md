# ppt-redesign

一个面向中文 PPT 视觉重设计的 Codex Skill：输入从 PowerPoint/PPT/PPTX 导出的 PDF，自动拆分页面、逐页视觉识别内容、生成中文视觉优化建议与逐页生图提示词，并使用 Codex 内置 `image_gen` 能力逐页生成重设计图片，最终合成为一份新的 PDF。


## 安装说明
把下面的话发送给你的 AI Agnet 即可完成安装：请用 Git clone 的方式安装这个 skill，不要用默认下载复制方式，https://github.com/Xuebin-Yang/ppt-redesign。
（因为 skill 还在迭代中，通过这个 Git clone 形式来安装后，每次运行 skill 时都会自动拉取 github 上的最新版本来运行）

## 注意事项
- 目前这个 Skill 只支持中文 PPT，不支持英文 PPT。将来会支持英文 PPT。
- 目前这个 Skill 只支持 PDF 输入，不支持其他格式输入。将来会支持其他格式输入。
- 目前只允许在 Codex 上运行，将来会支持在其他平台运行。
