"""Unit tests for the background deployment cache warm-up."""

from __future__ import annotations

import os
import sys
import time

from PySide6.QtCore import QCoreApplication

from bec_launcher.gui.cache_warmup import DeploymentCacheWarmup


def _app() -> QCoreApplication:
    return QCoreApplication.instance() or QCoreApplication([])


def _spin(app, predicate, timeout: float = 20.0) -> bool:
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        app.processEvents()
        if predicate():
            return True
        time.sleep(0.01)
    app.processEvents()
    return predicate()


def _make_deployment(tmp_path, name: str):
    """Create a minimal deployment: bec_venv with a real python and one module."""
    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    dep = tmp_path / name
    bin_dir = dep / "bec_venv" / "bin"
    site = dep / "bec_venv" / "lib" / version / "site-packages"
    bin_dir.mkdir(parents=True)
    site.mkdir(parents=True)
    os.symlink(sys.executable, bin_dir / "python")
    (site / "warm_me.py").write_text("X = 1\n")
    return dep, site


def test_warmup_compiles_deployment_site_packages(tmp_path):
    app = _app()
    dep, site = _make_deployment(tmp_path, "beamline")

    warmup = DeploymentCacheWarmup()
    events = []
    warmup.stateChanged.connect(lambda: events.append(warmup.status_text))
    warmup.start({"beamline": str(dep)})

    assert warmup.active is True
    assert "beamline" in warmup.status_text
    assert _spin(app, lambda: not warmup.active)

    pyc = list((site / "__pycache__").glob("warm_me.*.pyc"))
    assert pyc, "bytecode was not generated"
    assert warmup.status_text == "Python caches ready"
    assert events  # UI got at least one state update


def test_warmup_compiles_into_pycache_prefix(tmp_path):
    app = _app()
    dep, site = _make_deployment(tmp_path, "beamline")
    prefix = tmp_path / "cache-prefix"
    prefix.mkdir()

    warmup = DeploymentCacheWarmup(pycache_prefix=str(prefix))
    warmup.start({"beamline": str(dep)})
    assert _spin(app, lambda: not warmup.active)

    # With a prefix, bytecode mirrors the source path under the prefix instead of
    # landing in site-packages/__pycache__.
    assert not (site / "__pycache__").exists()
    mirrored = list(prefix.rglob("warm_me.*.pyc"))
    assert mirrored, "bytecode was not generated under the prefix"


def test_warmup_skips_deployments_without_venv(tmp_path):
    _app()
    dep = tmp_path / "no_venv"
    dep.mkdir()

    warmup = DeploymentCacheWarmup()
    warmup.start({"no_venv": str(dep)})

    # Nothing warmable: finishes silently without ever becoming active.
    assert warmup.active is False
    assert warmup.status_text == ""


def test_warmup_runs_only_once():
    _app()
    warmup = DeploymentCacheWarmup()
    warmup.start({})
    assert warmup.active is False
    # A second start (e.g. after refresh) must not restart the machinery.
    warmup.start({"x": "/nonexistent"})
    assert warmup.active is False
    assert warmup.status_text == ""
