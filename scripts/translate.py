"""
CSV ファイルの指定カラムを Apple Translation API (Swift CLI) で英語→日本語に翻訳する。

前提:
    - macOS 26 以降
    - atrans がビルド済み (swift build -c release) または PATH 上に存在

使い方:
    python scripts/translate.py input.csv -o output.csv -c column1 column2
"""

import argparse
import csv
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# PATH にあればそれを使い、なければローカルビルドを使う
_LOCAL_CLI = os.path.join(PROJECT_ROOT, ".build", "release", "atrans")
import shutil as _shutil
SWIFT_CLI = _shutil.which("atrans") or _LOCAL_CLI
BATCH_SIZE = 200


def check_cli():
    if not os.path.isfile(SWIFT_CLI):
        print(f"エラー: Swift CLI が見つかりません: {SWIFT_CLI}", file=sys.stderr)
        print("ビルド手順:", file=sys.stderr)
        print("  swift build -c release", file=sys.stderr)
        print("  または: .build/release/atrans を PATH に配置", file=sys.stderr)
        sys.exit(1)


def translate_batch(texts: list[str]) -> list[str]:
    """Swift CLI を呼び出してバッチ翻訳する。"""
    input_lines = "\n".join(texts)

    result = subprocess.run(
        [SWIFT_CLI, "--from", "en", "--to", "ja"],
        input=input_lines,
        capture_output=True,
        text=True,
        timeout=300,
    )

    if result.returncode != 0:
        print(f"  Swift CLI エラー (exit={result.returncode}):", file=sys.stderr)
        if result.stderr:
            print(f"  {result.stderr.strip()}", file=sys.stderr)
        return texts

    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            print(f"  [swift] {line}", file=sys.stderr)

    translated = [line for line in result.stdout.strip().split("\n") if line.strip()]

    # 行数が合わない場合は原文で補完
    while len(translated) < len(texts):
        translated.append(texts[len(translated)])
    return translated[: len(texts)]


def main():
    check_cli()

    parser = argparse.ArgumentParser(description="CSV翻訳ツール (Apple Translation API)")
    parser.add_argument("input", help="入力CSVファイル")
    parser.add_argument("-o", "--output", required=True, help="出力CSVファイル")
    parser.add_argument(
        "-c", "--columns", nargs="+", required=True, help="翻訳対象のカラム名"
    )
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    if not fieldnames:
        print("エラー: CSVにヘッダーがありません", file=sys.stderr)
        sys.exit(1)

    for col in args.columns:
        if col not in fieldnames:
            print(f"エラー: カラム '{col}' が見つかりません (利用可能: {fieldnames})", file=sys.stderr)
            sys.exit(1)

    print(f"入力: {args.input} ({len(rows)} 行)")
    print(f"翻訳カラム: {args.columns}")

    for col in args.columns:
        texts = [row[col] for row in rows]
        total = len(texts)

        for i in range(0, total, BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            print(f"  [{col}] {i + 1}-{i + len(batch)}/{total} ...", end=" ", flush=True)
            results = translate_batch(batch)
            for j, t in enumerate(results):
                rows[i + j][col] = t
            print("完了")

    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n出力: {args.output}")


if __name__ == "__main__":
    main()
