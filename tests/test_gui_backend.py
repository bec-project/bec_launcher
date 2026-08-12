from __future__ import annotations

import json
import socket
import time

from PySide6.QtCore import QCoreApplication

from bec_launcher.gui import backend as backend_module


def _spin(app, predicate, timeout: float = 3.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    app.processEvents()
    return predicate()


def _connect(path: str) -> socket.socket:
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.settimeout(2.0)
    client.connect(path)
    return client


def _send(client: socket.socket, obj: dict) -> None:
    client.sendall((json.dumps(obj) + "\n").encode())


class FakeSettings:
    def __init__(self, initial: dict[str, object] | None = None) -> None:
        self._values = dict(initial or {})

    def value(self, key: str, default: object = None, type=None):  # noqa: A002
        value = self._values.get(key, default)
        if type is bool:
            return bool(value)
        if type is str:
            return "" if value is None else str(value)
        return value

    def setValue(self, key: str, value: object) -> None:
        self._values[key] = value

    def remove(self, key: str) -> None:
        self._values.pop(key, None)

    def contains(self, key: str) -> bool:
        return key in self._values


def test_single_deployment_with_default_action_auto_launches(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    assert app is not None

    fake_settings = FakeSettings({backend_module.SETTINGS_DEFAULT_ACTION: "dock"})

    monkeypatch.setattr(backend_module, "QSettings", lambda *args, **kwargs: fake_settings)
    monkeypatch.setattr(
        backend_module,
        "get_available_deployments",
        lambda base_path: {"production": ["beamline"], "test": []},
    )

    backend = backend_module.Backend(base_path="/tmp/bec", fresh_start=False)

    assert backend.selectedIndex == 0
    assert backend.deploymentConfirmed is True
    assert backend.defaultDeployment == "beamline"
    assert backend.defaultAction == "dock"
    assert backend.shouldAutoLaunch is True
    assert backend.autoLaunchAction == "dock"


def _make_launch_backend(monkeypatch, launched, pycache_prefix="", handshake_support=True):
    fake_settings = FakeSettings()
    monkeypatch.setattr(backend_module, "QSettings", lambda *args, **kwargs: fake_settings)
    monkeypatch.setattr(
        backend_module,
        "get_available_deployments",
        lambda base_path: {"production": ["beamline"], "test": []},
    )
    monkeypatch.setattr(
        backend_module, "launch_deployment", lambda *args, **kwargs: launched.append((args, kwargs))
    )
    # Deployments are probed for handshake support; unit tests pin the answer.
    monkeypatch.setattr(
        backend_module, "deployment_supports_handshake", lambda path, **kw: handshake_support
    )
    return backend_module.Backend(
        base_path="/tmp/bec", fresh_start=True, pycache_prefix=pycache_prefix
    )


def test_gui_launch_opens_progress_channel_and_finishes_on_ready(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    assert app is not None

    launched = []
    quit_emitted = []
    backend = _make_launch_backend(monkeypatch, launched)
    backend.quitApplication.connect(lambda: quit_emitted.append(True))

    backend.selectDeployment(0)
    backend.launchApp()

    assert backend.launchInProgress is True
    assert launched
    env = launched[0][1]["extra_env"]
    socket_path = env[backend_module.PROGRESS_SOCKET_ENV]
    assert socket_path
    assert env[backend_module.PROGRESS_TOKEN_ENV]
    assert env[backend_module.PROGRESS_APP_ENV] == "BEC App"

    token = env[backend_module.PROGRESS_TOKEN_ENV]
    client = _connect(socket_path)
    try:
        _send(client, {"t": "hello", "token": token, "app": "bec-app", "pid": 999})
        _send(client, {"t": "stage", "name": "module imports", "delta_ms": 100, "total_ms": 100})
        assert _spin(app, lambda: backend.launchStageCount >= 1)
        assert backend.launchCurrentStage == "module imports"
        assert backend.launchStages[0]["name"] == "module imports"

        _send(client, {"t": "ready", "total_ms": 27710})
        assert _spin(app, lambda: quit_emitted)
        assert backend.launchInProgress is False
        assert backend.launchStatus == "GUI ready"
    finally:
        client.close()


def test_gui_launch_reports_error_when_child_disconnects_before_ready(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    launched = []
    backend = _make_launch_backend(monkeypatch, launched)

    backend.selectDeployment(0)
    backend.launchApp()
    env = launched[0][1]["extra_env"]
    token = env[backend_module.PROGRESS_TOKEN_ENV]

    client = _connect(env[backend_module.PROGRESS_SOCKET_ENV])
    _send(client, {"t": "hello", "token": token, "app": "bec-app", "pid": 999})
    assert _spin(app, lambda: backend.launchStatus == "Loading Python modules...")
    # Child dies before sending ready.
    client.close()

    assert _spin(app, lambda: backend.launchHasError)
    assert backend.launchInProgress is False
    assert "exited" in backend.launchStatus


def test_stray_wrong_token_connection_does_not_abort_launch(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    launched = []
    backend = _make_launch_backend(monkeypatch, launched)
    quit_emitted = []
    backend.quitApplication.connect(lambda: quit_emitted.append(True))

    backend.selectDeployment(0)
    backend.launchApp()
    env = launched[0][1]["extra_env"]
    socket_path = env[backend_module.PROGRESS_SOCKET_ENV]
    token = env[backend_module.PROGRESS_TOKEN_ENV]

    # A stray/probe connection with the wrong token connects first, then drops.
    stray = _connect(socket_path)
    _send(stray, {"t": "hello", "token": "WRONG", "pid": 1})
    _spin(app, lambda: False, timeout=0.3)
    stray.close()
    _spin(app, lambda: False, timeout=0.3)

    # The rejected connection must NOT have tripped the crash-before-ready error.
    assert backend.launchHasError is False
    assert backend.launchInProgress is True

    # The real child can still connect afterwards and complete the launch.
    real = _connect(socket_path)
    try:
        _send(real, {"t": "hello", "token": token, "app": "bec-app", "pid": 999})
        _send(real, {"t": "ready", "total_ms": 100})
        assert _spin(app, lambda: quit_emitted)
        assert backend.launchStatus == "GUI ready"
    finally:
        real.close()


def test_ready_with_trailing_data_finalizes_cleanly(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    launched = []
    backend = _make_launch_backend(monkeypatch, launched)
    quit_emitted = []
    backend.quitApplication.connect(lambda: quit_emitted.append(True))

    backend.selectDeployment(0)
    backend.launchApp()
    env = launched[0][1]["extra_env"]
    token = env[backend_module.PROGRESS_TOKEN_ENV]

    client = _connect(env[backend_module.PROGRESS_SOCKET_ENV])
    try:
        _send(client, {"t": "hello", "token": token, "app": "bec-app", "pid": 999})
        # ready plus a trailing message in one frame: finalize()/stop() runs mid-parse,
        # the buffered trailing line must not crash or be mis-handled.
        blob = (
            json.dumps({"t": "ready", "total_ms": 100})
            + "\n"
            + json.dumps({"t": "stage", "name": "late", "delta_ms": 1, "total_ms": 1})
            + "\n"
        )
        client.sendall(blob.encode())
        assert _spin(app, lambda: quit_emitted)
        assert backend.launchHasError is False
        assert backend.launchStatus == "GUI ready"
    finally:
        client.close()


def test_pycache_prefix_is_injected_into_all_launch_actions(monkeypatch, tmp_path):
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    prefix = str(tmp_path / "pycache")
    backend = _make_launch_backend(monkeypatch, launched, pycache_prefix=prefix)

    # The prefix directory is created eagerly so the first launch can use it.
    import os

    assert os.path.isdir(prefix)

    backend.selectDeployment(0)
    backend.launchTerminal()
    env = launched[0][1]["extra_env"]
    assert env == {"PYTHONPYCACHEPREFIX": prefix}

    backend.launchApp()
    env = launched[1][1]["extra_env"]
    assert env["PYTHONPYCACHEPREFIX"] == prefix
    assert backend_module.PROGRESS_SOCKET_ENV in env  # progress vars still present


def test_no_pycache_prefix_keeps_terminal_env_untouched(monkeypatch):
    """Off Linux an unset prefix injects nothing; Linux has its own default (below)."""
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    from unittest import mock

    monkeypatch.setattr("os.uname", lambda: mock.Mock(sysname="Darwin"))
    backend = _make_launch_backend(monkeypatch, launched)

    backend.selectDeployment(0)
    backend.launchTerminal()
    assert launched[0][1]["extra_env"] is None


def test_linux_defaults_pycache_prefix_to_user_cache(monkeypatch, tmp_path):
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    from unittest import mock

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr("os.uname", lambda: mock.Mock(sysname="Linux"))
    backend = _make_launch_backend(monkeypatch, launched)

    backend.selectDeployment(0)
    backend.launchTerminal()
    env = launched[0][1]["extra_env"]
    assert env["PYTHONPYCACHEPREFIX"] == str(tmp_path / ".cache" / "bec-pycache")

    import os

    assert os.path.isdir(env["PYTHONPYCACHEPREFIX"])


def test_legacy_deployment_launches_without_banner_and_quits(monkeypatch):
    """A deployment without handshake support behaves exactly as before the feature."""
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    quit_emitted = []
    backend = _make_launch_backend(monkeypatch, launched, handshake_support=False)
    backend.quitApplication.connect(lambda: quit_emitted.append(True))

    backend.selectDeployment(0)
    backend.launchApp()

    # No banner, no progress socket, launcher quits right after spawning.
    assert backend.launchInProgress is False
    assert backend.launchHasError is False
    assert quit_emitted == [True]
    env = launched[0][1]["extra_env"]
    assert env is None or backend_module.PROGRESS_SOCKET_ENV not in env


def test_handshake_probe_result_is_cached_per_deployment(monkeypatch):
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    calls = []
    backend = _make_launch_backend(monkeypatch, launched)
    monkeypatch.setattr(
        backend_module,
        "deployment_supports_handshake",
        lambda path, **kw: (calls.append(path), False)[1],
    )

    backend.selectDeployment(0)
    backend.launchApp()
    backend.launchApp()

    assert len(calls) == 1  # probed once, reused afterwards


def test_missing_hello_falls_back_to_legacy_behaviour(monkeypatch):
    """Probe said yes but nothing connects: recover instead of hanging forever."""
    app = QCoreApplication.instance() or QCoreApplication([])
    launched = []
    quit_emitted = []
    backend = _make_launch_backend(monkeypatch, launched)
    backend.quitApplication.connect(lambda: quit_emitted.append(True))

    backend.selectDeployment(0)
    backend.launchApp()
    assert backend.launchInProgress is True  # banner shown optimistically

    # Pretend the hello window elapsed without any client connecting.
    backend._launch_started_at -= backend_module.HELLO_TIMEOUT_S + 1
    backend._update_waiting_state()
    app.processEvents()

    assert quit_emitted == [True]
    assert backend.launchInProgress is False
    assert backend.launchHasError is False  # not an error - the GUI is starting fine
    # The deployment is remembered as unsupported for the rest of the session.
    assert backend._handshake_support["beamline"] is False


def test_hello_prevents_the_legacy_fallback(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    launched = []
    quit_emitted = []
    backend = _make_launch_backend(monkeypatch, launched)
    backend.quitApplication.connect(lambda: quit_emitted.append(True))

    backend.selectDeployment(0)
    backend.launchApp()
    env = launched[0][1]["extra_env"]
    token = env[backend_module.PROGRESS_TOKEN_ENV]

    client = _connect(env[backend_module.PROGRESS_SOCKET_ENV])
    try:
        _send(client, {"t": "hello", "token": token, "app": "bec-app", "pid": 999})
        assert _spin(app, lambda: backend._launch_saw_hello)

        # Even well past the hello window, a connected child keeps the banner alive.
        backend._launch_started_at -= backend_module.HELLO_TIMEOUT_S + 1
        backend._update_waiting_state()
        assert quit_emitted == []
        assert backend.launchInProgress is True
    finally:
        client.close()


def test_cold_start_info_sets_flag_and_status(monkeypatch):
    app = QCoreApplication.instance() or QCoreApplication([])
    launched = []
    backend = _make_launch_backend(monkeypatch, launched)

    backend.selectDeployment(0)
    backend.launchApp()
    env = launched[0][1]["extra_env"]
    token = env[backend_module.PROGRESS_TOKEN_ENV]

    client = _connect(env[backend_module.PROGRESS_SOCKET_ENV])
    try:
        _send(client, {"t": "hello", "token": token, "app": "bec-app", "pid": 999})
        _send(client, {"t": "info", "cold_start": True, "bytecode_cached_pct": 3})
        assert _spin(app, lambda: backend.launchIsColdStart)
        assert "First launch" in backend.launchStatus

        # A later stage overrides the status but the cold flag persists.
        _send(client, {"t": "stage", "name": "module imports", "delta_ms": 5, "total_ms": 5})
        assert _spin(app, lambda: backend.launchStageCount >= 1)
        assert backend.launchIsColdStart is True
    finally:
        client.close()


def test_child_process_early_exit_sets_error(monkeypatch):
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    backend = _make_launch_backend(monkeypatch, launched)
    backend.selectDeployment(0)
    backend.launchApp()

    class _DeadProc:
        def poll(self):
            return 1  # already exited

    backend._launch_child_proc = _DeadProc()
    backend._check_child_liveness()

    assert backend.launchHasError is True
    assert "exited" in backend.launchStatus


def test_dismiss_launch_error_returns_to_picker(monkeypatch):
    QCoreApplication.instance() or QCoreApplication([])
    launched = []
    backend = _make_launch_backend(monkeypatch, launched)
    backend.selectDeployment(0)
    backend.launchApp()
    backend._set_launch_error("boom")
    assert backend.launchHasError is True

    backend.dismissLaunchError()
    assert backend.launchHasError is False
    assert backend.launchInProgress is False
    assert backend.launchStages == []
    assert backend.launchStatus == ""
