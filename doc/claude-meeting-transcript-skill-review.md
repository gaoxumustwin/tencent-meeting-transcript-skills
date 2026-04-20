# Claude Code `meeting-transcript` Skill 对比分析与修改建议

## 结论

Claude 版效果差，不是因为 Claude Code 的 skill 机制不行，而是当前 `.claude` 版还没有把 Codex 成功的“低自由度执行链”完整搬过去。它已经有脚本能力，但脚本流水线还不完整；Codex 版则已经形成了更完整、更稳定的执行链。

官方参考文档：
- https://code.claude.com/docs/zh-CN/skills

## 主要问题

### 1. `.claude` 版功能并不等价

当前 Claude 版入口在：
- `.claude/skills/meeting-transcript/SKILL.md`

成功的 Codex 版入口在：
- `.agents/skills/meeting-transcript/SKILL.md`

`.claude` 版只有两个脚本：
- `.claude/skills/meeting-transcript/scripts/extract_transcript.js`
- `.claude/skills/meeting-transcript/scripts/format_minutes.py`

而 Codex 版实际依赖了完整的 4 段流水线：
- `.agents/skills/meeting-transcript/scripts/extract_transcript.js`
- `.agents/skills/meeting-transcript/scripts/extract_transcript_to_clipboard.js`
- `.agents/skills/meeting-transcript/scripts/save_transcript_json.py`
- `.agents/skills/meeting-transcript/scripts/format_minutes.py`

以及统一命名逻辑：
- `.agents/skills/meeting-transcript/scripts/artifact_utils.py`

少了这些桥接环节后，Claude 只能自己临时拼 JSON、自己决定文件名、自己处理中间态，这正是最容易漂移的部分。

### 2. 浏览器抽取脚本的执行形式不对

Claude 版的 `extract_transcript.js` 是 IIFE：
- `.claude/skills/meeting-transcript/scripts/extract_transcript.js`

并且 `.claude` 版 `SKILL.md` 还要求模型在运行时把 IIFE 手工“去壳”后再传给 `evaluate_script`。

这会导致两个问题：
- 本来应由脚本层解决的问题，被推给模型临场改写
- 执行方式不稳定，增加失败概率

Codex 成功版已经改成可直接作为 `evaluate_script.function` 传入的 `() => { ... }` 形式，不需要模型二次加工。

### 3. 产物链路太松，没有稳定中间态

Claude 版 `format_minutes.py` 的行为是：
- 直接按“会议主题”输出一个 TXT
- 默认写到 `output/`

Codex 版的行为是：
- 先落盘原始结构化 JSON 到 `output/json/`
- 再从 JSON 生成 TXT 到 `output/txt/`
- 两个产物使用同一个 basename
- basename 由 `artifact_utils.py` 统一计算

这意味着 Claude 版缺少：
- 原始 JSON 可复用产物
- 可验证的中间状态
- JSON/TXT 一一对应关系
- 稳定命名规则

### 4. 当前 skill 的触发模式需要明确：手动命令型还是自动触发型

`.claude/skills/meeting-transcript/SKILL.md` 里设置了：

```yaml
disable-model-invocation: true
```

按 Claude Code 官方文档，这表示：
- Claude 不会自动根据自然语言加载这个 skill
- 只能由用户显式 `/meeting-transcript ...` 调用

这不是配置错误本身，而是一个设计选择：
- 如果目标是命令式入口 `/meeting-transcript <url>`，这个配置是合理的
- 如果目标是“用户贴一个腾讯会议录制链接，Claude 自动想到用这个 skill”，那它就与目标冲突

因此，这一项应被视为“设计决策点”，而不是默认意义上的 bug。

### 5. `allowed-tools` 需要避免依赖未文档化的 frontmatter 变量替换

当前 `.claude` 版里使用：

```yaml
allowed-tools:
  - "Bash(python:*)"
```

需要注意的是，Claude Code 官方文档把 `$ARGUMENTS`、`${CLAUDE_SKILL_DIR}` 等字符串替换能力定义在 skill content 中，没有说明它们会在 frontmatter 里生效。因此，不应把 `${CLAUDE_SKILL_DIR}` 放进 `allowed-tools` 里并假设它会被替换。

不建议这样写：

```yaml
allowed-tools:
  - "Bash(python ${CLAUDE_SKILL_DIR}/scripts/save_transcript_json.py *)"
  - "Bash(python ${CLAUDE_SKILL_DIR}/scripts/format_minutes.py *)"
```

更稳妥的做法是：
- `${CLAUDE_SKILL_DIR}` 只放在正文里的实际命令中使用
- `allowed-tools` 里使用固定工具名或保守的命令模式，例如 `Bash(python *)`
- 如果不希望把 `allowed-tools` 放宽到 `Bash(python *)`，那就不要依赖 frontmatter 预授权，改用正常权限确认

这里的关键点不是“能不能侥幸工作”，而是“不应依赖官方未说明支持的行为”。

## 修改建议

### 1. 先把 `.claude` skill 做成真正自包含

把以下文件从 Codex 版移植到 `.claude/skills/meeting-transcript/scripts/`：
- `extract_transcript_to_clipboard.js`
- `save_transcript_json.py`
- `artifact_utils.py`
- 对齐后的 `format_minutes.py`
- 对齐后的 `extract_transcript.js`

不要再让 `.claude` 版依赖 `.agents` 目录里的实现，否则它不是独立 skill。

### 2. 改成固定流水线，不让模型手工处理中间文件

把 Claude 版执行链收紧成和 Codex 一样的固定流程：

1. 打开腾讯会议录制页并切到“逐字稿”
2. 执行 `extract_transcript.js` 验证抽取结果
3. 执行 `extract_transcript_to_clipboard.js` 写系统剪贴板
4. 运行 `save_transcript_json.py --from-clipboard --output-root-dir output`
5. 从输出中读取 `JSON_PATH` 或 `BASENAME`
6. 运行 `format_minutes.py "output/json/{basename}.json" --output-root-dir output`
7. 最后只做读取和汇报，不做临场格式推断

核心原则：
- 先保存原始 JSON
- 再从 JSON 生成 TXT
- 不要先转 TXT，更不要从 TXT 反推 JSON

需要补充一个工程风险说明：
- 剪贴板作为中间通道存在小的竞态窗口
- 在 `extract_transcript_to_clipboard.js` 写入剪贴板后，应立即执行 `save_transcript_json.py --from-clipboard`
- 这两步之间不要插入无关操作，也不要手工复制其他内容

在当前方案下，这个风险通常可控，但应被明确写入 skill 说明，而不是默认忽略。

### 3. 把 `extract_transcript.js` 改成直接可执行函数

不要保留 IIFE，不要在 `SKILL.md` 里要求 Claude 自己拆包装。

建议改成：

```js
() => {
  // ...
};
```

然后在 `SKILL.md` 里明确写：

```text
读取 scripts/extract_transcript.js 后，将文件内容原样作为 evaluate_script 的 function 参数执行。
```

### 4. 把 `format_minutes.py` 对齐到 Codex 版行为

至少补齐这些能力：
- 支持 `utf-8-sig`
- 使用 `artifact_utils.py` 统一 basename
- 输出目录固定为 `output/txt/`
- 打印 `TXT_PATH=...`
- 打印 `BASENAME=...`
- 不再按“会议主题”直接生成文件名

这一步非常关键，因为稳定命名和稳定产物路径会显著提高 skill 的可预测性。

### 5. 根据目标调整 frontmatter

如果目标是“手动命令型 skill”，保留：

```yaml
disable-model-invocation: true
```

这时就应该把它设计成明确的命令式入口：

```text
/meeting-transcript <url>
```

在这种模式下，`description` 仍然可以保留，但重点应放在“人类可读的用途说明”，而不是堆自动触发关键词；因为官方文档明确说明，`disable-model-invocation: true` 时 description 不参与 Claude 的自动匹配上下文。

如果目标是“用户自然语言触发，Claude 自动调用”，就移除 `disable-model-invocation: true`，并强化 `description` 或增加 `when_to_use`，覆盖这些触发说法：
- 导出逐字稿
- 生成会议纪要
- 保存会议记录
- 提取录制页文本
- 把录制内容落盘到当前项目

### 6. 缩短正文，强化硬约束

Claude Code skill 的正文不应堆太多解释，而应把关键不可变流程写死。

当前 `.claude` 版存在的问题是：
- 解释多
- 中间态约束少
- 实际执行步骤自由度高

建议保留：
- 入口条件
- 固定执行步骤
- 失败分支
- 产物路径与命名规则

建议弱化：
- 大段格式说明
- 需要模型临场推断的描述

## 建议的 Claude 版 `SKILL.md` 结构

下面是一版更适合 Claude Code 的写法骨架：

```md
---
name: meeting-transcript
description: Export the full transcript from a Tencent Meeting recording page and save both raw JSON and formatted TXT minutes under output/. Use when the user provides a meeting.tencent.com/cw/... recording URL and asks to export transcript, generate minutes, save the recording text, or persist the page content in the project.
argument-hint: [meeting-recording-url]
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - mcp__chrome-devtools__navigate_page
  - mcp__chrome-devtools__take_snapshot
  - mcp__chrome-devtools__click
  - mcp__chrome-devtools__evaluate_script
  - mcp__chrome-devtools__wait_for
  - Bash(python *)
---

处理 `$ARGUMENTS`：

1. 打开录制页并切到“逐字稿”标签。
2. 读取 `scripts/extract_transcript.js`，原样传给 `evaluate_script` 执行。
3. 若返回 `error`，立即停止并报告。
4. 再执行 `scripts/extract_transcript_to_clipboard.js`，确认返回 `copied: true`。
5. 运行 `python ${CLAUDE_SKILL_DIR}/scripts/save_transcript_json.py --from-clipboard --output-root-dir output`
6. 不要在这一步和下一步之间做任何无关操作，立即从剪贴板落盘。
7. 从输出中读取 `JSON_PATH` 或 `BASENAME`。
8. 运行 `python ${CLAUDE_SKILL_DIR}/scripts/format_minutes.py "output/json/{basename}.json" --output-root-dir output`
9. 报告生成的 JSON/TXT 路径和会议摘要。
```

如果不希望把 `allowed-tools` 放宽到 `Bash(python *)`，就不要在 frontmatter 里预授权脚本路径变量；改为保留正常权限确认，正文里的命令仍然使用 `${CLAUDE_SKILL_DIR}`。

## 最终建议

真正应该迁移的不是“文字风格”，而是 Codex 版已经验证过的这些能力：
- 低自由度执行链
- 自包含脚本资源
- JSON 先落盘再转 TXT
- 统一 basename
- 明确的错误分支
- 直接可执行的浏览器脚本

此外，还应明确两类实现边界：
- `disable-model-invocation: true` 是触发策略选择，不是默认错误
- PowerShell 不是要被绕开，而是要通过脚本内置的 UTF-8 配置稳定使用

只要把这些点一起搬进 `.claude/skills/meeting-transcript`，Claude Code 的 skill 效果会明显改善。
