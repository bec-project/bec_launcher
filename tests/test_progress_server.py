"""Unit tests for the launcher-side progress socket server."""

from __future__ import annotations

import json
import socket
import time

from PySide6.QtCore import QCoreApplication

from bec_launcher.gui.progress_server import ProgressServer


def _app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _spin(app: QCoreApplication, predicate, timeout: float = 3.0) -> bool:
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


def test_roundtrip_hello_stage_ready():
    app = _app()
    server = ProgressServer()
    hello, stages, ready = [], [], []
    server.helloReceived.connect(lambda a, p: hello.append((a, p)))
    server.stageReceived.connect(lambda n, d, t: stages.append((n, d, t)))
    server.readyReceived.connect(lambda t: ready.append(t))

    path = server.start("tok-1")
    client = _connect(path)
    try:
        _send(client, {"t": "hello", "token": "tok-1", "app": "bec-app", "pid": 4321})
        _send(client, {"t": "stage", "name": "module imports", "delta_ms": 6210, "total_ms": 6210})
        _send(client, {"t": "stage", "name": "interactive", "delta_ms": 60, "total_ms": 27710})
        _send(client, {"t": "ready", "total_ms": 27710})

        assert _spin(app, lambda: ready), "ready edge not received"
        assert hello == [("bec-app", 4321)]
        assert [s[0] for s in stages] == ["module imports", "interactive"]
        assert stages[0][2] == 6210.0
        assert ready == [27710.0]
        assert server.got_ready is True
    finally:
        client.close()
        server.stop()


def test_rejects_wrong_token():
    app = _app()
    server = ProgressServer()
    hello, stages = [], []
    server.helloReceived.connect(lambda a, p: hello.append((a, p)))
    server.stageReceived.connect(lambda n, d, t: stages.append((n, d, t)))

    path = server.start("right-token")
    client = _connect(path)
    try:
        _send(client, {"t": "hello", "token": "WRONG", "app": "bec-app", "pid": 1})
        _send(client, {"t": "stage", "name": "should be ignored", "delta_ms": 1, "total_ms": 1})
        # Give the server a chance to process and reject.
        _spin(app, lambda: False, timeout=0.3)
        assert hello == []
        assert stages == []
        assert server.got_ready is False
    finally:
        client.close()
        server.stop()


def test_info_message_is_forwarded():
    app = _app()
    server = ProgressServer()
    infos = []
    server.infoReceived.connect(lambda d: infos.append(d))

    path = server.start("tok-3")
    client = _connect(path)
    try:
        _send(client, {"t": "hello", "token": "tok-3", "app": "bec-app", "pid": 3})
        _send(client, {"t": "info", "cold_start": True, "bytecode_cached_pct": 7})
        assert _spin(app, lambda: infos)
        assert infos[0]["cold_start"] is True
        assert infos[0]["bytecode_cached_pct"] == 7
    finally:
        client.close()
        server.stop()


def test_ready_without_total_emits_sentinel():
    app = _app()
    server = ProgressServer()
    ready = []
    server.readyReceived.connect(lambda t: ready.append(t))

    path = server.start("tok-2")
    client = _connect(path)
    try:
        _send(client, {"t": "hello", "token": "tok-2", "app": "bec-app", "pid": 2})
        _send(client, {"t": "ready"})
        assert _spin(app, lambda: ready)
        assert ready == [-1.0]
    finally:
        client.close()
        server.stop()
