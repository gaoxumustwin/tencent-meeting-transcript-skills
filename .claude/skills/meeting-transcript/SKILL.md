---
name: meeting-transcript
description: 从腾讯会议录制页面提取完整逐字稿，并将原始 JSON 与格式化后的会议纪要 TXT 保存到当前项目的 output/ 目录下。适用于用户提供 `meeting.tencent.com/cw/...` 录制链接、`meeting.tencent.com/crm/...` 分享链接，并要求导出逐字稿、生成会议纪要、保存会议记录、提取录制页文本或将录制内容落盘到项目中的场景。
when_to_use: 当用户贴出腾讯会议录制页链接或分享链接，或描述“导出逐字稿”“生成会议纪要”“保存会议记录”“提取录制页面文本”“把录制内容保存到项目里”时使用。优先处理 `meeting.tencent.com/cw/...` 和 `meeting.tencent.com/crm/...`。不要用于其他会议平台，也不要用于用户已经直接粘贴了完整逐字稿文本的情况。
argument-hint: [meeting-recording-url]
allowed-tools:
  - "mcp__chrome-devtools__navigate_page"
  - "mcp__chrome-devtools__take_snapshot"
  - "mcp__chrome-devtools__click"
  - "mcp__chrome-devtools__evaluate_script"
  - "mcp__chrome-devtools__wait_for"
  - "Read"
  - "Write"
  - "Bash(python *)"
---

# 腾讯会议逐字稿导出

处理腾讯会议录制链接，从录制页提取完整逐字稿数据，先保存原始结构化 JSON，再在当前项目的 `output/` 目录生成会议纪要 TXT。若通过 `/meeting-transcript` 直接调用，则优先使用 `$ARGUMENTS`；若是自动触发，则从当前用户消息中识别 `meeting.tencent.com/cw/...` 录制链接或 `meeting.tencent.com/crm/...` 分享链接。

## Workflow

1. 从 `$ARGUMENTS` 或当前用户消息中获取腾讯会议链接。优先接受 `https://meeting.tencent.com/cw/...` 录制页，也接受 `https://meeting.tencent.com/crm/...` 分享链接。`crm` 链接通常会自动重定向到 `cw` 录制页；若未自动跳转，先观察页面提示再继续。
2. 使用 `mcp__chrome-devtools__navigate_page` 打开链接。如果页面要求登录、授权、验证码或中间确认，暂停并提示用户先完成页面交互。
3. 页面稳定后使用 `mcp__chrome-devtools__take_snapshot` 获取结构。如果当前不是“逐字稿”标签页，点击文本为“逐字稿”的元素切换过去。不要用 `mcp__chrome-devtools__wait_for` 等待 `minutes-module-list` 这类 CSS class 名；`wait_for` 只能匹配页面可见文本。如果确实需要等待，请等待“逐字稿”或其他可见文字。
4. 读取 [scripts/extract_transcript.js](scripts/extract_transcript.js)，把文件内容原样作为 `mcp__chrome-devtools__evaluate_script` 的 `function` 参数执行。这个脚本已经是可直接执行的 `function()` 声明格式，不要再包 IIFE，也不要手工去壳。注意：`evaluate_script` 不支持箭头函数语法，脚本必须使用 `function` 声明。
5. 检查返回值：
   - 如果包含 `error`，直接向用户报告并停止。
   - 如果 `items` 为空，先确认是否真的切到了“逐字稿”视图，再重试一次。
   - 如果 `pageMeta` 缺字段，优先依赖脚本里的 DOM 文本回退；仍缺失时，再根据最新 snapshot 或 `document.body.innerText` 补齐后继续。特别是 `topic` 缺失时，应优先使用页面上类似“某某预定的会议”的标题行作为兜底标题。
6. 再读取 [scripts/extract_transcript_to_clipboard.js](scripts/extract_transcript_to_clipboard.js)，通过 `mcp__chrome-devtools__evaluate_script` 执行，把浏览器中抽取到的原始 JSON 写进系统剪贴板。执行成功后返回值里应包含 `copied: true`。
7. 剪贴板是中间传输通道，存在短暂竞态窗口。执行完上一步后，立刻继续保存 JSON；这两步之间不要插入无关操作，也不要复制其他内容。
8. 立即运行：

```powershell
python "${CLAUDE_SKILL_DIR}/scripts/save_transcript_json.py" --from-clipboard --output-root-dir output
```

9. 读取 `save_transcript_json.py` 的输出，优先使用 `JSON_PATH=...` 或 `BASENAME=...` 继续生成 TXT。
10. 运行：

```powershell
python "${CLAUDE_SKILL_DIR}/scripts/format_minutes.py" "output/json/{basename}.json" --output-root-dir output
```

11. 文件命名统一使用 `会议时间 + 会议号 + 发言人统计 + _Claude` 组成 basename。JSON 输出到 `output/json/{basename}.json`，TXT 输出到 `output/txt/{basename}.txt`。
12. 读取生成的 TXT 文件，向用户报告 JSON/TXT 文件路径、会议时间、会议号、总发言数和发言人统计。
13. 除非用户要求清理文件，否则保留 JSON 和 TXT 两类产物，方便后续再加工。

## Extraction Notes

- 腾讯会议录制页通常是虚拟滚动列表，DOM 里只保留可见条目。不要依赖遍历可见节点抓逐字稿，优先使用 React Fiber 中的内部数据数组。
- 数据数组里可能有 `speaker` 为空的占位项，抽取时要过滤。
- `start_time` 以毫秒存储；会议纪要里统一展示为 `MM:SS`。
- [scripts/extract_transcript.js](scripts/extract_transcript.js) 用于验证抽取结果和元信息。
- [scripts/extract_transcript_to_clipboard.js](scripts/extract_transcript_to_clipboard.js) 把浏览器中的原始逐字稿 JSON 直接写入系统剪贴板。
- [scripts/save_transcript_json.py](scripts/save_transcript_json.py) 通过脚本内置的 PowerShell UTF-8 配置读取剪贴板，并在 Windows 上显式把 stdout/stderr 切到 UTF-8，减少控制台乱码导致的流水线中断。
- [scripts/format_minutes.py](scripts/format_minutes.py) 只从已保存的 JSON 生成会议纪要 TXT，并在 Windows 上显式把 stdout/stderr 切到 UTF-8。
- 如果腾讯会议页面结构调整导致抽取失败，优先更新 [scripts/extract_transcript.js](scripts/extract_transcript.js) 的选择器和 Fiber 回溯逻辑。

## Output

生成两个产物：

- `output/json/{会议时间}_{会议号}_{发言人统计}_Claude.json`：原始结构化逐字稿数据。
- `output/txt/{会议时间}_{会议号}_{发言人统计}_Claude.txt`：格式化后的可读会议纪要。

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
- [scripts/artifact_utils.py](scripts/artifact_utils.py)：统一 JSON/TXT 产物的 basename 和输出目录。
