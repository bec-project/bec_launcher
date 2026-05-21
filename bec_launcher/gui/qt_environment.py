from __future__ import annotations

import os

SOFTWARE_SCENE_GRAPH_BACKEND = "software"


def configure_qt_environment() -> None:
    """Configure Qt process environment before creating Qt application objects."""
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    os.environ.setdefault("QV4_FORCE_INTERPRETER", "1")


def configure_qt_quick_renderer(qquick_window_type) -> None:
    """Configure Qt Quick rendering before creating QGuiApplication."""
    qquick_window_type.setSceneGraphBackend(SOFTWARE_SCENE_GRAPH_BACKEND)
