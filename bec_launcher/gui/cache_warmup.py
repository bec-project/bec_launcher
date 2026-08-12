"""Background Python bytecode warm-up for the available deployments.

While the user is still choosing a deployment/action, the launcher pre-compiles
each deployment venv's ``site-packages`` to bytecode so the first GUI launch does
not pay the compile cost (which dominates cold starts, especially on NFS).

Design notes:

* One deployment at a time (``nice -n 10``, quiet) — background work must never
  compete with the launcher UI or an already-running launch for I/O.
* Processes are started detached (``start_new_session``) so an in-flight compile
  survives the launcher quitting (e.g. auto-launch) and still benefits the next
  start.
* When a ``PYTHONPYCACHEPREFIX`` is configured, compilation targets that prefix —
  this also makes warm-up work for read-only deployment venvs.
* Deployments without a discoverable venv are skipped silently; failures are
  reported as skipped rather than surfaced as errors.
"""

from __future__ import annotations

import glob
import os
import subprocess

from PySide6.QtCore import QObject, QTimer, Signal

COMPILE_WORKERS = "2"
POLL_INTERVAL_MS = 500


class DeploymentCacheWarmup(QObject):
    """Sequentially pre-compiles the site-packages of deployment venvs."""

    stateChanged = Signal()

    def __init__(self, parent: QObject | None = None, pycache_prefix: str = "") -> None:
        super().__init__(parent)
        self._pycache_prefix = pycache_prefix
        self._pending: list[tuple[str, str, str]] = []  # (name, python, site_packages)
        self._proc: subprocess.Popen | None = None
        self._current_name = ""
        self._total = 0
        self._done = 0
        self._skipped: list[str] = []
        self._active = False
        self._finished = False
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._poll)

    # -- public API ----------------------------------------------------------
    @property
    def active(self) -> bool:
        return self._active

    @property
    def status_text(self) -> str:
        if self._active:
            return (
                f"Preparing Python caches — {self._current_name} "
                f"({self._done + len(self._skipped) + 1}/{self._total})"
            )
        if not self._finished or self._done == 0:
            return ""
        if self._skipped:
            return f"Python caches ready ({len(self._skipped)} skipped)"
        return "Python caches ready"

    def start(self, deployments: dict[str, str]) -> None:
        """Queue a warm-up for ``{name: path}`` deployments. Runs once per launcher."""
        if self._active or self._finished:
            return
        for name, path in deployments.items():
            python, site_packages = self._venv_compile_target(path)
            if python and site_packages:
                self._pending.append((name, python, site_packages))
            else:
                self._skipped.append(name)
        self._total = len(self._pending) + len(self._skipped)
        if not self._pending:
            # Nothing warmable — finish silently, no UI noise.
            self._finished = True
            return
        self._active = True
        self._start_next()
        self._timer.start()
        self.stateChanged.emit()

    # -- internals -----------------------------------------------------------
    @staticmethod
    def _venv_compile_target(deployment_path: str) -> tuple[str, str]:
        """Locate ``(python, site-packages)`` for a deployment, mirroring launch_deployment."""
        for env_dir in (os.path.join(deployment_path, "bec_venv"), deployment_path):
            python = os.path.join(env_dir, "bin", "python")
            if not os.path.exists(python):
                continue
            matches = sorted(glob.glob(os.path.join(env_dir, "lib", "python*", "site-packages")))
            if matches:
                return python, matches[0]
        return "", ""

    def _start_next(self) -> None:
        while self._pending:
            name, python, site_packages = self._pending.pop(0)
            self._current_name = name
            env = os.environ.copy()
            if self._pycache_prefix:
                env["PYTHONPYCACHEPREFIX"] = self._pycache_prefix
            cmd = [
                "nice",
                "-n",
                "10",
                python,
                "-m",
                "compileall",
                "-q",
                "-j",
                COMPILE_WORKERS,
                site_packages,
            ]
            try:
                self._proc = subprocess.Popen(
                    cmd,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return
            except OSError:
                self._skipped.append(name)
        self._proc = None
        self._finish()

    def _poll(self) -> None:
        if self._proc is None:
            self._finish()
            return
        rc = self._proc.poll()
        if rc is None:
            return
        if rc == 0:
            self._done += 1
        else:
            # compileall returns non-zero when some files could not be compiled
            # (e.g. read-only venv without a cache prefix) — count as skipped.
            self._skipped.append(self._current_name)
        self._proc = None
        if self._pending:
            self._start_next()
            self.stateChanged.emit()
        else:
            self._finish()

    def _finish(self) -> None:
        if not self._active and self._finished:
            return
        self._timer.stop()
        self._active = False
        self._finished = True
        self._current_name = ""
        self.stateChanged.emit()
