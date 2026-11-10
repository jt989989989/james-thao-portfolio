// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ExpenseTracker",
    products: [
        .executable(name: "expense-tracker", targets: ["ExpenseTrackerCLI"]),
        .library(name: "ExpenseTrackerLib", targets: ["ExpenseTrackerLib"]),
    ],
    targets: [
        .target(name: "ExpenseTrackerLib", path: "Sources/ExpenseTrackerLib"),
        .executableTarget(
            name: "ExpenseTrackerCLI",
            dependencies: ["ExpenseTrackerLib"],
            path: "Sources/ExpenseTrackerCLI"
        ),
        .testTarget(
            name: "ExpenseTrackerTests",
            dependencies: ["ExpenseTrackerLib"],
            path: "Tests/ExpenseTrackerTests"
        ),
    ]
)
