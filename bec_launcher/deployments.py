"""
Simple helpers for fetching available deployments.
"""

from __future__ import annotations

import os
import shlex
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


def deployment_python(deployment_path: str) -> str:
    """
    Locate the Python interpreter of a deployment's virtual environment.

    Supports both supported layouts: a nested ``bec_venv`` and a deployment
    directory that is itself the venv.

    Args:
        deployment_path (str): The path to the deployment.

    Returns:
        str: Path to the interpreter, or an empty string when none was found.
    """
    for env_dir in (os.path.join(deployment_path, "bec_venv"), deployment_path):
        python = os.path.join(env_dir, "bin", "python")
        if os.path.exists(python):
            return python
    return ""


def launch_deployment(
    deployment_path: str,
    cmd: str,
    activate_env: bool = True,
    launch_new_terminal: bool = True,
    extra_env: dict[str, str] | None = None,
) -> subprocess.Popen | None:
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
        launch_new_terminal (bool): Whether to launch the command in a new terminal window.
        extra_env (dict[str, str] | None): Environment variables to set for the launched command.

    Returns:
        subprocess.Popen | None: The launched GUI process when ``launch_new_terminal`` is
        False (so the caller can watch it for an early exit); ``None`` for the
        terminal-based paths, where only an intermediate terminal/osascript process exists.
    """
    activation_script = os.path.join(deployment_path, "bec_venv", "bin", "activate")
    if not os.path.exists(activation_script):
        root_activation_script = os.path.join(deployment_path, "bin", "activate")
        if os.path.exists(root_activation_script):
            activation_script = root_activation_script
    env_path = os.path.dirname(os.path.dirname(activation_script))

    if not launch_new_terminal:
        command = shlex.split(cmd)
        if not command:
            raise ValueError("Command must not be empty.")
        env = os.environ.copy()
        if extra_env:
            env.update({key: str(value) for key, value in extra_env.items()})
        if activate_env:
            env["VIRTUAL_ENV"] = env_path
            env.pop("PYTHONHOME", None)
            # The deployment venv must be authoritative: an inherited PYTHONPATH
            # (e.g. PyCharm's "add content roots", conda hooks) would shadow the
            # venv's site-packages with foreign checkouts.
            env.pop("PYTHONPATH", None)
            env["PATH"] = os.pathsep.join([os.path.join(env_path, "bin"), env.get("PATH", "")])
            executable = os.path.join(env_path, "bin", command[0])
            if os.path.exists(executable):
                command[0] = executable
        return subprocess.Popen(command, env=env, start_new_session=True)

    # Same isolation for the terminal path: on Linux the terminal inherits the
    # launcher's environment, and shell rc files may set PYTHONPATH on macOS too.
    activation_command = f"unset PYTHONPATH PYTHONHOME; source {shlex.quote(activation_script)}"
    env_prefix = ""
    if extra_env:
        env_prefix = " ".join(
            f"{key}={shlex.quote(str(value))}" for key, value in extra_env.items()
        )
        env_prefix += " "

    command = f"{env_prefix}{cmd}"
    if not activate_env:
        full_command = command
    else:
        full_command = f"{activation_command} && {command}"
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
        full_command = ["bash", "-c", f"{full_command}"]
        if launch_new_terminal:
            # We prefix the command with "gnome-terminal --" to
            # ensure it runs in a new terminal window.
            full_command = ["gnome-terminal", "--"] + full_command
        subprocess.Popen(full_command)
    else:
        raise NotImplementedError("This function only supports macOS and Linux.")
