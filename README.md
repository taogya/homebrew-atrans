# apple-translate

Apple Translation API を使ったコマンドライン翻訳ツール。すべての翻訳はオンデバイスで処理され、データが外部に送信されることはありません。

A command-line translation tool powered by Apple Translation API. All translations are processed on-device — no data is ever sent externally.

## インストール / Installation

### Homebrew

```bash
brew tap taogya/AppleTranslateScript https://github.com/taogya/AppleTranslateScript
brew install apple-translate
```

### ソースからビルド / Build from Source

```bash
git clone https://github.com/taogya/AppleTranslateScript.git
cd AppleTranslateScript
swift build -c release
# バイナリを PATH の通った場所にコピー / Copy binary to a directory in PATH
cp .build/release/apple-translate /usr/local/bin/
```

## 必要環境 / Requirements

- macOS 26 (Tahoe) 以降 / macOS 26 (Tahoe) or later
- Swift 6.2 以降 / Swift 6.2 or later
- 翻訳言語パックがダウンロード済みであること（システム設定 > 一般 > 翻訳言語）
- Translation language packs must be downloaded (System Settings > General > Translation Languages)

## 使い方 / Usage

### プレーンテキスト翻訳 / Plain Text Translation (default)

```bash
echo "Hello, world!" | apple-translate
# => こんにちは、世界！

echo "こんにちは" | apple-translate --from ja --to en
# => Hello
```

### 利用可能な言語一覧 / List Available Languages

```bash
apple-translate --list-languages
```

### オプション一覧 / Options

```
--from <LANG>        翻訳元の言語コード / Source language (default: en)
--to <LANG>          翻訳先の言語コード / Target language (default: ja)
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

## License

BSD 3-Clause
