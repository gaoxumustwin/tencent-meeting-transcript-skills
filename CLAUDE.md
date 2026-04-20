# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI agent skill repository for exporting Tencent Meeting (腾讯会议) recording transcripts. It contains two parallel skill implementations for different agent platforms, plus shared output artifacts.

## Dual Skill Architecture

Two independent skill trees exist for the same functionality:

- **Codex skill**: `.agents/skills/meeting-transcript/` — the original proven implementation. Has a separate `agents/openai.yaml` for Codex-specific invocation policy.
- **Claude Code skill**: `.claude/skills/meeting-transcript/` — the active implementation used by Claude Code. Uses SKILL.md frontmatter (`allowed-tools`, `when_to_use`) instead of a separate policy file.

Both share the same pipeline design and nearly identical scripts. Changes to browser extraction logic (`extract_transcript.js`, `extract_transcript_to_clipboard.js`) should be made in both directories to maintain parity.

## Pipeline Architecture

The transcript extraction follows a fixed pipeline — the skill's core design principle is that the agent should not improvise intermediate steps:

1. Browser: navigate to recording page → switch to "逐字稿" tab
2. Browser: run `extract_transcript.js` via `evaluate_script` to validate extraction (returns items, meta, pageMeta)
3. Browser: run `extract_transcript_to_clipboard.js` via `evaluate_script` to write raw JSON to system clipboard
4. Local: `save_transcript_json.py --from-clipboard` reads clipboard and writes `output/json/{basename}.json`
5. Local: `format_minutes.py` reads that JSON and writes `output/txt/{basename}.txt`

Steps 3→4 must happen immediately with no intervening operations — clipboard is a transient channel with a race-condition window.

## Script Roles

- `extract_transcript.js`: Arrow function `() => {...}` format, directly executable as `evaluate_script` function parameter. Uses React Fiber (`__reactFiber$` keys) to find internal data arrays, not DOM traversal (page uses virtual scrolling).
- `extract_transcript_to_clipboard.js`: Async arrow function `async () => {...}`. Same extraction logic plus `navigator.clipboard.writeText()`.
- `save_transcript_json.py`: Reads clipboard via PowerShell with UTF-8 encoding fix. Outputs `JSON_PATH=...` and `BASENAME=...` markers for pipeline chaining.
- `format_minutes.py`: Reads saved JSON only. Outputs `TXT_PATH=...` and `BASENAME=...`.
- `artifact_utils.py`: Shared naming (`build_file_stem`) and directory setup (`ensure_output_dirs`). Both Python scripts import from this module. `artifact_utils.py` must be in the same directory as the scripts that import it — do not move it to a separate lib location.

## Naming Convention

Basename format: `{meeting_time}_{meeting_id}_{speaker_stats}_{source_suffix}`
- Codex suffix: `_codex`
- Claude Code suffix: `_Claude`

The suffix is defined in `artifact_utils.py` as `ARTIFACT_SUFFIX`. Changing it there changes it everywhere.

## Development Commands

```powershell
# Syntax-check all Python scripts (both skill trees)
python -m py_compile .agents/skills/meeting-transcript/scripts/artifact_utils.py .agents/skills/meeting-transcript/scripts/save_transcript_json.py .agents/skills/meeting-transcript/scripts/format_minutes.py
python -m py_compile .claude/skills/meeting-transcript/scripts/artifact_utils.py .claude/skills/meeting-transcript/scripts/save_transcript_json.py .claude/skills/meeting-transcript/scripts/format_minutes.py

# Regenerate TXT from an existing JSON (skip browser extraction)
python .claude/skills/meeting-transcript/scripts/format_minutes.py "output/json/{basename}.json" --output-root-dir output

# Save JSON from clipboard (after running extract_transcript_to_clipboard.js in browser)
python .claude/skills/meeting-transcript/scripts/save_transcript_json.py --from-clipboard --output-root-dir output
```

There is no formal test suite. Validate changes by: running `py_compile`, then executing the full JSON→TXT flow on a real or captured transcript, and verifying both output directories receive matching basenames.

## Known Runtime Issues

- Windows console defaults to GBK/CP936; Python scripts configure UTF-8 on stdout/stderr at startup (`configure_stdio()`), but agent-side parsing of stdout may still encounter mojibake. If `JSON_PATH` / `BASENAME` markers are unreadable, fall back to `ls output/json/` to discover the filename.
- `pageMeta.topic` often falls back to the "某某预定的会议" title line because Tencent Meeting recording pages rarely have an explicit topic field. The `extract_transcript.js` regex fallback handles this.
- `wait_for` tool matches visible page text only — never use it with CSS class names like `minutes-module-list`.