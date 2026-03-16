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

### プレーンテキスト翻訳 / Plain Text Translation

```bash
echo 'Hello, world!' | apple-translate --from en --to ja
# => こんにちは、世界！

echo "こんにちは" | apple-translate --from ja --to en
# => Hello
```

短縮形・フル形どちらの言語コードも使えます。
Both short and full language codes are accepted.

```bash
# 短縮形 / Short form
echo "Hello" | apple-translate --from en --to ja

# フル形 / Full form (maximalIdentifier)
echo "Hello" | apple-translate --from en-Latn-US --to ja-Jpan-JP
```

### 利用可能な言語一覧 / List Available Languages

```bash
apple-translate --list-languages
```

### オプション一覧 / Options

```
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

```bash
brew uninstall apple-translate
brew untap taogya/AppleTranslateScript
```

### ソースからインストールした場合 / Manual

```bash
rm /usr/local/bin/apple-translate
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
4. `Formula/apple-translate.rb` を更新
   ```bash
   # tar.gz の SHA256 を取得
   curl -sL https://github.com/taogya/AppleTranslateScript/archive/refs/tags/vX.Y.Z.tar.gz | shasum -a 256
   ```
   - `url` のバージョンを更新
   - `sha256` を更新
5. Formula をコミット＆プッシュ

## License

BSD 3-Clause
