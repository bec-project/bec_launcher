import argparse
import os
import sys

from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from bec_launcher.gui.backend import Backend

# Set Qt Quick Controls style to Basic (supports customization)
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="BEC Launcher - Launch BEC deployments", prog="bec-launcher"
    )
    parser.add_argument(
        "--fresh",
        "--reset",
        action="store_true",
        dest="fresh_start",
        help="Start fresh, ignoring saved preferences (deployment and action)",
    )
    parser.add_argument(
        "--base-path",
        type=str,
        default=None,
        help="Base path for deployments, typically /sls/<beamline>/config/bec",
    )
    return parser.parse_args()


def main() -> int:
    # Parse arguments before creating QGuiApplication
    args = parse_args()

    # Useful diagnostics during development (uncomment if needed)
    # os.environ["QML_IMPORT_TRACE"] = "1"
    # os.environ["QML_DISABLE_DISK_CACHE"] = "1"

    app = QGuiApplication(sys.argv)

    # Backend injection with fresh_start option
    backend = Backend(base_path=args.base_path, fresh_start=args.fresh_start)

    # Connect quitApplication signal to app.quit
    backend.quitApplication.connect(app.quit)

    # Check if we should auto-launch without showing UI
    if backend.shouldAutoLaunch:
        print(f"[Main] Auto-launching {backend.autoLaunchAction} without UI")

        # Use QTimer to launch after event loop starts
        def do_auto_launch():
            if backend.autoLaunchAction == "terminal":
                backend.launchTerminal()
            elif backend.autoLaunchAction == "gui":
                backend.launchGui()

        QTimer.singleShot(0, do_auto_launch)
        return app.exec()

    # Normal flow - show UI
    engine = QQmlApplicationEngine()

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # This directory must be the parent directory that contains the QML module folder "Launcher"
    qml_root = os.path.join(base_dir, "qml")
    engine.addImportPath(qml_root)

    # Add the Launcher project folder so that "import Launcher" finds qml/Launcher/Launcher/qmldir
    qml_launcher_dir = os.path.join(qml_root, "Launcher")
    engine.addImportPath(qml_launcher_dir)

    qml_content_dir = os.path.join(qml_root, "Launcher", "LauncherContent")
    engine.addImportPath(qml_content_dir)

    engine.rootContext().setContextProperty("backend", backend)

    app_qml = os.path.join(qml_root, "Launcher", "LauncherContent", "App.qml")
    engine.load(QUrl.fromLocalFile(app_qml))

    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
