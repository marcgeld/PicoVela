// swift-tools-version: 6.2

import PackageDescription

let package = Package(
    name: "PicoVela",
    platforms: [
        .macOS(.v14),
        .iOS(.v17),
        .tvOS(.v17),
        .watchOS(.v10),
        .visionOS(.v1),
    ],
    products: [
        .library(
            name: "PicoVela",
            targets: ["PicoVela"]
        ),
        .executable(
            name: "picovela-plot",
            targets: ["PicoVelaPlot"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/marcgeld/SwiftNumerica.git", branch: "main"),
    ],
    targets: [
        .target(
            name: "PicoVela",
            dependencies: [
                .product(name: "SwiftNumerica", package: "SwiftNumerica"),
            ]
        ),
        .executableTarget(
            name: "PicoVelaPlot",
            dependencies: ["PicoVela"]
        ),
        .testTarget(
            name: "PicoVelaTests",
            dependencies: ["PicoVela"]
        ),
    ],
    swiftLanguageModes: [.v6]
)
