# atrans

Apple Translation API を使ったコマンドライン翻訳ツール。すべての翻訳はオンデバイスで処理され、データが外部に送信されることはありません。

A command-line translation tool powered by Apple Translation API. All translations are processed on-device — no data is ever sent externally.

## インストール / Installation

### Homebrew

このリポジトリには Homebrew Formula が含まれています。現在の Formula は `main` ブランチを参照する HEAD インストールです。

This repository includes a Homebrew formula. The current formula installs from the `main` branch as a HEAD build.

```bash
brew tap taogya/atrans
brew install --HEAD atrans
```

### ソースからビルド / Build from Source

```bash
git clone https://github.com/taogya/homebrew-atrans.git atrans
cd atrans
swift build -c release
# バイナリを PATH の通った場所にコピー / Copy binary to a directory in PATH
cp .build/release/atrans /usr/local/bin/
```

## 必要環境 / Requirements

- macOS 26 (Tahoe) 以降 / macOS 26 (Tahoe) or later
- Swift 6.2 以降 / Swift 6.2 or later
- 翻訳言語パックがダウンロード済みであること（システム設定 > 一般 > 翻訳言語）
- Translation language packs must be downloaded (System Settings > General > Translation Languages)

## 使い方 / Usage

### プレーンテキスト翻訳 / Plain Text Translation

```bash
# stdin（パイプ）
echo 'Hello, world!' | atrans --from en --to ja
# => こんにちは、世界！

echo "こんにちは" | atrans --from ja --to en
# => Hello
```

### 引数テキスト翻訳 / Argument Text Translation

```bash
# 位置引数
atrans 'Hello, world!' --from en --to ja
# => こんにちは、世界！

# --text フラグ
atrans --text 'Hello, world!' --from en --to ja
```

### ファイル入力 / File Input

```bash
atrans --file input.txt --from en --to ja
```

各行が個別に翻訳され、結果が stdout に出力されます。
Each line is translated individually and output to stdout.

> **注意 / Note:** 入力ソース（位置引数、`--text`、`--file`、stdin）は1つだけ指定してください。複数指定するとエラーになります。
> Only one input source (positional text, `--text`, `--file`, stdin) can be used at a time.

短縮形・フル形どちらの言語コードも使えます。
Both short and full language codes are accepted.

```bash
# 短縮形 / Short form
atrans 'Hello' --from en --to ja

# フル形 / Full form (maximalIdentifier)
atrans 'Hello' --from en-Latn-US --to ja-Jpan-JP
```

### 利用可能な言語一覧 / List Available Languages

```bash
atrans --list-languages
```

### オプション一覧 / Options

```
TEXT                 翻訳テキスト（位置引数） / Text to translate (positional argument)
--text <TEXT>        翻訳テキスト / Text to translate
--file <PATH>        ファイルからテキストを読み込み / Read text from file
--from <LANG>        翻訳元の言語コード（必須） / Source language (required)
--to <LANG>          翻訳先の言語コード（必須） / Target language (required)
--list-languages, -l 利用可能な言語の一覧を表示 / List available languages
--version, -v        バージョンを表示 / Show version
--help, -h           ヘルプを表示 / Show help
```

## CSV 翻訳スクリプト / CSV Translation Script

CSV ファイルを一括翻訳する Python ラッパーも付属しています。

A Python wrapper for batch-translating CSV files is also included.

```bash
python scripts/translate.py scripts/sample.csv -o output.csv -c title description
```

詳細は / See [scripts/translate.py](scripts/translate.py)

## プライバシー / Privacy

このツールは Apple Translation framework の `installedSource` を使用しており、翻訳はすべてオンデバイスで完結します。ネットワーク通信は一切行いません。

This tool uses the `installedSource` parameter of Apple's Translation framework, ensuring all translations are performed entirely on-device. No network communication occurs.

## アンインストール / Uninstall

### Homebrew

Homebrew でインストールした場合:

Installed with Homebrew:

```bash
brew uninstall atrans
brew untap taogya/atrans
```

### ソースからインストールした場合 / Manual

```bash
rm /usr/local/bin/atrans
```

## リリース手順 / Release Process

開発者向けの手順です。 / For maintainers.

1. `Sources/main.swift` のバージョン文字列を更新
2. コミット＆タグ作成
   ```bash
   git add -A && git commit -m "Bump version to vX.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```
3. GitHub でリリースを作成（タグ `vX.Y.Z`）
4. `Formula/atrans.rb` を更新
   ```bash
   # tar.gz の SHA256 を取得
   curl -sL https://github.com/taogya/homebrew-atrans/archive/refs/tags/vX.Y.Z.tar.gz | shasum -a 256
   ```
   - `url` のバージョンを更新
   - `sha256` を更新
5. Formula をコミット＆プッシュ

## License

BSD 3-Clause
