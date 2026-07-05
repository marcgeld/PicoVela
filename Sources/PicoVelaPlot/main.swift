#if os(macOS)
import AppKit
import SwiftUI

@MainActor
func main() {
    do {
        let command = try PlotCommand.parse()
        let document = try PlotDataBuilder(command: command).build()

        let app = NSApplication.shared
        app.setActivationPolicy(.regular)
        app.mainMenu = makeMainMenu()

        let hostingView = NSHostingView(rootView: PlotView(document: document))
        let window = NSWindow(
            contentRect: NSRect(x: 0, y: 0, width: 1100, height: 780),
            styleMask: [.titled, .closable, .miniaturizable, .resizable],
            backing: .buffered,
            defer: false
        )
        window.title = "PicoVela - \(document.displayTitle)"
        window.center()
        window.contentView = hostingView
        window.makeKeyAndOrderFront(nil)

        app.activate(ignoringOtherApps: true)
        app.run()
    } catch PlotCommandError.helpRequested {
        print(PlotCommand.help)
    } catch {
        fputs("picovela-plot: \(error)\n", stderr)
        exit(1)
    }
}

main()

private func makeMainMenu() -> NSMenu {
    let mainMenu = NSMenu()
    let appMenuItem = NSMenuItem()
    let appMenu = NSMenu()
    let quitItem = NSMenuItem(
        title: "Quit PicoVela Plot",
        action: #selector(NSApplication.terminate(_:)),
        keyEquivalent: "q"
    )

    appMenu.addItem(quitItem)
    appMenuItem.submenu = appMenu
    mainMenu.addItem(appMenuItem)
    return mainMenu
}
#else
print("picovela-plot is available on macOS only.")
#endif
