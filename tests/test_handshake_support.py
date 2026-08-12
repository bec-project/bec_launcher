"""Unit tests for handshake capability detection of deployments."""

from __future__ import annotations

import os
import sys
import sysconfig

from bec_launcher.deployments import deployment_python
from bec_launcher.gui.handshake_support import deployment_supports_handshake


def _make_deployment(tmp_path, name: str, with_handshake: bool, nested_venv: bool = True):
    """Build a deployment that behaves like a real venv holding a stub bec_widgets.

    A ``pyvenv.cfg`` next to ``bin/python`` is what makes the interpreter treat the
    directory as a venv and pick up its ``site-packages`` — so the probe resolves the
    stub exactly like it would resolve a deployment's own bec_widgets.
    """
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    dep = tmp_path / name
    env = dep / "bec_venv" if nested_venv else dep
    bin_dir = env / "bin"
    site = env / "lib" / version / "site-packages"
    bin_dir.mkdir(parents=True)
    site.mkdir(parents=True)
    os.symlink(sys.executable, bin_dir / "python")
    (env / "pyvenv.cfg").write_text(
        f"home = {os.path.dirname(sys.executable)}\n"
        "include-system-site-packages = false\n"
        f"version = {sysconfig.get_python_version()}\n"
    )

    pkg = site / "bec_widgets"
    (pkg / "utils").mkdir(parents=True)
    # Explodes if executed: proves the probe only *locates* the package.
    (pkg / "__init__.py").write_text("raise RuntimeError('must not be imported')\n")
    (pkg / "utils" / "__init__.py").write_text("")
    if with_handshake:
        (pkg / "utils" / "launch_progress.py").write_text("launch_progress = None\n")
    return dep, site


def test_detects_deployment_with_handshake(tmp_path):
    dep, _ = _make_deployment(tmp_path, "new_deployment", with_handshake=True)
    assert deployment_supports_handshake(str(dep)) is True


def test_detects_deployment_without_handshake(tmp_path):
    dep, _ = _make_deployment(tmp_path, "old_deployment", with_handshake=False)
    assert deployment_supports_handshake(str(dep)) is False


def test_probe_ignores_inherited_pythonpath(tmp_path, monkeypatch):
    """A foreign checkout on PYTHONPATH must not answer for the deployment."""
    foreign = tmp_path / "foreign"
    (foreign / "bec_widgets" / "utils").mkdir(parents=True)
    (foreign / "bec_widgets" / "__init__.py").write_text("")
    (foreign / "bec_widgets" / "utils" / "__init__.py").write_text("")
    (foreign / "bec_widgets" / "utils" / "launch_progress.py").write_text("")

    dep, _ = _make_deployment(tmp_path, "old_deployment", with_handshake=False)
    monkeypatch.setenv("PYTHONPATH", str(foreign))

    # Without the shield the foreign copy would make this report True.
    assert deployment_supports_handshake(str(dep)) is False


def test_probe_ignores_the_working_directory(tmp_path, monkeypatch):
    """A bec_widgets checkout in the launcher's cwd must not answer for the deployment."""
    cwd_checkout = tmp_path / "some_checkout"
    (cwd_checkout / "bec_widgets" / "utils").mkdir(parents=True)
    (cwd_checkout / "bec_widgets" / "__init__.py").write_text("")
    (cwd_checkout / "bec_widgets" / "utils" / "__init__.py").write_text("")
    (cwd_checkout / "bec_widgets" / "utils" / "launch_progress.py").write_text("")

    dep, _ = _make_deployment(tmp_path, "old_deployment", with_handshake=False)
    monkeypatch.chdir(cwd_checkout)

    # Without isolation the cwd copy would make this report True.
    assert deployment_supports_handshake(str(dep)) is False


def test_probe_is_inconclusive_without_interpreter(tmp_path):
    dep = tmp_path / "no_venv"
    dep.mkdir()
    assert deployment_supports_handshake(str(dep)) is None


def test_probe_is_inconclusive_when_bec_widgets_is_missing(tmp_path):
    dep = tmp_path / "empty_venv"
    bin_dir = dep / "bec_venv" / "bin"
    site = dep / "bec_venv" / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}"
    (site / "site-packages").mkdir(parents=True)
    bin_dir.mkdir(parents=True)
    os.symlink(sys.executable, bin_dir / "python")
    (dep / "bec_venv" / "pyvenv.cfg").write_text(
        f"home = {os.path.dirname(sys.executable)}\ninclude-system-site-packages = false\n"
    )

    assert deployment_supports_handshake(str(dep)) is None


def test_deployment_python_supports_both_layouts(tmp_path):
    nested, _ = _make_deployment(tmp_path, "nested", with_handshake=True)
    assert deployment_python(str(nested)) == str(nested / "bec_venv" / "bin" / "python")

    flat, _ = _make_deployment(tmp_path, "flat", with_handshake=True, nested_venv=False)
    assert deployment_python(str(flat)) == str(flat / "bin" / "python")

    assert deployment_python(str(tmp_path / "missing")) == ""
