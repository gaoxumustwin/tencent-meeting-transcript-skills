# 腾讯会议逐字稿导出仓库

这个仓库用于把腾讯会议录制页面里的逐字稿稳定导出为两类产物：

- 结构化原始 JSON
- 可直接阅读和转发的会议纪要 TXT

它同时包含两套 skill 实现：

- Codex 版：`.agents/skills/meeting-transcript/`
- Claude Code 版：`.claude/skills/meeting-transcript/`

两套 skill 的目标一致，都是从腾讯会议录制页提取完整逐字稿，先保存原始 JSON，再基于 JSON 生成 TXT。这样做的好处是，既能保留后续再加工所需的结构化数据，也能立即拿到可读的会议纪要文本。

## 这是什么

这是一个面向 AI coding agent 的技能仓库，不是传统 Web 应用，也不是命令行产品本体。你可以把它理解成：

- 一套给 Codex 用的 `meeting-transcript` skill
- 一套给 Claude Code 用的 `meeting-transcript` skill
- 一组已经验证过的辅助脚本，用来降低浏览器抽取、JSON 落盘、TXT 生成这条链路的失败率

核心思路是固定流水线，而不是让模型临场发挥：

1. 打开腾讯会议录制页
2. 切换到“逐字稿”
3. 从页面内部数据中抽取完整逐字稿
4. 先保存原始 JSON
5. 再从 JSON 生成 TXT

## 适用场景

这个仓库适合下面几类场景：

- 会后快速导出逐字稿，并生成一份可发给团队的会议纪要
- 保留原始 JSON，方便后续做摘要、结构化分析、知识库入库或二次加工
- 需要把会议记录稳定落盘到项目目录，而不是只停留在浏览器页面里
- 需要区分不同 agent 生成的产物，例如 Codex 和 Claude Code 分别导出的文件
- 一次会议被拆成多个录制视频时，按片段逐个导出并统一整理

关于“一个会议多个视频”的说明：

- 本仓库不会自动把多个录制片段合并成一个总文件
- 但每个片段都会生成标准化命名的 JSON 和 TXT，且保留时间、会议号、发言人统计等信息
- 因此当一次会议被拆成多个录制片段时，可以逐个处理后按时间顺序整理，较容易保持内容连续性

## 当前支持范围

- 平台：腾讯会议录制页面
- 推荐链接：`meeting.tencent.com/cw/...`
- Claude Code 版也覆盖 `meeting.tencent.com/crm/...` 分享链接；这类链接通常会自动跳转到最终录制页

不适用的情况：

- 其他会议平台
- 用户已经直接粘贴了完整逐字稿文本，此时通常不需要再走浏览器抽取流程

## 仓库结构

```text
.agents/skills/meeting-transcript/
  SKILL.md
  agents/openai.yaml
  scripts/

.claude/skills/meeting-transcript/
  SKILL.md
  scripts/

output/json/
output/txt/
```

主要脚本职责如下：

- `extract_transcript.js`：从腾讯会议录制页抽取逐字稿和页面元信息
- `extract_transcript_to_clipboard.js`：把抽取到的原始 JSON 写入系统剪贴板
- `save_transcript_json.py`：把原始 JSON 落盘到 `output/json/`
- `format_minutes.py`：从已保存的 JSON 生成 `output/txt/`
- `artifact_utils.py`：统一 basename 和输出目录规则

## 输出规则

每次导出都会生成两类产物：

- `output/json/{basename}.json`
- `output/txt/{basename}.txt`

两套 skill 的 basename 会带不同尾缀，便于区分来源：

- Codex：`_codex`
- Claude Code：`_Claude`

下面的示例为了避免暴露真实发言人姓名，统一使用三个代号：

- `代号A`
- `代号B`
- `代号C`

例如：

```text
2026_04_17 20_59_495 243 551_代号A58、代号B35、代号C24_codex.txt
2026_04_17 20_59_495 243 551_代号A58、代号B35、代号C24_Claude.json
```

命名主体规则为：

```text
会议时间_会议号_发言人统计_来源后缀
```

这种命名方式有两个作用：

- 同一轮导出的 JSON 和 TXT 可以稳定配对
- 不同 agent 生成的文件不会混淆

### 输出目录示例

```text
output/
  json/
    2026_04_17 20_59_495 243 551_代号A58、代号B35、代号C24_codex.json
    2026_04_17 20_59_495 243 551_代号A58、代号B35、代号C24_Claude.json
  txt/
    2026_04_17 20_59_495 243 551_代号A58、代号B35、代号C24_codex.txt
    2026_04_17 20_59_495 243 551_代号A58、代号B35、代号C24_Claude.txt
```

### JSON 形式示例

JSON 是结构化原始数据，适合后续继续分析、做摘要、合并多个片段或导入知识库。典型结构如下：

```json
{
  "items": [
    {
      "pid": "495243551-001",
      "speaker": "代号A",
      "start_time_ms": 3000,
      "start_time_formatted": "00:03",
      "text": "我们先快速确认一下本次讨论的目标。"
    },
    {
      "pid": "495243551-002",
      "speaker": "代号B",
      "start_time_ms": 12500,
      "start_time_formatted": "00:12",
      "text": "这次主要聚焦在合作方式和后续排期。"
    }
  ],
  "meta": {
    "totalItems": 117,
    "speakers": {
      "代号A": 58,
      "代号B": 35,
      "代号C": 24
    }
  },
  "pageMeta": {
    "organizer": "代号A",
    "meetingTime": "2026/04/17 20:59",
    "meetingId": "495 243 551",
    "topic": "项目协作与排期讨论会"
  }
}
```

### TXT 形式示例

TXT 是面向阅读和转发的交付形式，会保留会议元信息、发言人统计和逐条发言内容。典型结构如下：

```text
会议纪要
================================================================================
会议主题：项目协作与排期讨论会
预定人：代号A
会议时间：2026/04/17 20:59
会议号：495 243 551
导出时间：2026-04-20 12:30:00
总发言数：117
================================================================================

发言人统计：
  - 代号A: 58 次发言
  - 代号B: 35 次发言
  - 代号C: 24 次发言

================================================================================

[00:03] 代号A:
我们先快速确认一下本次讨论的目标。

[00:12] 代号B:
这次主要聚焦在合作方式和后续排期。

[00:25] 代号C:
我补充一下资源侧当前能配合的时间窗口。
```

### 两种产物各自适合做什么

- JSON：适合后续自动处理，比如二次摘要、结构化分析、片段合并、统计发言频次。
- TXT：适合直接阅读、转发、归档，给团队成员快速查看会议内容。

## 如何使用

### 1. 使用前准备

无论是 Claude Code 还是 Codex，都建议先满足这些前提：

- 当前工作目录就是本仓库根目录
- 浏览器里已经登录腾讯会议，并且能打开录制页面
- Agent 具备浏览器 MCP / devtools 能力
- 本地可运行 Python

### 2. 在 Codex 中使用

Codex 版 skill 位于：

- `.agents/skills/meeting-transcript/`

推荐两种触发方式：

- 直接给出腾讯会议录制页链接，并说明“导出逐字稿/生成会议纪要”
- 显式提到 `$meeting-transcript`

示例：

```text
用这个链接导出会议逐字稿并生成纪要：https://meeting.tencent.com/cw/xxxx
```

```text
Use $meeting-transcript to extract the transcript from https://meeting.tencent.com/cw/xxxx and save JSON/TXT under output.
```

### 3. 在 Claude Code 中使用

Claude Code 版 skill 位于：

- `.claude/skills/meeting-transcript/`

当前设计支持两种方式：

- 自动触发：直接给录制链接并描述需求
- 手动调用：`/meeting-transcript <url>`

示例：

```text
请把这个腾讯会议录制页导出成逐字稿和会议纪要：https://meeting.tencent.com/cw/xxxx
```

```text
/meeting-transcript https://meeting.tencent.com/cw/xxxx
```

如果用户拿到的是分享链接，也可以直接提供：

```text
https://meeting.tencent.com/crm/xxxx
```

### 4. 本地脚本直接使用

如果你已经拿到了结构化 JSON，也可以跳过浏览器抽取，直接本地生成 TXT。

Codex 版示例：

```powershell
python .agents/skills/meeting-transcript/scripts/format_minutes.py "output/json/your_file.json" --output-root-dir output
```

Claude Code 版示例：

```powershell
python .claude/skills/meeting-transcript/scripts/format_minutes.py "output/json/your_file.json" --output-root-dir output
```

如果要检查 Python 脚本语法：

```powershell
python -m py_compile .agents/skills/meeting-transcript/scripts/artifact_utils.py .agents/skills/meeting-transcript/scripts/save_transcript_json.py .agents/skills/meeting-transcript/scripts/format_minutes.py
python -m py_compile .claude/skills/meeting-transcript/scripts/artifact_utils.py .claude/skills/meeting-transcript/scripts/save_transcript_json.py .claude/skills/meeting-transcript/scripts/format_minutes.py
```

## 工作流说明

两套 skill 都遵循同一个原则：

- 先验证页面已经进入“逐字稿”视图
- 先保存 JSON，再生成 TXT
- 不从 TXT 反推 JSON
- 保留中间产物，方便复查和二次加工

这比“直接让模型从页面内容写一份纪要”更稳定，原因在于：

- 页面使用虚拟滚动，DOM 中未必有完整逐字稿
- 结构化 JSON 更适合后续自动化处理
- TXT 只是面向阅读的最终呈现，不应该作为唯一数据源

## 已知限制

- 腾讯会议页面结构变化后，抽取脚本可能需要更新
- 登录、授权、验证码、中间确认等步骤仍然需要人工配合
- `crm` 分享链接通常会跳转到 `cw` 录制页，但不应把这种跳转视为永远稳定不变
- 多个录制片段不会自动合并，需要后续按时间顺序整理

## 什么时候优先保留 JSON

下面这些情况，建议一定保留 JSON，不要只保留 TXT：

- 之后还要继续做摘要或问答
- 需要重新排版纪要
- 一个会议有多个片段，后面要合并整理
- 需要追溯发言顺序、时间戳或发言人统计

## 建议使用方式

如果你只是要一份可读纪要：

- 直接让 agent 跑完整 skill，拿 JSON + TXT

如果你后面还要继续处理这次会议：

- 保留 `output/json/` 下的原始文件
- 把 `output/txt/` 视为给人看的交付层

这样同一份会议数据既能“马上可读”，又能“后续可加工”。

## License

This repository is licensed under the MIT License. See [LICENSE](LICENSE).
