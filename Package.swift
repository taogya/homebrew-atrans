// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "AppleTranslateCLI",
    platforms: [.macOS(.v26)],
    targets: [
        .executableTarget(
            name: "apple-translate",
            path: "Sources"
        ),
    ],
    swiftLanguageModes: [.v6]
)
