"""
Simple helpers for fetching available deployments.
"""

from __future__ import annotations

import os
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
        if item.endswith("deployments") or item.startswith("old"):
            continue

        # If the item starts with "test_", add to test deployments
        if item.startswith("test"):
            out["test"].append(item)
        else:
            out["production"].append(item)

    return out
