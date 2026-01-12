"""
Simple helpers for fetching available deployments.
"""

from __future__ import annotations

import os
import subprocess
from typing import TypedDict


class DeploymentDict(TypedDict):
    """
    Dictionary structure for deployment names.
    """

    production: list[str]
    test: list[str]


def get_available_deployments(base_path: str) -> DeploymentDict:
    """
    Get a list of available deployments by listing directories in the given base path.

    Returns:
        DeploymentDict: A dictionary with 'production' and 'test' keys containing lists of deployment names.
    """
    out: DeploymentDict = {"production": [], "test": []}

    if not os.path.exists(base_path):
        return out

    for item in os.listdir(base_path):
        # Skip if not a directory
        if not os.path.isdir(os.path.join(base_path, item)):
            continue

        # Skip if ends with "deployments" or starts with "old"
        if (
            item.endswith("deployments")
            or item.startswith("old")
            or item.startswith(".")
            or item.startswith("_")
        ):
            continue

        # If the item starts with "test_", add to test deployments
        if item.startswith("test"):
            out["test"].append(item)
        else:
            out["production"].append(item)

    return out


def launch_deployment(deployment_path: str, cmd: str, activate_env: bool = True) -> None:
    """
    Activate the BEC environment for the specified deployment
    and execute the given command. To this end, we open a new terminal window
    and run the activation command followed by the specified command.

    Only macOS and Linux are supported.

    Note that the current process will quit after launching the command.
    Args:
        deployment_path (str): The path to the deployment.
        cmd (str): The command to execute after activation.
        activate_env (bool): Whether to activate the BEC virtual environment.
    """
    activation_command = f"source {os.path.join(deployment_path, 'bec_venv', 'bin', 'activate')}"
    if not activate_env:
        full_command = cmd
    else:
        full_command = f"{activation_command} && {cmd}"
    platform = os.uname().sysname

    if platform == "Darwin":  # macOS
        iterm_check = subprocess.run(
            ["osascript", "-e", 'application "iTerm" is running'],
            capture_output=True,
            text=True,
            check=True,
        )
        if iterm_check.returncode == 0:
            # iTerm is running
            apple_script = f"""
            tell application "iTerm"
                create window with default profile
                tell current session of current window
                    write text "{full_command}"
                end tell
            end tell
            """
        else:
            # iTerm is not running, use Terminal.app
            apple_script = f"""
            tell application "Terminal"
                do script "{full_command}"
                activate
            end tell
            """
        subprocess.Popen(["osascript", "-e", apple_script])
    elif platform == "Linux":
        subprocess.Popen(["gnome-terminal", "--", "bash", "-c", full_command])
    else:
        raise NotImplementedError("This function only supports macOS and Linux.")
