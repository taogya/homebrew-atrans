# AppleTranslateScript

Apple Translation API を使って CSV ファイルを英語から日本語に翻訳する CLI ツール。

## 必要環境

- macOS 26 以降
- Swift 6.2 以降
- Python 3.10 以降

## ビルド

```bash
cd apple_translate
swift build -c release
```

## 使い方

```bash
python translate.py <入力CSV> -o <出力CSV> -c <翻訳カラム名...>
```

### 例

```bash
python translate.py sample.csv -o output.csv -c title description
```

`sample.csv` の `title` と `description` カラムを日本語に翻訳し、`output.csv` に出力します。

## Swift CLI 単体での利用

stdin に JSON Lines を渡して直接翻訳することもできます。

```bash
echo '{"text":"Hello, world!"}' | ./apple_translate/.build/release/apple-translate --from en --to ja
# => {"text":"こんにちは、世界！"}
```
