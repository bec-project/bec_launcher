"""
Tests for deployments module.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from bec_launcher.deployments import get_available_deployments, launch_deployment


@pytest.fixture
def temp_deployment_dir(tmpdir):
    """Create a temporary directory structure for testing."""
    base_path = Path(tmpdir)

    # Create various directories
    (base_path / "production").mkdir()
    (base_path / "test").mkdir()
    (base_path / "old_production_deployments").mkdir()
    (base_path / "old_test_deployments").mkdir()
    (base_path / "production_deployments").mkdir()
    (base_path / "test_deployments").mkdir()

    # Create a file (should be ignored)
    (base_path / "readme.txt").touch()

    return str(base_path)


def test_get_available_deployments_filters_correctly(temp_deployment_dir):
    """Test that only valid deployment names are returned."""
    result = get_available_deployments(temp_deployment_dir)

    assert "production" in result["production"]
    assert "test" in result["test"]
    assert len(result["production"]) == 1
    assert len(result["test"]) == 1


def test_get_available_deployments_excludes_old_directories(temp_deployment_dir):
    """Test that directories starting with 'old' are excluded."""
    result = get_available_deployments(temp_deployment_dir)

    all_deployments = result["production"] + result["test"]
    assert not any(d.startswith("old") for d in all_deployments)


def test_get_available_deployments_excludes_deployment_suffixed_directories(temp_deployment_dir):
    """Test that directories ending with 'deployments' are excluded."""
    result = get_available_deployments(temp_deployment_dir)

    all_deployments = result["production"] + result["test"]
    assert not any(d.endswith("deployments") for d in all_deployments)


def test_get_available_deployments_excludes_files(temp_deployment_dir):
    """Test that files are not included in the results."""
    result = get_available_deployments(temp_deployment_dir)

    all_deployments = result["production"] + result["test"]
    assert "readme.txt" not in all_deployments


def test_get_available_deployments_nonexistent_path():
    """Test behavior when the base path doesn't exist."""
    result = get_available_deployments("/nonexistent/path")

    assert result == {"production": [], "test": []}


def test_get_available_deployments_empty_directory(tmpdir):
    """Test behavior with an empty directory."""
    result = get_available_deployments(str(tmpdir))

    assert result == {"production": [], "test": []}


def test_get_available_deployments_separates_test_and_production(tmpdir):
    """Test that test deployments are correctly separated from production."""
    base_path = Path(tmpdir)

    # Create test deployments
    (base_path / "test").mkdir()
    (base_path / "test_env1").mkdir()
    (base_path / "test_env2").mkdir()

    # Create production deployments
    (base_path / "production").mkdir()
    (base_path / "staging").mkdir()
    (base_path / "dev").mkdir()

    result = get_available_deployments(str(base_path))

    assert "test" in result["test"]
    assert "test_env1" in result["test"]
    assert "test_env2" in result["test"]
    assert len(result["test"]) == 3

    assert "production" in result["production"]
    assert "staging" in result["production"]
    assert "dev" in result["production"]


def test_get_available_deployments_complex_scenario(tmpdir):
    """Test with a complex directory structure."""
    base_path = Path(tmpdir)

    # Valid deployments
    (base_path / "production").mkdir()
    (base_path / "test").mkdir()
    (base_path / "staging").mkdir()
    (base_path / "test_feature").mkdir()

    # Should be excluded
    (base_path / "old_production").mkdir()
    (base_path / "old_test").mkdir()
    (base_path / "production_deployments").mkdir()
    (base_path / "test_deployments").mkdir()
    (base_path / "old_deployments").mkdir()

    # Files (should be ignored)
    (base_path / "config.yaml").touch()

    result = get_available_deployments(str(base_path))

    # Check production deployments
    assert "production" in result["production"]
    assert "staging" in result["production"]
    assert len(result["production"]) == 2

    # Check test deployments
    assert "test" in result["test"]
    assert "test_feature" in result["test"]
    assert len(result["test"]) == 2

    # Ensure excluded items are not present
    all_deployments = result["production"] + result["test"]
    assert "old_production" not in all_deployments
    assert "old_test" not in all_deployments
    assert "production_deployments" not in all_deployments
    assert "test_deployments" not in all_deployments
    assert "old_deployments" not in all_deployments


def test_get_available_deployments_custom_names(tmpdir):
    """Test with custom deployment names."""
    base_path = Path(tmpdir)

    # Create custom named deployments
    (base_path / "saxs").mkdir()
    (base_path / "test_saxs").mkdir()

    result = get_available_deployments(str(base_path))

    assert "saxs" in result["production"]
    assert len(result["production"]) == 1
    assert "test_saxs" in result["test"]
    assert len(result["test"]) == 1


@pytest.fixture
def mock_deployment_path(tmpdir):
    """Create a mock deployment directory structure."""
    deployment_path = Path(tmpdir) / "test_deployment"
    deployment_path.mkdir()
    venv_path = deployment_path / "bec_venv" / "bin"
    venv_path.mkdir(parents=True)
    (venv_path / "activate").touch()
    return str(deployment_path)


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
@mock.patch("subprocess.run")
def test_launch_deployment_macos_with_iterm(mock_run, mock_popen, mock_uname, mock_deployment_path):
    """Test launch_deployment on macOS with iTerm running."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Darwin")
    mock_run.return_value = mock.Mock(returncode=0)

    cmd = "bec"
    launch_deployment(mock_deployment_path, cmd)

    # Verify osascript was called to check iTerm
    assert mock_run.called
    run_args = mock_run.call_args[0][0]
    assert "osascript" in run_args
    assert 'application "iTerm" is running' in run_args

    # Verify Popen was called with iTerm AppleScript
    assert mock_popen.called
    popen_args = mock_popen.call_args[0][0]
    assert "osascript" in popen_args
    assert "iTerm" in popen_args[2]
    assert "create window with default profile" in popen_args[2]


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
@mock.patch("subprocess.run")
def test_launch_deployment_macos_without_iterm(
    mock_run, mock_popen, mock_uname, mock_deployment_path
):
    """Test launch_deployment on macOS without iTerm running."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Darwin")
    mock_run.return_value = mock.Mock(returncode=1)  # iTerm not running

    cmd = "bec"
    launch_deployment(mock_deployment_path, cmd)

    # Verify Popen was called with Terminal.app AppleScript
    assert mock_popen.called
    popen_args = mock_popen.call_args[0][0]
    assert "osascript" in popen_args
    assert "Terminal" in popen_args[2]
    assert "do script" in popen_args[2]


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
def test_launch_deployment_linux(mock_popen, mock_uname, mock_deployment_path):
    """Test launch_deployment on Linux."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Linux")

    cmd = "bec"
    launch_deployment(mock_deployment_path, cmd)

    # Verify Popen was called with gnome-terminal
    assert mock_popen.called
    popen_args = mock_popen.call_args[0][0]
    assert "gnome-terminal" in popen_args
    assert "--" in popen_args
    assert "bash" in popen_args
    assert "-c" in popen_args


@mock.patch("os.uname")
def test_launch_deployment_unsupported_platform(mock_uname, mock_deployment_path):
    """Test launch_deployment raises error for unsupported platforms."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Windows")

    cmd = "bec"
    with pytest.raises(NotImplementedError, match="This function only supports macOS and Linux"):
        launch_deployment(mock_deployment_path, cmd)


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
@mock.patch("subprocess.run")
def test_launch_deployment_with_activate_env_true(
    mock_run, mock_popen, mock_uname, mock_deployment_path
):
    """Test launch_deployment activates virtual environment when activate_env=True."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Darwin")
    mock_run.return_value = mock.Mock(returncode=0)

    cmd = "bec"
    launch_deployment(mock_deployment_path, cmd, activate_env=True)

    # Verify command includes activation
    popen_args = mock_popen.call_args[0][0]
    applescript = popen_args[2]
    assert "source" in applescript
    assert "bec_venv/bin/activate" in applescript
    assert "&&" in applescript
    assert cmd in applescript


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
@mock.patch("subprocess.run")
def test_launch_deployment_with_activate_env_false(
    mock_run, mock_popen, mock_uname, mock_deployment_path
):
    """Test launch_deployment skips activation when activate_env=False."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Darwin")
    mock_run.return_value = mock.Mock(returncode=0)

    cmd = "bec"
    launch_deployment(mock_deployment_path, cmd, activate_env=False)

    # Verify command does not include activation
    popen_args = mock_popen.call_args[0][0]
    applescript = popen_args[2]
    assert "source" not in applescript
    assert "bec_venv/bin/activate" not in applescript
    assert "&&" not in applescript
    assert cmd in applescript


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
@mock.patch("subprocess.run")
def test_launch_deployment_command_escaping(mock_run, mock_popen, mock_uname, mock_deployment_path):
    """Test launch_deployment handles command strings properly."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Darwin")
    mock_run.return_value = mock.Mock(returncode=0)

    # Test with complex command
    cmd = "bec-client --config /path/to/config.yaml"
    launch_deployment(mock_deployment_path, cmd)

    # Verify command is included correctly
    popen_args = mock_popen.call_args[0][0]
    applescript = popen_args[2]
    assert cmd in applescript


@mock.patch("os.uname")
@mock.patch("subprocess.Popen")
def test_launch_deployment_linux_with_activate_env_false(
    mock_popen, mock_uname, mock_deployment_path
):
    """Test launch_deployment on Linux with activate_env=False."""
    # Setup mocks
    mock_uname.return_value = mock.Mock(sysname="Linux")

    cmd = "python script.py"
    launch_deployment(mock_deployment_path, cmd, activate_env=False)

    # Verify Popen was called with gnome-terminal and correct command
    assert mock_popen.called
    popen_args = mock_popen.call_args[0][0]
    full_command = popen_args[-1]
    assert cmd == full_command
    assert "source" not in full_command
