from __future__ import annotations

import argparse
import os
import sys

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

# Representative bec-app startup timeline (name, per-stage ms) for the preview.
DEMO_STAGES = [
    ("module imports", 6210),
    ("QApplication", 340),
    ("theme applied", 90),
    ("BEC connection + base window", 18400),
    ("DockAreaView", 2100),
    ("DeviceManagerView", 640),
    ("AdminView", 220),
    ("views added", 30),
    ("guided tour", 60),
    ("main window built", 40),
    ("window shown", 20),
    ("interactive", 60),
]


class DemoLaunchState(QObject):
    """Simulates the streaming handshake so the banner can be previewed offline.

    It streams the stages above, then briefly demonstrates the stalled and error
    states before looping, so ``--demo`` exercises every visual state.
    """

    changed = Signal()

    def __init__(self):
        super().__init__()
        self._elapsed = 0
        self._stages: list[dict] = []
        self._index = 0
        self._post = 0
        self._has_error = False
        self._is_stalled = False
        self._status = "Starting GUI..."

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(1000)
        self._elapsed_timer.timeout.connect(self._tick_elapsed)
        self._elapsed_timer.start()

        self._stage_timer = QTimer(self)
        self._stage_timer.setInterval(1100)
        self._stage_timer.timeout.connect(self._tick_stage)
        self._stage_timer.start()

    def _tick_elapsed(self) -> None:
        self._elapsed += 1
        self.changed.emit()

    def _tick_stage(self) -> None:
        if self._index < len(DEMO_STAGES):
            name, ms = DEMO_STAGES[self._index]
            self._stages = self._stages + [{"name": name, "ms": ms, "total_ms": 0}]
            self._status = name
            self._index += 1
        else:
            self._post += 1
            if self._post == 2:
                self._is_stalled = True
                self._status = "Still starting — this can take a while on a cold cache."
            elif self._post == 5:
                self._is_stalled = False
                self._has_error = True
                self._status = "The GUI process exited before it finished starting."
            elif self._post >= 8:
                self._stages = []
                self._index = 0
                self._post = 0
                self._elapsed = 0
                self._has_error = False
                self._is_stalled = False
                self._status = "Starting GUI..."
        self.changed.emit()

    @Property(str, notify=changed)
    def deploymentName(self) -> str:
        return "demo"

    @Property(str, notify=changed)
    def launchMode(self) -> str:
        return "BEC App"

    @Property(str, notify=changed)
    def statusText(self) -> str:
        return self._status

    @Property(int, notify=changed)
    def elapsedSeconds(self) -> int:
        return self._elapsed

    @Property(bool, notify=changed)
    def hasError(self) -> bool:
        return self._has_error

    @Property(list, notify=changed)
    def stages(self) -> list:
        return self._stages

    @Property(int, notify=changed)
    def stageCount(self) -> int:
        return len(self._stages)

    @Property(int, notify=changed)
    def expectedStages(self) -> int:
        return 9

    @Property(str, notify=changed)
    def currentStage(self) -> str:
        return self._stages[-1]["name"] if self._stages else ""

    @Property(bool, notify=changed)
    def isStalled(self) -> bool:
        return self._is_stalled

    @Property(bool, notify=changed)
    def coldStart(self) -> bool:
        # Demo the first-launch hint during the initial import-heavy stages.
        return self._index < 5 and not self._has_error


def main() -> int:
    # Running the module IS the preview; argparse only provides --help.
    parser = argparse.ArgumentParser(
        description="Preview the BEC launcher loading banner with a simulated launch timeline."
    )
    parser.parse_args()

    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    state = DemoLaunchState()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    qml_root = os.path.join(base_dir, "qml")
    engine.addImportPath(qml_root)
    engine.addImportPath(os.path.join(qml_root, "Launcher"))
    engine.addImportPath(os.path.join(qml_root, "Launcher", "LauncherContent"))
    engine.rootContext().setContextProperty("demoState", state)

    qml_file = os.path.join(qml_root, "Launcher", "LauncherContent", "LaunchBannerPreview.qml")
    engine.load(QUrl.fromLocalFile(qml_file))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
