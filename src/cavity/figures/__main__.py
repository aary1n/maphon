"""Regenerate the full figure set: ``python -m cavity.figures``.

Writes docs/figures/<name>.pdf + .png for all six figures. Deterministic
by construction (fixed committed inputs, shared rcParams, no RNG, PDF
CreationDate stripped) — delete-and-regenerate must reproduce the files.
"""

from __future__ import annotations

import argparse
import importlib
from pathlib import Path

from cavity.figures import FIGURE_MODULES


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=None,
        help="output directory (default: docs/figures at repo root)",
    )
    args = parser.parse_args()
    out_dir = Path(args.out) if args.out else None
    for name in FIGURE_MODULES:
        module = importlib.import_module(f"cavity.figures.{name}")
        module.main(out_dir)


if __name__ == "__main__":
    main()
