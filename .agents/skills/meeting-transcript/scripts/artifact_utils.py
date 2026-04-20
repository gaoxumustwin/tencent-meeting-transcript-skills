#!/usr/bin/env python3
"""Shared helpers for transcript artifact naming and output paths."""

from pathlib import Path


INVALID_FILENAME_CHARS = '<>:"/\\|?*'
ARTIFACT_SUFFIX = "_codex"


def sanitize_filename(value: str) -> str:
    cleaned = "".join("_" if ch in INVALID_FILENAME_CHARS else ch for ch in value).strip()
    return cleaned or "会议"


def build_file_stem(data):
    meta = data.get("meta", {})
    page_meta = data.get("pageMeta", {})

    meeting_time = sanitize_filename(page_meta.get("meetingTime", "未知时间"))
    meeting_id = sanitize_filename(page_meta.get("meetingId", "未知会议号"))

    speakers = meta.get("speakers", {})
    sorted_speakers = sorted(speakers.items(), key=lambda item: (-item[1], item[0]))
    if sorted_speakers:
        speaker_part = "、".join(f"{sanitize_filename(name)}{count}" for name, count in sorted_speakers)
    else:
        speaker_part = "无发言人统计"

    return f"{meeting_time}_{meeting_id}_{speaker_part}{ARTIFACT_SUFFIX}"


def ensure_output_dirs(output_root):
    root = Path(output_root) if output_root else Path("output")
    json_dir = root / "json"
    txt_dir = root / "txt"
    json_dir.mkdir(parents=True, exist_ok=True)
    txt_dir.mkdir(parents=True, exist_ok=True)
    return json_dir, txt_dir
