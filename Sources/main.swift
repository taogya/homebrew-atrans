/// Apple Translation API を使った CLI 翻訳ツール。
///
/// 使い方:
///   echo "Hello" | atrans --from en --to ja
///   atrans 'Hello, world!' --from en --to ja
///   atrans --text 'Hello' --from en --to ja
///   atrans --file input.txt --from en --to ja
///   atrans --list-languages

import Foundation
import Translation

@main
struct AtransCLI {
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
            print("atrans 2.0.0")
            return
        }

        // --list-languages
        if args.contains("--list-languages") || args.contains("-l") {
            try await listLanguages()
            return
        }

        // --from / --to は必須
        guard let sourceLang = flagValue(args: args, flag: "--from") else {
            FileHandle.standardError.write(Data("Error: --from is required.\n".utf8))
            _exit(1)
        }
        guard let targetLang = flagValue(args: args, flag: "--to") else {
            FileHandle.standardError.write(Data("Error: --to is required.\n".utf8))
            _exit(1)
        }

        // 入力ソースの決定（複数の明示的ソースはエラー）
        let textFromFlag = flagValue(args: args, flag: "--text")
        let fileFromFlag = flagValue(args: args, flag: "--file")
        let positionalText = extractPositionalText(args: args)

        var explicitSourceCount = 0
        if textFromFlag != nil { explicitSourceCount += 1 }
        if fileFromFlag != nil { explicitSourceCount += 1 }
        if positionalText != nil { explicitSourceCount += 1 }

        if explicitSourceCount > 1 {
            FileHandle.standardError.write(
                Data("Error: Multiple input sources specified. Use only one of: positional text, --text, or --file.\n".utf8)
            )
            _exit(1)
        }

        let source = Locale.Language(identifier: sourceLang)
        let target = Locale.Language(identifier: targetLang)

        // 同一言語ペアの検出
        if source.languageCode == target.languageCode {
            FileHandle.standardError.write(
                Data("Error: Source and target are the same language (\(source.maximalIdentifier) and \(target.maximalIdentifier)).\n".utf8)
            )
            _exit(1)
        }

        // 入力テキストの取得
        var inputLines: [String]

        if let text = textFromFlag {
            inputLines = [text]
        } else if let text = positionalText {
            inputLines = [text]
        } else if let filePath = fileFromFlag {
            do {
                let content = try String(contentsOfFile: filePath, encoding: .utf8)
                let normalized = content.replacingOccurrences(of: "\r\n", with: "\n").replacingOccurrences(of: "\r", with: "\n")
                inputLines = normalized.components(separatedBy: "\n")
                if inputLines.last?.isEmpty == true { inputLines.removeLast() }
            } catch {
                FileHandle.standardError.write(
                    Data("Error: Cannot read file '\(filePath)': \(error.localizedDescription)\n".utf8)
                )
                _exit(1)
            }
        } else {
            // stdin（明示的ソースがない場合のフォールバック）
            if isatty(STDIN_FILENO) != 0 {
                FileHandle.standardError.write(Data("Error: No input. Provide text as argument, --text, --file, or pipe via stdin.\n".utf8))
                _exit(1)
            }
            let data = FileHandle.standardInput.readDataToEndOfFile()
            let content = String(data: data, encoding: .utf8) ?? ""
            let normalized = content.replacingOccurrences(of: "\r\n", with: "\n").replacingOccurrences(of: "\r", with: "\n")
            inputLines = normalized.components(separatedBy: "\n")
            if inputLines.last?.isEmpty == true { inputLines.removeLast() }
        }

        // リクエスト作成（空行は翻訳せず位置を保持）
        var requests: [(index: Int, text: String)] = []
        for (i, line) in inputLines.enumerated() {
            let trimmed = line.trimmingCharacters(in: .whitespaces)
            if !trimmed.isEmpty {
                requests.append((index: i, text: trimmed))
            }
        }

        if requests.isEmpty {
            for line in inputLines { print(line) }
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

        // index 順にソートして出力（空行を元の位置に復元）
        results.sort { $0.index < $1.index }

        var resultMap: [Int: String] = [:]
        for r in results {
            resultMap[r.index] = r.translated
        }

        for i in 0..<inputLines.count {
            if let translated = resultMap[i] {
                print(translated)
            } else {
                print(inputLines[i])
            }
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
        Usage: atrans [TEXT] --from <LANG> --to <LANG>
               echo <text> | atrans --from <LANG> --to <LANG>

        A CLI translation tool powered by Apple Translation API.
        Translates text from argument, file, or stdin.
        All translations are performed on-device.

        Input (use only one):
          TEXT                 Positional text argument
          --text <TEXT>        Text to translate
          --file <PATH>        Read text from file (one translation per line)
          <stdin>              Pipe text via stdin

        Options:
          --from <LANG>        Source language code (required)
          --to <LANG>          Target language code (required)
          --list-languages, -l List available languages
          --version, -v        Show version
          --help, -h           Show this help

        Language codes:
          Both short (ja, en, ko, zh-Hans) and full (ja-Jpan-JP, en-Latn-US) forms
          are accepted. Use --list-languages to see available languages.

        Examples:
          atrans 'Hello, world!' --from en --to ja
          atrans --text 'Hello, world!' --from en --to ja
          atrans --file input.txt --from en --to ja
          echo 'Hello, world!' | atrans --from en --to ja
          atrans --list-languages
        """
        print(usage)
    }

    static func flagValue(args: [String], flag: String) -> String? {
        guard let idx = args.firstIndex(of: flag), idx + 1 < args.count else {
            return nil
        }
        return args[idx + 1]
    }

    /// 位置引数からテキストを抽出する。
    /// フラグ（--xxx）およびそのパラメータを除いた残りの引数を位置引数とみなす。
    static func extractPositionalText(args: [String]) -> String? {
        let flagsWithValue: Set<String> = ["--from", "--to", "--text", "--file"]
        let standaloneFlags: Set<String> = ["--help", "-h", "--version", "-v", "--list-languages", "-l"]

        var positional: [String] = []
        var i = 1 // args[0] はバイナリパス
        while i < args.count {
            let arg = args[i]
            if flagsWithValue.contains(arg) {
                i += 2 // フラグ + 値をスキップ
            } else if standaloneFlags.contains(arg) {
                i += 1
            } else if arg.hasPrefix("-") {
                i += 1 // 不明なフラグはスキップ
            } else {
                positional.append(arg)
                i += 1
            }
        }
        return positional.isEmpty ? nil : positional.joined(separator: " ")
    }

}
