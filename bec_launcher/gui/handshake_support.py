"""Detect whether a deployment can talk the launch-progress handshake.

Deployments are upgraded independently of the launcher, so a launcher that
speaks the handshake will regularly be pointed at a ``bec_widgets`` that predates
it. Such a deployment never connects to the progress socket, which would leave
the loading banner spinning forever. To stay backwards compatible, the launcher
probes the deployment first and falls back to the pre-handshake behaviour
(launch and quit immediately, no banner) when support is missing.

The probe runs the deployment's own interpreter and only *locates*
``bec_widgets`` via ``importlib.util.find_spec`` — it never imports the package,
so it costs an interpreter startup (~50 ms warm) instead of the multi-second
import of the real GUI stack.
"""

from __future__ import annotations

import os
import subprocess

from bec_launcher.deployments import deployment_python

# Module the child needs for the handshake (bec_widgets.utils.launch_progress).
_PROBE_SOURCE = (
    "import importlib.util, os, sys\n"
    "spec = importlib.util.find_spec('bec_widgets')\n"
    "if not spec or not spec.origin:\n"
    "    sys.exit(2)\n"
    "path = os.path.join(os.path.dirname(spec.origin), 'utils', 'launch_progress.py')\n"
    "sys.exit(0 if os.path.exists(path) else 1)\n"
)

PROBE_TIMEOUT_S = 10.0


def deployment_supports_handshake(
    deployment_path: str, timeout: float = PROBE_TIMEOUT_S
) -> bool | None:
    """Check whether ``deployment_path`` ships a handshake-capable ``bec_widgets``.

    Args:
        deployment_path(str): Path of the deployment to probe.
        timeout(float): Seconds to wait for the probe interpreter.

    Returns:
        bool | None: ``True``/``False`` when the probe answered, ``None`` when it
        was inconclusive (no interpreter found, timeout, or an unexpected error).
        Callers should treat ``None`` optimistically and rely on the launcher's
        hello-timeout fallback instead.
    """
    python = deployment_python(deployment_path)
    if not python:
        return None

    # Mirror launch_deployment's isolation: an inherited PYTHONPATH (PyCharm content
    # roots, conda hooks) would point the probe at a foreign bec_widgets checkout and
    # answer for the wrong code.
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)

    try:
        result = subprocess.run(
            # -I (isolated) keeps the answer about the *deployment*: it stops Python
            # from prepending the launcher's working directory to sys.path, which
            # would otherwise let a bec_widgets checkout the launcher happens to be
            # started from answer instead of the deployment's own installation.
            [python, "-I", "-c", _PROBE_SOURCE],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    return None
