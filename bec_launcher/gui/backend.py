"""
Backend for the BEC Launcher QML application.
Provides deployment data and launch actions to the QML frontend.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal, Slot, Property, QSettings

from bec_launcher.deployments import get_available_deployments, launch_deployment

# Default to the deployments folder in bec_launcher package
DEFAULT_DEPLOYMENTS_PATH = str(Path(__file__).parent.parent / "deployments")

# Settings keys
SETTINGS_REMEMBER_CHOICE = "launcher/remember_choice"
SETTINGS_LAST_DEPLOYMENT = "launcher/last_deployment"
SETTINGS_LAST_ACTION = "launcher/last_action"  # "terminal" or "gui"


def _get_version() -> str:
    """Get version from importlib.metadata or fallback to pyproject.toml."""
    try:
        from importlib.metadata import version

        return version("bec_launcher")
    except Exception:
        pass

    # Fallback: read from pyproject.toml
    try:
        import tomllib

        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "unknown")
    except Exception:
        pass

    return "unknown"


class Backend(QObject):
    """Backend providing deployment data and actions for the QML UI."""

    # Signals for property changes
    deploymentNamesChanged = Signal()
    deploymentPathsChanged = Signal()
    selectedIndexChanged = Signal()
    deploymentConfirmedChanged = Signal()
    versionChanged = Signal()
    rememberChoiceChanged = Signal()
    autoLaunchTriggered = Signal(str)  # Emits "terminal" or "gui" for auto-launch
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
        self._version: str = _get_version()
        self._remember_choice: bool = False
        self._should_auto_launch: bool = False
        self._auto_launch_action: str = ""

        # Load deployments
        self._load_deployments()

        # Load saved preferences (unless fresh start)
        if not fresh_start:
            self._load_saved_preferences()

    def _load_saved_preferences(self) -> None:
        """Load saved preferences from QSettings."""
        self._remember_choice = self._settings.value(SETTINGS_REMEMBER_CHOICE, False, type=bool)

        if self._remember_choice:
            saved_deployment = self._settings.value(SETTINGS_LAST_DEPLOYMENT, "", type=str)
            saved_action = self._settings.value(SETTINGS_LAST_ACTION, "", type=str)

            if saved_deployment and saved_action:
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

    @Property(str, notify=versionChanged)
    def version(self) -> str:
        """Application version from pyproject.toml."""
        return self._version

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
        """The action to auto-launch ('terminal' or 'gui')."""
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

        # Save preferences if enabled
        action = "gui"  # Default to GUI action
        if self._remember_choice:
            # Check if we should launch terminal instead
            name = self._deployment_names[self._selected_index]
            path = self._deployment_paths.get(name)
            if path and os.path.exists(os.path.join(path, "bin", "bash")):
                action = "terminal"

        self._save_preferences(action)

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
        if self._selected_index < 0 or self._selected_index >= len(self._deployment_names):
            print("[Backend] No deployment selected")
            return

        name = self._deployment_names[self._selected_index]
        path = self._deployment_paths.get(name)

        if not path:
            print(f"[Backend] Path not found for deployment: {name}")
            return

        # Save preference if remember is enabled
        if self._remember_choice:
            self._save_preferences("terminal")

        print(f"[Backend] Launching terminal for deployment: {name} at {path}")

        try:
            # Just open a shell in the activated environment
            launch_deployment(path, "bec --nogui", activate_env=True)
            # Quit the launcher after starting the terminal
            self.quitApplication.emit()
        except Exception as e:
            print(f"[Backend] Error launching terminal: {e}")

    @Slot()
    def launchGui(self) -> None:
        """Launch the GUI for the selected deployment."""
        if self._selected_index < 0 or self._selected_index >= len(self._deployment_names):
            print("[Backend] No deployment selected")
            return

        name = self._deployment_names[self._selected_index]
        path = self._deployment_paths.get(name)

        if not path:
            print(f"[Backend] Path not found for deployment: {name}")
            return

        # Save preference if remember is enabled
        if self._remember_choice:
            self._save_preferences("gui")

        print(f"[Backend] Launching GUI for deployment: {name} at {path}")

        try:
            # Launch bec-gui command
            launch_deployment(path, "bec-server-gui", activate_env=True)
            # Quit the launcher after starting the GUI
            self.quitApplication.emit()
        except Exception as e:
            print(f"[Backend] Error launching GUI: {e}")

    @Slot()
    def refresh(self) -> None:
        """Refresh the list of deployments."""
        self._load_deployments()
        self._selected_index = -1
        self._deployment_confirmed = False
        self.selectedIndexChanged.emit()
        self.deploymentConfirmedChanged.emit()
