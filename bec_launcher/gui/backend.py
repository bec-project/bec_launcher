"""
Backend for the BEC Launcher QML application.
Provides deployment data and launch actions to the QML frontend.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

from PySide6.QtCore import Property, QObject, QSettings, Signal, Slot

from bec_launcher.deployments import get_available_deployments, launch_deployment

DEFAULT_DEPLOYMENTS_PATH = str(Path(sys.prefix).parent.parent.parent / "config" / "bec")

SETTINGS_DEFAULT_DEPLOYMENT = "launcher/default_deployment"
SETTINGS_DEFAULT_ACTION = "launcher/default_action"
SETTINGS_REMEMBER_CHOICE = "launcher/remember_choice"
SETTINGS_LAST_DEPLOYMENT = "launcher/last_deployment"
SETTINGS_LAST_ACTION = "launcher/last_action"

VALID_ACTIONS = {"terminal", "dock", "app"}


class Backend(QObject):
    """Backend providing deployment data and actions for the QML UI."""

    deploymentNamesChanged = Signal()
    deploymentPathsChanged = Signal()
    selectedIndexChanged = Signal()
    deploymentConfirmedChanged = Signal()
    defaultDeploymentChanged = Signal()
    defaultActionChanged = Signal()
    quitApplication = Signal()

    def __init__(self, base_path: str | None = None, fresh_start: bool = False):
        super().__init__()

        self._base_path = base_path or DEFAULT_DEPLOYMENTS_PATH
        self._fresh_start = fresh_start
        self._settings = QSettings("PSI", "BECLauncher")

        print(f"[Backend] Using deployments path: {self._base_path}")
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

        self._load_deployments()
        self._migrate_legacy_settings()
        self._load_saved_defaults()
        self._apply_default_state()
        self._auto_select_single_deployment()

    def _normalize_action(self, action: str) -> str:
        if action == "gui":
            return "dock"
        return action if action in VALID_ACTIONS else ""

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
        if (
            self._should_auto_launch
            or self._deployment_confirmed
            or len(self._deployment_names) != 1
        ):
            return

        should_emit_selected = self._selected_index != 0
        should_emit_confirmed = not self._deployment_confirmed

        self._selected_index = 0
        self._deployment_confirmed = True
        print(f"[Backend] Auto-selecting the only deployment: {self._deployment_names[0]}")

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
            launch_deployment(
                path, command, activate_env=True, launch_new_terminal=launch_new_terminal
            )
            self.quitApplication.emit()
        except Exception as exc:
            print(f"[Backend] Error launching {label}: {exc}")

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
