from __future__ import annotations

import os

SOFTWARE_SCENE_GRAPH_BACKEND = "software"
QT_QML_RUNTIME_ENVIRONMENT = {"QV4_FORCE_INTERPRETER": "1"}


def configure_qt_environment() -> None:
    """Configure Qt process environment before creating Qt application objects."""
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    for key, value in QT_QML_RUNTIME_ENVIRONMENT.items():
        os.environ.setdefault(key, value)


def qt_qml_runtime_environment() -> dict[str, str]:
    """Return Qt QML runtime variables for child GUI processes."""
    return dict(QT_QML_RUNTIME_ENVIRONMENT)


def configure_qt_quick_renderer(qquick_window_type) -> None:
    """Configure Qt Quick rendering before creating QGuiApplication."""
    qquick_window_type.setSceneGraphBackend(SOFTWARE_SCENE_GRAPH_BACKEND)
