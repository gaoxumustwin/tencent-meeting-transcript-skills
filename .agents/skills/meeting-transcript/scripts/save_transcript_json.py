#!/usr/bin/env python3
"""
将浏览器抽取到的原始逐字稿数据先落盘为结构化 JSON。

用法:
  python save_transcript_json.py <json-path> [output-root-dir]
  python save_transcript_json.py < input.json
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from artifact_utils import build_file_stem, ensure_output_dirs


def save_transcript_json(data, output_dir=None):
    stem = build_file_stem(data)
    json_dir, _ = ensure_output_dirs(output_dir)
    json_path = json_dir / f"{stem}.json"
    json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"已保存结构化 JSON 文件：{json_path.absolute()}")
    print(f"文件基名：{stem}")
    print(f"JSON_PATH={json_path.absolute()}")
    print(f"BASENAME={stem}")

    return {
        "json_path": str(json_path.absolute()),
        "stem": stem,
    }


def read_clipboard_text():
    command = [
        "powershell",
        "-NoProfile",
        "-Command",
        "[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; Get-Clipboard -Raw",
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Save transcript JSON artifacts.")
    parser.add_argument("source_path", nargs="?", help="Path to a JSON file. Omit to read from stdin.")
    parser.add_argument("--from-clipboard", action="store_true", help="Read raw JSON from the system clipboard.")
    parser.add_argument("--output-root-dir", dest="output_root_dir", help="Root output directory.")
    args = parser.parse_args()

    if args.from_clipboard:
        output_dir = args.output_root_dir
        data = json.loads(read_clipboard_text())
    elif args.source_path:
        source_path = Path(args.source_path)
        output_dir = args.output_root_dir
        data = json.loads(source_path.read_text(encoding="utf-8-sig"))
    else:
        data = json.load(sys.stdin)
        output_dir = args.output_root_dir

    if data.get("error"):
        print(f'错误：{data["error"]}', file=sys.stderr)
        sys.exit(1)

    save_transcript_json(data, output_dir)


if __name__ == "__main__":
    main()
