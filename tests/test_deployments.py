"""
Tests for deployments module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from bec_launcher.deployments import get_available_deployments


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
