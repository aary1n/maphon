"""Provenance boundary — one-way dependency between calibration/ and cavity/.

The calibration rig is not the maser cavity; its parameters must not leak
into the cavity model. Direction of allowed imports:

    calibration -> cavity   (shared thermal machinery, graded constants)
    cavity -> calibration   (FORBIDDEN)

Enforced by AST inspection of every module on both sides, so a violating
import fails CI even if it is never executed on the tested code path.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CAVITY_DIR = REPO_ROOT / "src" / "cavity"
CALIBRATION_DIR = REPO_ROOT / "calibration"

# The whitelist mirrors the plan's "interfaces to existing thermal machinery"
# section (docs/plans/layer_b_calibration_plan.md): extend it there first.
ALLOWED_CAVITY_IMPORTS = {
    "cavity.thermal.cylinder",
    "cavity.thermal.layered",
    "cavity.thermal.radiation",
    "cavity.provenance",
    "cavity.provenance.constants",
}


def _imported_modules(py_file: Path) -> set[str]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def test_cavity_never_imports_calibration():
    offenders = [
        f"{py_file.relative_to(REPO_ROOT)} imports {mod}"
        for py_file in sorted(CAVITY_DIR.rglob("*.py"))
        for mod in _imported_modules(py_file)
        if mod == "calibration" or mod.startswith("calibration.")
    ]
    assert not offenders, "\n".join(offenders)


def test_calibration_imports_only_whitelisted_cavity_modules():
    offenders = []
    for py_file in sorted(CALIBRATION_DIR.rglob("*.py")):
        for mod in _imported_modules(py_file):
            if mod == "cavity" or mod.startswith("cavity."):
                if mod not in ALLOWED_CAVITY_IMPORTS:
                    offenders.append(f"{py_file.relative_to(REPO_ROOT)} imports {mod}")
    assert not offenders, (
        "non-whitelisted cavity import from calibration/ "
        "(extend the plan's interface list first):\n" + "\n".join(offenders)
    )
