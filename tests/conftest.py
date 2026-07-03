"""Test-tier switch (SPEC §1): COMSOL is never assumed available.

Tests marked `requires_comsol` are skipped by default so the synthetic
suite stays green on any host; pass `--comsol` to run them against a
local licence:

    pytest --comsol -m requires_comsol      # COMSOL tier only
    pytest --comsol                         # everything
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--comsol",
        action="store_true",
        default=False,
        help="run tests that need MPh + a local COMSOL licence",
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--comsol"):
        return
    skip = pytest.mark.skip(
        reason="needs --comsol and a local COMSOL licence (SPEC §1)"
    )
    for item in items:
        if "requires_comsol" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def comsol_client():
    """One shared COMSOL session for the whole --comsol run.

    `mph.start()` is idempotent (one client per process), so sharing a
    session-scoped fixture avoids repeated JVM/server startup.
    """
    mph = pytest.importorskip("mph")
    return mph.start()
