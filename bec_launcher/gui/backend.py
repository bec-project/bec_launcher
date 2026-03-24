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

# Default to the deployments folder in bec_launcher package
DEFAULT_DEPLOYMENTS_PATH = str(Path(sys.prefix).parent.parent.parent / "config" / "bec")

# Settings keys
SETTINGS_REMEMBER_CHOICE = "launcher/remember_choice"
SETTINGS_LAST_DEPLOYMENT = "launcher/last_deployment"
SETTINGS_LAST_ACTION = "launcher/last_action"  # "terminal", "dock", or "app"


class Backend(QObject):
    """Backend providing deployment data and actions for the QML UI."""

    # Signals for property changes
    deploymentNamesChanged = Signal()
    deploymentPathsChanged = Signal()
    selectedIndexChanged = Signal()
    deploymentConfirmedChanged = Signal()
    rememberChoiceChanged = Signal()
    autoLaunchTriggered = Signal(str)  # Emits "terminal", "dock", or "app" for auto-launch
    quitApplication = Signal()  # Signal to quit the application

    def __init__(self, base_path: str | None = None, fresh_start: bool = False):
        super().__init__()

        self._base_path = base_path or DEFAULT_DEPLOYMENTS_PATH
        self._fresh_start = fresh_start
        self._settings = QSettings("PSI", "BECLauncher")

        print(f"[Backend] Using deployments path: {self._base_path}")
        if fresh_start:
            print("[Backend] Fresh start requested - ignoring saved preferences")

        self._deployment_names: List[str] = []
        self._deployment_paths_list: List[str] = []
        self._deployment_paths: dict[str, str] = {}
        self._selected_index: int = -1
        self._deployment_confirmed: bool = False
        self._remember_choice: bool = False
        self._should_auto_launch: bool = False
        self._auto_launch_action: str = ""

        # Load deployments
        self._load_deployments()

        # Load saved preferences (unless fresh start)
        if not fresh_start:
            self._load_saved_preferences()

        self._auto_select_single_deployment()

    def _load_saved_preferences(self) -> None:
        """Load saved preferences from QSettings."""
        self._remember_choice = self._settings.value(SETTINGS_REMEMBER_CHOICE, False, type=bool)

        if self._remember_choice:
            saved_deployment = self._settings.value(SETTINGS_LAST_DEPLOYMENT, "", type=str)
            saved_action = self._settings.value(SETTINGS_LAST_ACTION, "", type=str)

            if saved_deployment and saved_action:
                if saved_action == "gui":
                    saved_action = "dock"

                # Find the index of the saved deployment
                try:
                    idx = self._deployment_names.index(saved_deployment)
                    self._selected_index = idx
                    self._deployment_confirmed = True
                    self._should_auto_launch = True
                    self._auto_launch_action = saved_action
                    print(f"[Backend] Auto-selecting saved deployment: {saved_deployment}")
                    print(f"[Backend] Will auto-launch: {saved_action}")
                except ValueError:
                    print(f"[Backend] Saved deployment '{saved_deployment}' not found, ignoring")
                    self._remember_choice = False
                    self._should_auto_launch = False

    def _save_preferences(self, action: str) -> None:
        """Save current preferences to QSettings."""
        if self._remember_choice and self._selected_index >= 0:
            deployment_name = self._deployment_names[self._selected_index]
            self._settings.setValue(SETTINGS_REMEMBER_CHOICE, True)
            self._settings.setValue(SETTINGS_LAST_DEPLOYMENT, deployment_name)
            self._settings.setValue(SETTINGS_LAST_ACTION, action)
            print(f"[Backend] Saved preferences: {deployment_name} -> {action}")
        else:
            self._settings.setValue(SETTINGS_REMEMBER_CHOICE, False)
            self._settings.remove(SETTINGS_LAST_DEPLOYMENT)
            self._settings.remove(SETTINGS_LAST_ACTION)

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

        # Add production deployments first
        for name in sorted(deployments["production"]):
            self._deployment_names.append(name)
            path = os.path.join(self._base_path, name)
            self._deployment_paths_list.append(path)
            self._deployment_paths[name] = path

        # Then add test deployments
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

    # ─────────────────────────────────────────────────────────
    # Properties exposed to QML
    # ─────────────────────────────────────────────────────────

    @Property(list, notify=deploymentNamesChanged)
    def deploymentNames(self) -> List[str]:
        """List of deployment names available for selection."""
        return self._deployment_names

    @Property(list, notify=deploymentPathsChanged)
    def deploymentPaths(self) -> List[str]:
        """List of deployment paths corresponding to deploymentNames."""
        return self._deployment_paths_list

    @Property(int, notify=selectedIndexChanged)
    def selectedIndex(self) -> int:
        """Currently selected deployment index."""
        return self._selected_index

    @Property(bool, notify=deploymentConfirmedChanged)
    def deploymentConfirmed(self) -> bool:
        """Whether a deployment has been confirmed."""
        return self._deployment_confirmed

    @Property(bool, notify=rememberChoiceChanged)
    def rememberChoice(self) -> bool:
        """Whether to remember the user's last choice."""
        return self._remember_choice

    @Property(bool, constant=True)
    def shouldAutoLaunch(self) -> bool:
        """Whether to auto-launch without showing UI."""
        return self._should_auto_launch

    @Property(str, constant=True)
    def autoLaunchAction(self) -> str:
        """The action to auto-launch ('terminal', 'dock', or 'app')."""
        return self._auto_launch_action

    # ─────────────────────────────────────────────────────────
    # Slots callable from QML
    # ─────────────────────────────────────────────────────────

    @Slot(int)
    def selectDeployment(self, index: int) -> None:
        """Select a deployment by index."""
        if index < 0 or index >= len(self._deployment_names):
            return

        if self._selected_index != index:
            self._selected_index = index
            self.selectedIndexChanged.emit()

    @Slot()
    def confirmDeployment(self) -> None:
        """Confirm the current deployment selection."""
        if self._selected_index < 0:
            return

        self._deployment_confirmed = True
        self.deploymentConfirmedChanged.emit()

        if self._remember_choice:
            self._save_preferences("terminal")

    @Slot()
    def changeDeployment(self) -> None:
        """Go back to deployment selection."""
        self._deployment_confirmed = False
        self.deploymentConfirmedChanged.emit()

    @Slot(bool)
    def setRememberChoice(self, remember: bool) -> None:
        """Set whether to remember the user's choice."""
        if self._remember_choice != remember:
            self._remember_choice = remember
            self.rememberChoiceChanged.emit()

            if not remember:
                # Clear saved preferences when unchecked
                self._settings.setValue(SETTINGS_REMEMBER_CHOICE, False)
                self._settings.remove(SETTINGS_LAST_DEPLOYMENT)
                self._settings.remove(SETTINGS_LAST_ACTION)

    @Slot()
    def resetPreferences(self) -> None:
        """Reset all saved preferences."""
        self._remember_choice = False
        self._settings.setValue(SETTINGS_REMEMBER_CHOICE, False)
        self._settings.remove(SETTINGS_LAST_DEPLOYMENT)
        self._settings.remove(SETTINGS_LAST_ACTION)
        self.rememberChoiceChanged.emit()
        print("[Backend] Preferences reset")

    @Slot()
    def launchTerminal(self) -> None:
        """Launch a terminal with the selected deployment's environment."""
        self._launch_action("terminal", "bec --nogui ", "terminal", launch_new_terminal=True)

    @Slot()
    def launchDock(self) -> None:
        """Launch BEC with the dock companion workflow."""
        self._launch_action("dock", "bec ", "dock companion", launch_new_terminal=True)

    @Slot()
    def launchApp(self) -> None:
        """Launch the standalone BEC App."""
        self._launch_action("app", "bec-app", "BEC App", launch_new_terminal=False)

    @Slot()
    def launchGui(self) -> None:
        """Backward-compatible alias for the dock companion action."""
        self.launchDock()

    def _launch_action(
        self, action: str, command: str, label: str, launch_new_terminal: bool = True
    ) -> None:
        """Launch the selected deployment using the requested command."""
        if self._selected_index < 0 or self._selected_index >= len(self._deployment_names):
            print("[Backend] No deployment selected")
            return

        name = self._deployment_names[self._selected_index]
        path = self._deployment_paths.get(name)

        if not path:
            print(f"[Backend] Path not found for deployment: {name}")
            return

        if self._remember_choice:
            self._save_preferences(action)

        print(f"[Backend] Launching {label} for deployment: {name} at {path}")

        try:
            launch_deployment(
                path, command, activate_env=True, launch_new_terminal=launch_new_terminal
            )
            self.quitApplication.emit()
        except Exception as e:
            print(f"[Backend] Error launching {label}: {e}")

    @Slot()
    def refresh(self) -> None:
        """Refresh the list of deployments."""
        self._load_deployments()
        self._selected_index = -1
        self._deployment_confirmed = False
        self._should_auto_launch = False
        self._auto_launch_action = ""
        self._auto_select_single_deployment()
        self.selectedIndexChanged.emit()
        self.deploymentConfirmedChanged.emit()
