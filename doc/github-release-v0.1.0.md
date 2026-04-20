# v0.1.0

首个可用版本，提供面向腾讯会议录制页的逐字稿导出 skill，并同时支持 Codex 与 Claude Code。

## Highlights

- 提供 Codex 版 `meeting-transcript` skill
- 提供 Claude Code 版 `meeting-transcript` skill
- 从腾讯会议录制页抽取完整逐字稿，而不是只依赖可见 DOM
- 先保存结构化 JSON，再生成可读 TXT 会议纪要
- 对 Codex 和 Claude Code 产物追加不同尾缀，避免混淆
- 支持腾讯会议 `cw` 录制链接，Claude Code 版额外覆盖 `crm` 分享链接

## Artifacts

- `output/json/{basename}.json`
- `output/txt/{basename}.txt`

其中：

- Codex 产物使用 `_codex` 后缀
- Claude Code 产物使用 `_Claude` 后缀

## Notes

- 仓库默认忽略 `output/` 会议产物与 `.claude/settings.local.json`
- 当前版本适合“导出逐字稿 + 生成纪要 + 保留结构化数据”这类工作流
- 多视频片段不会自动合并，但每个片段都会生成标准化命名产物，便于后续按时间顺序整理
