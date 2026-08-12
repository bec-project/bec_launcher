"""
Backend for the BEC Launcher QML application.
Provides deployment data and launch actions to the QML frontend.
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path
from typing import List

from PySide6.QtCore import Property, QObject, QSettings, QTimer, Signal, Slot

from bec_launcher.deployments import get_available_deployments, launch_deployment
from bec_launcher.gui.cache_warmup import DeploymentCacheWarmup
from bec_launcher.gui.progress_server import ProgressServer

DEFAULT_DEPLOYMENTS_PATH = str(Path(sys.prefix).parent.parent.parent / "config" / "bec")

SETTINGS_DEFAULT_DEPLOYMENT = "launcher/default_deployment"
SETTINGS_DEFAULT_ACTION = "launcher/default_action"
SETTINGS_REMEMBER_CHOICE = "launcher/remember_choice"
SETTINGS_LAST_DEPLOYMENT = "launcher/last_deployment"
SETTINGS_LAST_ACTION = "launcher/last_action"

# Handshake env vars injected into the launched GUI process (child side lives in
# bec_widgets.utils.launch_progress).
PROGRESS_SOCKET_ENV = "BEC_LAUNCH_PROGRESS_SOCKET"
PROGRESS_TOKEN_ENV = "BEC_LAUNCH_PROGRESS_TOKEN"
PROGRESS_APP_ENV = "BEC_LAUNCH_APP"

# Known bec-app startup stages; used only as the denominator for the banner's
# step meter. Extra or missing stages are tolerated gracefully.
EXPECTED_STAGES = (
    "module imports",
    "QApplication",
    "theme applied",
    "BEC connection + base window",
    "views added",
    "guided tour",
    "main window built",
    "window shown",
    "interactive",
)

# Time without any progress message (and without a ready edge) before the banner
# flags the launch as stalled. Generous, to tolerate cold NFS/Redis starts.
STALL_TIMEOUT_S = 45.0

# Delay before the background cache warm-up starts, so it never competes with the
# launcher's own startup for I/O.
WARMUP_START_DELAY_MS = 1500

VALID_ACTIONS = {"terminal", "dock", "app"}
GUI_ACTIONS = {"dock", "app"}


class Backend(QObject):
    """Backend providing deployment data and actions for the QML UI."""

    deploymentNamesChanged = Signal()
    deploymentPathsChanged = Signal()
    selectedIndexChanged = Signal()
    deploymentConfirmedChanged = Signal()
    defaultDeploymentChanged = Signal()
    defaultActionChanged = Signal()
    launchStateChanged = Signal()
    cacheWarmupChanged = Signal()
    quitApplication = Signal()

    def __init__(
        self, base_path: str | None = None, fresh_start: bool = False, pycache_prefix: str = ""
    ):
        super().__init__()

        self._base_path = base_path or DEFAULT_DEPLOYMENTS_PATH
        self._fresh_start = fresh_start
        self._settings = QSettings("PSI", "BECLauncher")
        self._pycache_prefix = self._setup_pycache_prefix(pycache_prefix)

        print(f"[Backend] Using deployments path: {self._base_path}")
        settings_file = getattr(self._settings, "fileName", lambda: "")()
        print(f"[Backend] Using settings file: {settings_file}")
        if fresh_start:
            print(
                "[Backend] Fresh start requested - defaults will be preloaded without auto-launch"
            )

        self._deployment_names: List[str] = []
        self._deployment_paths_list: List[str] = []
        self._deployment_paths: dict[str, str] = {}
        self._selected_index = -1
        self._deployment_confirmed = False
        self._default_deployment = ""
        self._default_action = ""
        self._should_auto_launch = False
        self._auto_launch_action = ""
        self._launch_in_progress = False
        self._launch_has_error = False
        self._launch_status = ""
        self._launch_mode = ""
        self._launch_deployment = ""
        self._launch_started_at = 0.0
        self._launch_elapsed_seconds = 0
        self._launch_stages: list[dict] = []
        self._launch_current_stage = ""
        self._launch_is_stalled = False
        self._launch_last_activity = 0.0
        self._launch_child_proc = None  # subprocess.Popen | None (no-terminal path)
        self._launch_token = ""

        self._launch_cold_start = False

        self._progress_server = ProgressServer(self)
        self._progress_server.helloReceived.connect(self._on_child_hello)
        self._progress_server.stageReceived.connect(self._on_child_stage)
        self._progress_server.infoReceived.connect(self._on_child_info)
        self._progress_server.readyReceived.connect(self._on_child_ready)
        self._progress_server.errorReceived.connect(self._on_child_error)
        self._progress_server.clientDisconnected.connect(self._on_child_disconnected)

        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.setInterval(250)
        self._elapsed_timer.timeout.connect(self._update_waiting_state)

        self._cache_warmup = DeploymentCacheWarmup(self, pycache_prefix=self._pycache_prefix)
        self._cache_warmup.stateChanged.connect(self.cacheWarmupChanged)

        self._load_deployments()
        self._migrate_legacy_settings()
        self._load_saved_defaults()
        self._apply_default_state()
        self._auto_select_single_deployment()

        # Use the time the user spends choosing a deployment/action to pre-compile
        # bytecode caches for all available deployments in the background.
        QTimer.singleShot(WARMUP_START_DELAY_MS, self._start_cache_warmup)

    def __del__(self):
        try:
            self._progress_server.stop()
        except Exception:  # pragma: no cover - best-effort teardown
            pass

    @staticmethod
    def _normalize_action(action: str) -> str:
        if action == "gui":
            return "dock"
        return action if action in VALID_ACTIONS else ""

    @staticmethod
    def _setup_pycache_prefix(pycache_prefix: str) -> str:
        """Normalize and create the bytecode-cache prefix directory.

        On Linux an unset prefix defaults to ``~/.cache/bec-pycache`` (deployment
        venvs there are typically read-only NFS), matching the behavior the
        launcher previously hardcoded in ``launch_deployment``. macOS keeps no
        default. ``--pycache-prefix`` / ``$BEC_LAUNCHER_PYCACHE_PREFIX`` override.
        """
        if not pycache_prefix and os.uname().sysname == "Linux":
            pycache_prefix = "~/.cache/bec-pycache"
        if not pycache_prefix:
            return ""
        prefix = os.path.abspath(os.path.expanduser(pycache_prefix))
        try:
            os.makedirs(prefix, exist_ok=True)
        except OSError as exc:
            print(f"[Backend] Ignoring unusable pycache prefix '{prefix}': {exc}")
            return ""
        print(f"[Backend] Using Python cache prefix: {prefix}")
        return prefix

    def _launch_base_env(self) -> dict[str, str]:
        """Env vars every launched deployment receives, regardless of action."""
        env: dict[str, str] = {}
        if self._pycache_prefix:
            env["PYTHONPYCACHEPREFIX"] = self._pycache_prefix
        return env

    def _prepare_progress_channel(self, label: str) -> dict[str, str]:
        """Open the per-launch progress socket and return the child env vars."""
        self._progress_server.stop()
        self._launch_token = uuid.uuid4().hex
        socket_path = self._progress_server.start(self._launch_token)
        return {
            PROGRESS_SOCKET_ENV: socket_path,
            PROGRESS_TOKEN_ENV: self._launch_token,
            PROGRESS_APP_ENV: label,
        }

    def _touch_activity(self) -> None:
        self._launch_last_activity = time.monotonic()
        if self._launch_is_stalled:
            self._launch_is_stalled = False

    # -- progress-server signal handlers ------------------------------------
    def _on_child_hello(self, app: str, pid: int) -> None:
        self._touch_activity()
        # The child connects before its heavy imports run, so this is what it is
        # actually doing until the first stage mark arrives.
        self._launch_status = "Loading Python modules..."
        self.launchStateChanged.emit()

    def _on_child_info(self, info: dict) -> None:
        self._touch_activity()
        if info.get("cold_start"):
            self._launch_cold_start = True
            self._launch_status = "First launch — compiling Python bytecode..."
        self.launchStateChanged.emit()

    def _on_child_stage(self, name: str, delta_ms: float, total_ms: float) -> None:
        self._touch_activity()
        # ``ms`` is the per-stage duration (what the banner shows per row); ``total_ms``
        # is cumulative since process start.
        self._launch_stages = self._launch_stages + [
            {"name": name, "ms": int(round(delta_ms)), "total_ms": int(round(total_ms))}
        ]
        self._launch_current_stage = name
        self._launch_status = name
        self.launchStateChanged.emit()

    def _on_child_ready(self, total_ms: float) -> None:
        self._finalize_ready()

    def _on_child_error(self, message: str) -> None:
        self._set_launch_error(message or "The GUI reported an error during startup.")

    def _on_child_disconnected(self) -> None:
        # The socket closed. If it happened before the ready edge while we were
        # still waiting, the GUI process died during startup.
        if self._launch_in_progress and not self._progress_server.got_ready:
            self._set_launch_error("The GUI process exited before it finished starting.")

    def _finalize_ready(self) -> None:
        self._elapsed_timer.stop()
        self._launch_in_progress = False
        self._launch_is_stalled = False
        self._progress_server.stop()
        self._launch_child_proc = None
        self._launch_current_stage = ""
        self._launch_status = "GUI ready"
        self.launchStateChanged.emit()
        self.quitApplication.emit()

    def _begin_launch_banner(self, label: str, deployment_name: str) -> None:
        self._launch_in_progress = True
        self._launch_has_error = False
        self._launch_is_stalled = False
        self._launch_cold_start = False
        self._launch_mode = label
        self._launch_deployment = deployment_name
        self._launch_status = "Starting GUI..."
        self._launch_stages = []
        self._launch_current_stage = ""
        self._launch_child_proc = None
        self._launch_started_at = time.monotonic()
        self._launch_last_activity = self._launch_started_at
        self._launch_elapsed_seconds = 0
        self._elapsed_timer.start()
        self.launchStateChanged.emit()

    def _set_launch_error(self, message: str) -> None:
        self._launch_in_progress = False
        self._launch_has_error = True
        self._launch_is_stalled = False
        self._launch_status = message
        self._elapsed_timer.stop()
        self._progress_server.stop()
        self.launchStateChanged.emit()

    @Slot()
    def dismissLaunchError(self) -> None:
        """Return from the banner to the deployment picker (recovery affordance)."""
        self._elapsed_timer.stop()
        self._progress_server.stop()
        self._launch_in_progress = False
        self._launch_has_error = False
        self._launch_is_stalled = False
        self._launch_cold_start = False
        self._launch_status = ""
        self._launch_stages = []
        self._launch_current_stage = ""
        self._launch_child_proc = None
        self.launchStateChanged.emit()

    def _update_elapsed(self) -> None:
        if not self._launch_started_at:
            return
        elapsed = int(time.monotonic() - self._launch_started_at)
        if elapsed != self._launch_elapsed_seconds:
            self._launch_elapsed_seconds = elapsed
            self.launchStateChanged.emit()

    def _update_waiting_state(self) -> None:
        self._update_elapsed()
        if not self._launch_in_progress:
            return
        self._check_child_liveness()
        self._check_stall()

    def _check_child_liveness(self) -> None:
        """For the no-terminal path, detect a child that exited before ready."""
        proc = self._launch_child_proc
        if proc is None or self._progress_server.got_ready:
            return
        if proc.poll() is not None:
            self._set_launch_error("The GUI process exited before it finished starting.")

    def _check_stall(self) -> None:
        if self._progress_server.got_ready or self._launch_is_stalled:
            return
        if time.monotonic() - self._launch_last_activity > STALL_TIMEOUT_S:
            self._launch_is_stalled = True
            self._launch_status = "Still starting — this can take a while on a cold cache."
            self.launchStateChanged.emit()

    def _persist_default_deployment(self) -> None:
        if self._default_deployment:
            self._settings.setValue(SETTINGS_DEFAULT_DEPLOYMENT, self._default_deployment)
        else:
            self._settings.remove(SETTINGS_DEFAULT_DEPLOYMENT)

    def _persist_default_action(self) -> None:
        if self._default_action:
            self._settings.setValue(SETTINGS_DEFAULT_ACTION, self._default_action)
        else:
            self._settings.remove(SETTINGS_DEFAULT_ACTION)

    def _set_default_deployment(self, deployment_name: str) -> None:
        normalized_name = deployment_name if deployment_name in self._deployment_names else ""
        if self._default_deployment == normalized_name:
            return

        self._default_deployment = normalized_name
        self._persist_default_deployment()
        self.defaultDeploymentChanged.emit()

    def _set_default_action(self, action: str) -> None:
        normalized_action = self._normalize_action(action)
        if self._default_action == normalized_action:
            return

        self._default_action = normalized_action
        self._persist_default_action()
        self.defaultActionChanged.emit()

    def _clear_legacy_settings(self) -> None:
        self._settings.remove(SETTINGS_REMEMBER_CHOICE)
        self._settings.remove(SETTINGS_LAST_DEPLOYMENT)
        self._settings.remove(SETTINGS_LAST_ACTION)

    def _migrate_legacy_settings(self) -> None:
        """Migrate the old remember-choice model to the new default model once."""
        has_new_defaults = self._settings.contains(
            SETTINGS_DEFAULT_DEPLOYMENT
        ) or self._settings.contains(SETTINGS_DEFAULT_ACTION)
        legacy_remember = self._settings.value(SETTINGS_REMEMBER_CHOICE, False, type=bool)
        if has_new_defaults or not legacy_remember:
            return

        legacy_deployment = self._settings.value(SETTINGS_LAST_DEPLOYMENT, "", type=str)
        legacy_action = self._normalize_action(
            self._settings.value(SETTINGS_LAST_ACTION, "", type=str)
        )

        if legacy_deployment:
            self._settings.setValue(SETTINGS_DEFAULT_DEPLOYMENT, legacy_deployment)
        if legacy_action:
            self._settings.setValue(SETTINGS_DEFAULT_ACTION, legacy_action)

        self._clear_legacy_settings()
        print("[Backend] Migrated legacy remember-choice settings to defaults")

    def _load_saved_defaults(self) -> None:
        """Load saved defaults from QSettings."""
        self._default_deployment = self._settings.value(SETTINGS_DEFAULT_DEPLOYMENT, "", type=str)
        raw_action = self._settings.value(SETTINGS_DEFAULT_ACTION, "", type=str)
        self._default_action = self._normalize_action(raw_action)

        if raw_action and not self._default_action:
            self._settings.remove(SETTINGS_DEFAULT_ACTION)
        elif self._default_action:
            self._persist_default_action()

    def _apply_default_state(self) -> None:
        """Preload selection/confirmation state from saved defaults."""
        self._selected_index = -1
        self._deployment_confirmed = False
        self._should_auto_launch = False
        self._auto_launch_action = ""

        if self._default_deployment:
            try:
                self._selected_index = self._deployment_names.index(self._default_deployment)
            except ValueError:
                print(
                    f"[Backend] Saved default deployment '{self._default_deployment}' not found, clearing"
                )
                self._set_default_deployment("")

        if self._default_action and self._default_action not in VALID_ACTIONS:
            self._set_default_action("")

        if self._selected_index >= 0 and self._default_action:
            self._deployment_confirmed = True
            if not self._fresh_start:
                self._should_auto_launch = True
                self._auto_launch_action = self._default_action
                print(
                    f"[Backend] Will auto-launch default action '{self._default_action}' "
                    f"for deployment '{self._deployment_names[self._selected_index]}'"
                )

    def _auto_select_single_deployment(self, emit_signals: bool = False) -> None:
        """Skip Step 1 when exactly one deployment is available."""
        if len(self._deployment_names) != 1 or self._should_auto_launch:
            return

        should_emit_selected = self._selected_index != 0
        should_emit_confirmed = not self._deployment_confirmed

        self._selected_index = 0
        self._deployment_confirmed = True
        deployment_name = self._deployment_names[0]
        print(f"[Backend] Auto-selecting the only deployment: {deployment_name}")

        if not self._default_deployment:
            self._set_default_deployment(deployment_name)

        if self._default_action and not self._fresh_start:
            self._should_auto_launch = True
            self._auto_launch_action = self._default_action
            print(
                f"[Backend] Will auto-launch default action '{self._default_action}' "
                f"for the only deployment '{deployment_name}'"
            )

        if emit_signals:
            if should_emit_selected:
                self.selectedIndexChanged.emit()
            if should_emit_confirmed:
                self.deploymentConfirmedChanged.emit()

    def _load_deployments(self) -> None:
        """Load available deployments from the filesystem."""
        deployments = get_available_deployments(self._base_path)

        self._deployment_names = []
        self._deployment_paths_list = []
        self._deployment_paths = {}

        for name in sorted(deployments["production"]):
            self._deployment_names.append(name)
            path = os.path.join(self._base_path, name)
            self._deployment_paths_list.append(path)
            self._deployment_paths[name] = path

        for name in sorted(deployments["test"]):
            self._deployment_names.append(name)
            path = os.path.join(self._base_path, name)
            self._deployment_paths_list.append(path)
            self._deployment_paths[name] = path

        print(
            f"[Backend] Found {len(self._deployment_names)} deployments: {self._deployment_names}"
        )

        self.deploymentNamesChanged.emit()
        self.deploymentPathsChanged.emit()

    @Property(list, notify=deploymentNamesChanged)
    def deploymentNames(self) -> List[str]:
        return self._deployment_names

    @Property(list, notify=deploymentPathsChanged)
    def deploymentPaths(self) -> List[str]:
        return self._deployment_paths_list

    @Property(int, notify=selectedIndexChanged)
    def selectedIndex(self) -> int:
        return self._selected_index

    @Property(bool, notify=deploymentConfirmedChanged)
    def deploymentConfirmed(self) -> bool:
        return self._deployment_confirmed

    @Property(str, notify=defaultDeploymentChanged)
    def defaultDeployment(self) -> str:
        return self._default_deployment

    @Property(str, notify=defaultActionChanged)
    def defaultAction(self) -> str:
        return self._default_action

    @Property(bool, constant=True)
    def shouldAutoLaunch(self) -> bool:
        return self._should_auto_launch

    @Property(str, constant=True)
    def autoLaunchAction(self) -> str:
        return self._auto_launch_action

    @Property(bool, notify=launchStateChanged)
    def launchInProgress(self) -> bool:
        return self._launch_in_progress

    @Property(bool, notify=launchStateChanged)
    def launchHasError(self) -> bool:
        return self._launch_has_error

    @Property(str, notify=launchStateChanged)
    def launchStatus(self) -> str:
        return self._launch_status

    @Property(str, notify=launchStateChanged)
    def launchMode(self) -> str:
        return self._launch_mode

    @Property(str, notify=launchStateChanged)
    def launchDeployment(self) -> str:
        return self._launch_deployment

    @Property(int, notify=launchStateChanged)
    def launchElapsedSeconds(self) -> int:
        return self._launch_elapsed_seconds

    @Property(list, notify=launchStateChanged)
    def launchStages(self) -> list:
        """List of completed startup stages as ``{"name": str, "ms": int}`` dicts."""
        return self._launch_stages

    @Property(int, notify=launchStateChanged)
    def launchStageCount(self) -> int:
        return len(self._launch_stages)

    @Property(int, constant=True)
    def launchExpectedStages(self) -> int:
        return len(EXPECTED_STAGES)

    @Property(str, notify=launchStateChanged)
    def launchCurrentStage(self) -> str:
        return self._launch_current_stage

    @Property(bool, notify=launchStateChanged)
    def launchIsStalled(self) -> bool:
        return self._launch_is_stalled

    @Property(bool, notify=launchStateChanged)
    def launchIsColdStart(self) -> bool:
        """True when the child reported missing bytecode caches (first launch)."""
        return self._launch_cold_start

    def _start_cache_warmup(self) -> None:
        self._cache_warmup.start(dict(self._deployment_paths))

    @Property(bool, notify=cacheWarmupChanged)
    def cacheWarmupActive(self) -> bool:
        return self._cache_warmup.active

    @Property(str, notify=cacheWarmupChanged)
    def cacheWarmupText(self) -> str:
        return self._cache_warmup.status_text

    @Slot(int)
    def selectDeployment(self, index: int) -> None:
        if index < 0 or index >= len(self._deployment_names):
            return

        if self._selected_index != index:
            self._selected_index = index
            self.selectedIndexChanged.emit()

    @Slot()
    def confirmDeployment(self) -> None:
        if self._selected_index < 0:
            return

        if not self._deployment_confirmed:
            self._deployment_confirmed = True
            self.deploymentConfirmedChanged.emit()

    @Slot()
    def changeDeployment(self) -> None:
        if self._deployment_confirmed:
            self._deployment_confirmed = False
            self.deploymentConfirmedChanged.emit()

    @Slot(int, bool)
    def setDefaultDeployment(self, index: int, enabled: bool) -> None:
        if index < 0 or index >= len(self._deployment_names):
            return

        deployment_name = self._deployment_names[index]
        if enabled:
            self.selectDeployment(index)
            self._set_default_deployment(deployment_name)
        elif self._default_deployment == deployment_name:
            self._set_default_deployment("")

    @Slot(str, bool)
    def setDefaultAction(self, action: str, enabled: bool) -> None:
        normalized_action = self._normalize_action(action)
        if not normalized_action:
            return

        if enabled:
            self._set_default_action(normalized_action)
        elif self._default_action == normalized_action:
            self._set_default_action("")

    @Slot()
    def launchTerminal(self) -> None:
        self._launch_action("terminal", "bec --nogui ", "terminal", launch_new_terminal=True)

    @Slot()
    def launchDock(self) -> None:
        self._launch_action("dock", "bec ", "dock companion", launch_new_terminal=True)

    @Slot()
    def launchApp(self) -> None:
        self._launch_action("app", "bec-app", "BEC App", launch_new_terminal=False)

    @Slot()
    def launchGui(self) -> None:
        self.launchDock()

    def _launch_action(
        self, action: str, command: str, label: str, launch_new_terminal: bool = True
    ) -> None:
        if self._selected_index < 0 or self._selected_index >= len(self._deployment_names):
            print("[Backend] No deployment selected")
            return

        name = self._deployment_names[self._selected_index]
        path = self._deployment_paths.get(name)

        if not path:
            print(f"[Backend] Path not found for deployment: {name}")
            return

        print(f"[Backend] Launching {label} for deployment: {name} at {path}")

        try:
            extra_env = self._launch_base_env()
            if action in GUI_ACTIONS:
                self._begin_launch_banner(label, name)
                extra_env.update(self._prepare_progress_channel(label))
            proc = launch_deployment(
                path,
                command,
                activate_env=True,
                launch_new_terminal=launch_new_terminal,
                extra_env=extra_env or None,
            )
            # Only the no-terminal path hands back the actual GUI child process,
            # so we can watch it for an early exit (crash before ready).
            if action in GUI_ACTIONS and not launch_new_terminal:
                self._launch_child_proc = proc
            if action not in GUI_ACTIONS:
                self.quitApplication.emit()
        except Exception as exc:
            message = f"Error launching {label}: {exc}"
            print(f"[Backend] {message}")
            if action in GUI_ACTIONS:
                self._set_launch_error(message)

    @Slot()
    def refresh(self) -> None:
        self._load_deployments()
        self._load_saved_defaults()
        self._apply_default_state()
        self._auto_select_single_deployment()
        self.selectedIndexChanged.emit()
        self.deploymentConfirmedChanged.emit()
        self.defaultDeploymentChanged.emit()
        self.defaultActionChanged.emit()
