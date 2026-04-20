# Repository Guidelines

## Project Structure & Module Organization
This repository is centered on a single Codex skill for Tencent Meeting transcript export.

- `.agents/skills/meeting-transcript/`: source of truth for the Codex skill.
- `.agents/skills/meeting-transcript/scripts/`: implementation scripts.
  `extract_transcript.js` validates page extraction, `extract_transcript_to_clipboard.js` copies raw JSON from the browser, `save_transcript_json.py` persists JSON, `format_minutes.py` renders TXT, and `artifact_utils.py` owns shared naming/output logic.
- `.agents/skills/meeting-transcript/agents/openai.yaml`: Codex skill metadata and invocation policy.
- `.claude/`: legacy Claude version kept for reference only; do not update it unless migration work requires parity.
- `output/json/` and `output/txt/`: generated artifacts. Treat them as outputs, not source files.

## Build, Test, and Development Commands
Use Python and PowerShell from the repo root.

- `python -m py_compile .agents/skills/meeting-transcript/scripts/artifact_utils.py .agents/skills/meeting-transcript/scripts/save_transcript_json.py .agents/skills/meeting-transcript/scripts/format_minutes.py`
  Syntax-check Python scripts.
- `python .agents/skills/meeting-transcript/scripts/save_transcript_json.py --from-clipboard --output-root-dir output`
  Save transcript JSON copied from the browser.
- `python .agents/skills/meeting-transcript/scripts/format_minutes.py "output/json/{basename}.json" --output-root-dir output`
  Generate the minutes TXT from a saved JSON file.

## Coding Style & Naming Conventions
Use ASCII unless the file already contains Chinese business text. Follow existing style: 4-space indentation in Python, small focused functions, and shared filename logic in `artifact_utils.py` instead of duplicating it. Keep browser extraction logic in JavaScript and local file generation in Python.

Generated filenames must follow:
`{meeting_time}_{meeting_id}_{speaker_stats}.{ext}`

## Testing Guidelines
There is no formal test suite in this workspace. Minimum validation for every change:

- run `py_compile` on touched Python files;
- execute the JSON-to-TXT flow on a real or captured transcript sample;
- verify both `output/json/` and `output/txt/` receive files with the same basename.

## Commit & Pull Request Guidelines
This workspace snapshot does not include a `.git` directory, so local Git history is unavailable. Use short conventional commit messages such as `fix: harden clipboard JSON import` or `docs: update skill workflow`.

PRs should describe the recording scenario tested, note any Tencent Meeting UI assumptions, and include the exact commands used for verification.

## Security & Configuration Tips
Tencent Meeting recording pages may require an authenticated browser session. Do not commit sensitive meeting outputs or real customer transcript data unless explicitly requested.
