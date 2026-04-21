---
name: meeting-transcript
description: 从腾讯会议录制页面提取完整逐字稿并生成格式化会议纪要 TXT 文件。Use when the user provides a Tencent Meeting recording URL such as meeting.tencent.com/cw/... and asks to导出逐字稿、生成会议纪要、保存会议记录、提取录制页文本，或把录制内容落盘到当前项目。Do not use for other meeting platforms or when the user already pasted the transcript text.
---

# 腾讯会议逐字稿导出

处理腾讯会议录制链接 `https://meeting.tencent.com/cw/...`，从录制页提取完整逐字稿数据，先保存原始结构化 JSON，再在当前仓库的 `output/` 目录生成可交付的会议纪要 TXT。

## Workflow

1. 确认用户给的是腾讯会议录制页 URL，而不是普通会议链接或已经导出的文本。
2. 用 `mcp__chrome_devtools__navigate_page` 打开录制页；如果页面要求登录、授权或验证码，暂停并让用户先完成页面交互。
3. 等页面稳定后用 `mcp__chrome_devtools__take_snapshot` 获取结构；如果当前不是“逐字稿”标签页，点击文本为“逐字稿”的元素切换过去。
4. 先读取 [scripts/extract_transcript.js](scripts/extract_transcript.js)，把文件内容原样作为 `mcp__chrome_devtools__evaluate_script` 的 `function` 参数执行，用来验证抽取是否成功、总条数是否合理。
5. 检查返回值：
   - 如果包含 `error`，直接向用户报告并停止。
   - 如果 `items` 为空，先确认是否真的切到了“逐字稿”视图，再重试一次。
   - 如果 `pageMeta` 缺字段，优先依赖脚本里的 DOM 文本回退；仍缺失时，再根据最新 snapshot 或 `document.body.innerText` 补齐后继续。
6. 再读取 [scripts/extract_transcript_to_clipboard.js](scripts/extract_transcript_to_clipboard.js)，通过 `mcp__chrome_devtools__evaluate_script` 执行，把浏览器真实抽取到的原始 JSON 写进系统剪贴板。执行成功后返回值里应包含 `copied: true`。
7. 先把剪贴板里的原始 JSON 落盘，不要先转 TXT，更不要从 TXT 反推 JSON。优先使用脚本直接读取系统剪贴板，避免 PowerShell 管道传输中文时发生编码损坏。运行：

```powershell
python .agents/skills/meeting-transcript/scripts/save_transcript_json.py --from-clipboard --output-root-dir output
```

8. 读取 `save_transcript_json.py` 的输出，优先使用 `JSON_PATH=...` 或 `BASENAME=...` 继续生成 TXT。运行：

```powershell
python .agents/skills/meeting-transcript/scripts/format_minutes.py "output/json/{basename}.json" --output-root-dir output
```

9. 文件命名统一使用 `会议时间 + 会议号 + 发言人统计 + _codex` 组成 basename，例如：

```text
2026_04_16 21_36_451 606 790_朱达Tracy54、DavidHu42、Alg高7_codex
```

10. JSON 输出到 `output/json/{basename}.json`；确认 JSON 已保存后，再基于这个 JSON 生成 `output/txt/{basename}.txt`。
11. 读取生成的 TXT 文件，向用户报告文件路径、会议时间、会议号、总发言数和发言人统计。
12. 除非用户要求清理文件，否则保留 JSON 和 TXT 两类产物，方便后续再加工。

## Extraction Notes

- 腾讯会议录制页通常是虚拟滚动列表，DOM 里只保留可见条目。不要依赖遍历可见节点抓逐字稿，优先使用 React Fiber 中的内部数据数组。
- 数据数组里可能有 `speaker` 为空的占位项，抽取时要过滤。
- `start_time` 以毫秒存储；会议纪要里统一展示为 `MM:SS`。
- [scripts/extract_transcript.js](scripts/extract_transcript.js) 已经写成可直接传给 `mcp__chrome_devtools__evaluate_script` 的 `function()` 声明格式，不要再包一层 IIFE。注意：`evaluate_script` 不支持箭头函数语法，脚本必须使用 `function` 声明。
- [scripts/extract_transcript_to_clipboard.js](scripts/extract_transcript_to_clipboard.js) 使用 `async function()` 声明格式，把浏览器里的原始结构化 JSON 直接写入系统剪贴板，适合后续由 `save_transcript_json.py --from-clipboard` 落盘。
- Windows/PowerShell 落盘的临时 JSON 可能带 UTF-8 BOM；`save_transcript_json.py` 和 `format_minutes.py` 已兼容 `utf-8-sig`。
- 如果腾讯会议页面结构调整导致抽取失败，优先更新 [scripts/extract_transcript.js](scripts/extract_transcript.js) 的选择器和 Fiber 回溯逻辑。

## Output

生成两个产物：

- `output/json/{会议时间}_{会议号}_{发言人统计}_codex.json`：原始结构化逐字稿数据。
- `output/txt/{会议时间}_{会议号}_{发言人统计}_codex.txt`：格式化后的可读会议纪要。

TXT 内容结构固定为：

```text
会议纪要
================================================================================
会议主题：...
预定人：...
会议时间：...
会议号：...
导出时间：...
总发言数：...
================================================================================

发言人统计：
  - 张三: 12 次发言
  - 李四: 8 次发言

================================================================================

[00:03] 张三:
发言内容
```

## Resources

- [scripts/extract_transcript.js](scripts/extract_transcript.js)：浏览器端逐字稿抽取函数。使用 `function()` 声明格式（`evaluate_script` 不支持箭头函数）。
- [scripts/extract_transcript_to_clipboard.js](scripts/extract_transcript_to_clipboard.js)：把浏览器中的原始逐字稿 JSON 写入系统剪贴板。使用 `async function()` 声明格式。
- [scripts/save_transcript_json.py](scripts/save_transcript_json.py)：先保存浏览器抽取到的原始结构化 JSON。
- [scripts/format_minutes.py](scripts/format_minutes.py)：只从已保存的 JSON 生成会议纪要 TXT。
