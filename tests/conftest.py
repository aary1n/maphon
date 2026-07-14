"""Test-tier switch (SPEC §1): COMSOL is never assumed available.

Tests marked `requires_comsol` are skipped by default so the synthetic
suite stays green on any host; pass `--comsol` to run them against a
local licence:

    pytest --comsol -m requires_comsol      # COMSOL tier only
    pytest --comsol                         # everything
"""

from __future__ import annotations

from pathlib import Path

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


@pytest.fixture(scope="session", autouse=True)
def calibration_reports_stay_clean():
    """Guard: a test run must not add integrity_failure_* files to the real
    calibration/reports/. Synthetic failure-path tests write to tmp_path; a
    leak here means a reports_dir default has regressed to the repo directory
    (the def-time-bound default did exactly that until 2026-07-14). Deliberate
    committed failure records predating the run are allowed through."""
    reports_dir = Path(__file__).resolve().parent.parent / "calibration" / "reports"
    before = {p.name for p in reports_dir.glob("integrity_failure_*.md")}
    yield
    leaked = {p.name for p in reports_dir.glob("integrity_failure_*.md")} - before
    assert not leaked, (
        "test run leaked integrity-failure reports into calibration/reports/: "
        f"{sorted(leaked)}"
    )


@pytest.fixture(scope="session")
def comsol_client():
    """One shared COMSOL session for the whole --comsol run.

    `mph.start()` is idempotent (one client per process), so sharing a
    session-scoped fixture avoids repeated JVM/server startup.
    """
    mph = pytest.importorskip("mph")
    return mph.start()
