#!/usr/bin/env python3
"""批量将各类文件（PDF/Office/图片/音频/网页/压缩包等）转换为 Markdown。

底层使用 microsoft/markitdown，本脚本补充官方 CLI 缺少的批量与目录扫描能力。
"""

import argparse
import os
import re
import sys

try:
    from markitdown import MarkItDown
except ImportError:
    print("Missing dependency: markitdown")
    print("Install it with: python3 -m pip install 'markitdown[all]'")
    raise SystemExit(1)

# markitdown 0.1.7 内置转换器接受的扩展名，用于扫描目录时过滤
SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".pptx",
    ".xlsx",
    ".xls",
    ".csv",
    ".json",
    ".jsonl",
    ".txt",
    ".text",
    ".md",
    ".markdown",
    ".html",
    ".htm",
    ".xml",
    ".rss",
    ".atom",
    ".zip",
    ".epub",
    ".msg",
    ".ipynb",
    ".jpg",
    ".jpeg",
    ".png",
    ".wav",
    ".mp3",
    ".m4a",
    ".mp4",
}

# 扫描目录时跳过：本身已经是 Markdown，转换等于原样复制
SCAN_SKIP_EXTENSIONS = {".md", ".markdown"}


def log(message):
    """进度信息走 stderr，保证 --stdout 输出的是纯 Markdown。"""
    print(message, file=sys.stderr)


def is_url(value):
    return value.startswith("http://") or value.startswith("https://")


def url_to_filename(url):
    """把 URL 变成一个安全的 .md 文件名。"""
    name = re.sub(r"^https?://", "", url)
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
    return (name[:80] or "url") + ".md"


def scan_directory(directory, recursive):
    """扫描目录，返回受支持的文件列表。"""
    found = []
    if recursive:
        walker = os.walk(directory)
    else:
        walker = [(directory, [], os.listdir(directory))]

    for root, _dirs, files in walker:
        for filename in sorted(files):
            if filename.startswith("~$") or filename.startswith("."):
                continue
            extension = os.path.splitext(filename)[1].lower()
            if extension not in SUPPORTED_EXTENSIONS:
                continue
            if extension in SCAN_SKIP_EXTENSIONS:
                continue
            full_path = os.path.join(root, filename)
            if os.path.isfile(full_path):
                found.append(full_path)
    return found


def collect_inputs(paths, recursive):
    """把命令行参数展开成待转换的输入列表，并返回无效路径数量。"""
    inputs = []
    missing = 0
    for path in paths:
        if is_url(path):
            inputs.append(path)
        elif os.path.isdir(path):
            inputs.extend(scan_directory(path, recursive))
        elif os.path.isfile(path):
            inputs.append(path)
        else:
            log(f"Path not found: {path}")
            missing += 1
    return inputs, missing


def output_path_for(source, output_dir, taken):
    """算出输出路径；本次运行内重名的加序号，避免 a.csv 和 a.xlsx 互相覆盖。"""
    if is_url(source):
        target = os.path.join(output_dir or os.getcwd(), url_to_filename(source))
    elif output_dir:
        target = os.path.join(
            output_dir, os.path.basename(os.path.splitext(source)[0] + ".md")
        )
    else:
        target = os.path.splitext(source)[0] + ".md"

    base, ext = os.path.splitext(target)
    index = 1
    while target in taken:
        target = f"{base}_{index}{ext}"
        index += 1
    taken.add(target)
    return target


def main():
    parser = argparse.ArgumentParser(
        description="Convert files (PDF, Office, images, audio, HTML, ZIP, URLs...) to Markdown via markitdown."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="待转换的文件、目录或 URL；留空则扫描当前目录",
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="递归扫描子目录"
    )
    parser.add_argument(
        "-o", "--output-dir", help="输出目录；默认与源文件同目录"
    )
    parser.add_argument(
        "--stdout", action="store_true", help="输出到标准输出而非写文件"
    )
    parser.add_argument(
        "-p", "--use-plugins", action="store_true", help="启用第三方 markitdown 插件"
    )
    parser.add_argument(
        "--keep-data-uris",
        action="store_true",
        help="保留 data URI（如 base64 图片），默认截断",
    )
    args = parser.parse_args()

    paths = args.paths or [os.getcwd()]
    inputs, missing = collect_inputs(paths, args.recursive)

    if not inputs:
        log("No supported files found to convert.")
        return 1 if missing else 0

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)

    log(f"Found {len(inputs)} item(s) to convert.")
    converter = MarkItDown(enable_plugins=args.use_plugins)

    failures = missing
    taken = set()
    for source in inputs:
        target = output_path_for(source, args.output_dir, taken)
        if (
            not args.stdout
            and not is_url(source)
            and os.path.abspath(target) == os.path.abspath(source)
        ):
            log(f"Skipping (output would overwrite input): {source}")
            continue

        log(f"Processing: {source}")
        try:
            result = converter.convert(source, keep_data_uris=args.keep_data_uris)
        except Exception as exc:  # markitdown 对不支持的格式会抛异常
            log(f"Error converting {source}: {exc}")
            failures += 1
            continue

        if args.stdout:
            print(result.text_content)
            continue

        with open(target, "w", encoding="utf-8") as handle:
            handle.write(result.text_content)
        log(f"Created: {target}")

    if failures:
        log(f"{failures} item(s) failed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
