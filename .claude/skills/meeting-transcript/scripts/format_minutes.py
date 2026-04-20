#!/usr/bin/env python3
"""
从已保存的腾讯会议逐字稿 JSON 生成会议纪要 TXT。

用法:
  python format_minutes.py <json-path> [output-root-dir]
  python format_minutes.py < input.json
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from artifact_utils import build_file_stem, ensure_output_dirs


def configure_stdio():
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def format_minutes(data, output_dir=None):
    items = data.get("items", [])
    meta = data.get("meta", {})
    page_meta = data.get("pageMeta", {})

    speakers = meta.get("speakers", {})
    sorted_speakers = sorted(speakers.items(), key=lambda item: (-item[1], item[0]))

    separator = "=" * 80
    lines = ["会议纪要", separator]

    if page_meta.get("topic"):
        lines.append(f'会议主题：{page_meta["topic"]}')
    if page_meta.get("organizer"):
        lines.append(f'预定人：{page_meta["organizer"]}')
    if page_meta.get("meetingTime"):
        lines.append(f'会议时间：{page_meta["meetingTime"]}')
    if page_meta.get("meetingId"):
        lines.append(f'会议号：{page_meta["meetingId"]}')

    lines.append(f'导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'总发言数：{meta.get("totalItems", len(items))}')
    lines.append(separator)
    lines.append("")
    lines.append("发言人统计：")

    for name, count in sorted_speakers:
        lines.append(f"  - {name}: {count} 次发言")

    lines.append("")
    lines.append(separator)
    lines.append("")

    for item in items:
        time_str = item.get("start_time_formatted", "")
        if not time_str and item.get("start_time_ms") is not None:
            total_sec = int(item["start_time_ms"] / 1000)
            minutes, seconds = divmod(total_sec, 60)
            time_str = f"{minutes:02d}:{seconds:02d}"

        speaker = item.get("speaker", "未知")
        text = item.get("text", "")

        lines.append(f"[{time_str}] {speaker}:")
        lines.append(text)
        lines.append("")

    stem = build_file_stem(data)
    _, txt_dir = ensure_output_dirs(output_dir)
    out_path = txt_dir / f"{stem}.txt"

    content = "\n".join(lines)
    out_path.write_text(content, encoding="utf-8")

    print(f"已生成会议纪要文件：{out_path.absolute()}")
    print(f"总发言数：{len(items)}")
    if sorted_speakers:
        stats = ", ".join(f"{name}({count}次)" for name, count in sorted_speakers)
        print(f"发言人：{stats}")
    else:
        print("发言人：无")
    print(f"TXT_PATH={out_path.absolute()}")
    print(f"BASENAME={stem}")

    return {
        "txt_path": str(out_path.absolute()),
        "stem": stem,
    }


def main():
    configure_stdio()
    parser = argparse.ArgumentParser(description="Format transcript JSON into minutes TXT.")
    parser.add_argument("json_path", nargs="?", help="Path to the saved transcript JSON. Omit to read from stdin.")
    parser.add_argument("--output-root-dir", dest="output_root_dir", help="Root output directory.")
    args = parser.parse_args()

    if args.json_path:
        json_path = Path(args.json_path)
        output_dir = args.output_root_dir
        data = json.loads(json_path.read_text(encoding="utf-8-sig"))
    else:
        data = json.load(sys.stdin)
        output_dir = args.output_root_dir

    if data.get("error"):
        print(f'错误：{data["error"]}', file=sys.stderr)
        sys.exit(1)

    result = format_minutes(data, output_dir)
    if result:
        print(f'文件基名：{result["stem"]}')


if __name__ == "__main__":
    main()
