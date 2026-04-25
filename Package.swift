// swift-tools-version: 6.2
import PackageDescription

let package = Package(
    name: "atrans",
    platforms: [.macOS(.v26)],
    targets: [
        .executableTarget(
            name: "atrans",
            path: "Sources"
        ),
    ],
    swiftLanguageModes: [.v6]
)
