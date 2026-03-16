/// Apple Translation API を使った CLI 翻訳ツール。
///
/// 使い方:
///   echo "Hello" | apple-translate --from en --to ja
///   apple-translate --list-languages

import Foundation
import Translation

@main
struct AppleTranslateCLI {
    static func main() async throws {
        try await _run()
    }

    nonisolated static func _run() async throws {
        let args = CommandLine.arguments

        // --help
        if args.contains("--help") || args.contains("-h") {
            printUsage()
            return
        }

        // --version
        if args.contains("--version") || args.contains("-v") {
            print("apple-translate 1.0.0")
            return
        }

        // --list-languages
        if args.contains("--list-languages") || args.contains("-l") {
            try await listLanguages()
            return
        }

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
            requests.append((index: lineIndex, text: trimmed))
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
                        results.append((index: req.index, translated: req.text))
                    }
                }
            }
        }

        // index 順にソートして出力
        results.sort { $0.index < $1.index }

        for r in results {
            print(r.translated)
        }
    }

    // MARK: - サブコマンド

    nonisolated static func listLanguages() async throws {
        let availability = LanguageAvailability()
        let languages = await availability.supportedLanguages

        let englishLocale = Locale(identifier: "en")
        let sorted = languages
            .map { lang -> (code: String, name: String) in
                let code = lang.maximalIdentifier
                let name = englishLocale.localizedString(forIdentifier: code) ?? code
                return (code: code, name: name)
            }
            .sorted { $0.code < $1.code }

        let maxCodeLen = sorted.map(\.code.count).max() ?? 5
        for lang in sorted {
            let padded = lang.code.padding(toLength: maxCodeLen + 2, withPad: " ", startingAt: 0)
            print("\(padded)\(lang.name)")
        }
    }

    // MARK: - ヘルパー

    static func printUsage() {
        let usage = """
        Usage: apple-translate [OPTIONS]

        A CLI translation tool powered by Apple Translation API.
        Reads text from stdin and writes translated text to stdout.
        All translations are performed on-device.

        Options:
          --from <LANG>        Source language code (default: en)
          --to <LANG>          Target language code (default: ja)
          --list-languages, -l List available languages
          --version, -v        Show version
          --help, -h           Show this help

        Examples:
          echo "Hello, world!" | apple-translate
          echo "こんにちは" | apple-translate --from ja --to en
          apple-translate --list-languages
        """
        print(usage)
    }

    static func flagValue(args: [String], flag: String) -> String? {
        guard let idx = args.firstIndex(of: flag), idx + 1 < args.count else {
            return nil
        }
        return args[idx + 1]
    }
}
