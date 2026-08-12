"""Server side of the BEC launch-progress handshake.

The launcher opens a per-launch AF_UNIX socket (via Qt's :class:`QLocalServer`,
which integrates with the event loop) and hands its path plus a one-shot token
to the launched GUI process through the environment. The child streams startup
stages and a final ``ready`` edge back over that socket, letting the launcher
render a live loading banner and detect a crash (socket closed before ``ready``).

Message framing: one JSON object per line (``\\n``-terminated, utf-8). The first
line must be ``{"t":"hello","token":<token>,...}``; connections presenting the
wrong token are dropped.
"""

from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class ProgressServer(QObject):
    """Accepts a single launch-progress client and re-emits its messages as signals."""

    helloReceived = Signal(str, int)  # app, pid
    stageReceived = Signal(str, float, float)  # name, delta_ms, total_ms
    infoReceived = Signal(dict)  # informational payload (e.g. cold-start status)
    readyReceived = Signal(float)  # total_ms (-1.0 when the child omitted it)
    errorReceived = Signal(str)  # explicit error message from the child
    clientDisconnected = Signal()  # the child closed the socket

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._server: QLocalServer | None = None
        self._conn: QLocalSocket | None = None
        self._token = ""
        self._authed = False
        self._ready_seen = False
        self._buffer = bytearray()

    @property
    def got_ready(self) -> bool:
        return self._authed and self._ready_seen

    def start(self, token: str) -> str:
        """Open the socket for ``token`` and return its filesystem path.

        ``token`` is the full auth secret echoed by the child in ``hello``; only a
        short prefix is used for the socket *name* so the resulting AF_UNIX path
        stays well under the platform limit (~104 chars on macOS).
        """
        self.stop()
        self._token = token
        self._authed = False
        self._ready_seen = False
        self._buffer = bytearray()

        name = f"bec-launch-{token[:12]}"
        QLocalServer.removeServer(name)
        self._server = QLocalServer(self)
        # Restrict the socket to the current user (0600) — no other user may connect.
        self._server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        if not self._server.listen(name):
            QLocalServer.removeServer(name)
            if not self._server.listen(name):
                error = self._server.errorString()
                self._server = None
                raise RuntimeError(f"Could not open launch progress socket: {error}")
        self._server.newConnection.connect(self._on_new_connection)
        return self._server.fullServerName()

    def stop(self) -> None:
        if self._conn is not None:
            try:
                self._conn.disconnected.disconnect(self._on_disconnected)
            except (RuntimeError, TypeError):
                pass
            self._conn.close()
            self._conn.deleteLater()
            self._conn = None
        if self._server is not None:
            self._server.close()
            self._server.deleteLater()
            self._server = None

    # -- internals ----------------------------------------------------------
    def _on_new_connection(self) -> None:
        if self._server is None:
            return
        conn = self._server.nextPendingConnection()
        if conn is None:
            return
        if self._conn is not None:
            # Only one launch client is expected; reject any extra connections.
            conn.close()
            conn.deleteLater()
            return
        self._conn = conn
        conn.readyRead.connect(self._on_ready_read)
        conn.disconnected.connect(self._on_disconnected)
        # Data may already be buffered if the client wrote immediately after
        # connecting (readyRead fired before we attached the slot) — drain it now.
        if conn.bytesAvailable() > 0:
            self._on_ready_read()

    def _on_ready_read(self) -> None:
        if self._conn is None:
            return
        self._buffer += bytes(self._conn.readAll().data())
        while b"\n" in self._buffer:
            line, _, rest = self._buffer.partition(b"\n")
            self._buffer = bytearray(rest)
            self._handle_line(line)
            # A handler (e.g. ready -> finalize -> stop, or a rejected auth) may tear
            # the connection down re-entrantly; stop parsing buffered lines if so.
            if self._conn is None:
                break

    def _handle_line(self, raw: bytes) -> None:
        text = raw.decode("utf-8", "replace").strip()
        if not text:
            return
        try:
            msg = json.loads(text)
        except ValueError:
            return
        if not isinstance(msg, dict):
            return

        kind = msg.get("t")
        if not self._authed:
            # The very first valid message must authenticate with the token.
            if kind != "hello" or msg.get("token") != self._token:
                self._reject()
                return
            self._authed = True
            self.helloReceived.emit(str(msg.get("app", "")), int(msg.get("pid", 0) or 0))
            return

        if kind == "stage":
            self.stageReceived.emit(
                str(msg.get("name", "")),
                float(msg.get("delta_ms", 0.0) or 0.0),
                float(msg.get("total_ms", 0.0) or 0.0),
            )
        elif kind == "info":
            self.infoReceived.emit(dict(msg))
        elif kind == "ready":
            self._ready_seen = True
            total = msg.get("total_ms")
            self.readyReceived.emit(float(total) if total is not None else -1.0)
        elif kind == "error":
            self.errorReceived.emit(str(msg.get("msg", "")))

    def _reject(self) -> None:
        if self._conn is not None:
            # Mirror stop(): drop the disconnected wiring first, so closing a bad/
            # unauthenticated connection does not emit clientDisconnected and get
            # misread by the backend as the real GUI child crashing before ready.
            try:
                self._conn.disconnected.disconnect(self._on_disconnected)
            except (RuntimeError, TypeError):
                pass
            self._conn.close()
            self._conn.deleteLater()
            self._conn = None
        self._buffer = bytearray()

    def _on_disconnected(self) -> None:
        self.clientDisconnected.emit()
