/// Apple Translation API を使った CLI 翻訳ツール。
///
/// stdin から JSON Lines を読み取り、各行を翻訳して stdout に JSON Lines で出力する。
///
/// 入力形式 (JSON Lines):
///   {"text": "Hello, world!"}
///   {"text": "How are you?"}
///
/// 出力形式 (JSON Lines):
///   {"text": "こんにちは、世界！"}
///   {"text": "お元気ですか？"}
///
/// 使い方:
///   echo '{"text":"Hello"}' | .build/release/apple-translate --from en --to ja

import Foundation
import Translation

@main
struct AppleTranslateCLI {
    static func main() async throws {
        try await _run()
    }

    nonisolated static func _run() async throws {
        let args = CommandLine.arguments
        let sourceLang = flagValue(args: args, flag: "--from") ?? "en"
        let targetLang = flagValue(args: args, flag: "--to") ?? "ja"

        let source = Locale.Language(identifier: sourceLang)
        let target = Locale.Language(identifier: targetLang)

        // stdin から全行読み取り
        var requests: [(index: Int, text: String)] = []
        var lineIndex = 0
        while let line = readLine(strippingNewline: true) {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if trimmed.isEmpty { continue }

            if let data = trimmed.data(using: .utf8),
               let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
               let text = obj["text"] as? String {
                requests.append((index: lineIndex, text: text))
            } else {
                // JSON でなければそのままテキストとして扱う
                requests.append((index: lineIndex, text: trimmed))
            }
            lineIndex += 1
        }

        if requests.isEmpty {
            exit(0)
        }

        // セッション作成
        let session = TranslationSession(
            installedSource: source,
            target: target
        )

        // バッチ翻訳
        let batchSize = 100
        var results: [(index: Int, translated: String)] = []

        for batchStart in stride(from: 0, to: requests.count, by: batchSize) {
            let batchEnd = min(batchStart + batchSize, requests.count)
            let batch = Array(requests[batchStart..<batchEnd])

            let translationRequests = batch.map {
                TranslationSession.Request(sourceText: $0.text, clientIdentifier: "\($0.index)")
            }

            do {
                let responses = try await session.translations(from: translationRequests)
                for response in responses {
                    if let idx = Int(response.clientIdentifier ?? "") {
                        results.append((index: idx, translated: response.targetText))
                    }
                }
            } catch {
                // バッチ失敗時は1件ずつフォールバック
                FileHandle.standardError.write(
                    Data("Warning: batch failed (\(error)), falling back to single\n".utf8)
                )
                for req in batch {
                    do {
                        let singleReq = [TranslationSession.Request(
                            sourceText: req.text,
                            clientIdentifier: "\(req.index)"
                        )]
                        let resp = try await session.translations(from: singleReq)
                        if let r = resp.first {
                            results.append((index: req.index, translated: r.targetText))
                        }
                    } catch {
                        FileHandle.standardError.write(
                            Data("Error translating line \(req.index): \(error)\n".utf8)
                        )
                        // 失敗時は原文を返す
                        results.append((index: req.index, translated: req.text))
                    }
                }
            }
        }

        // index 順にソートして出力
        results.sort { $0.index < $1.index }

        let encoder = JSONEncoder()
        encoder.outputFormatting = []
        for r in results {
            let obj: [String: String] = ["text": r.translated]
            if let data = try? encoder.encode(obj),
               let jsonStr = String(data: data, encoding: .utf8) {
                print(jsonStr)
            }
        }
    }

    static func flagValue(args: [String], flag: String) -> String? {
        guard let idx = args.firstIndex(of: flag), idx + 1 < args.count else {
            return nil
        }
        return args[idx + 1]
    }
}
