"""Viz export CLI (viz/PLAN.md §5, Phase 1).

    python -m cavity.viz.export [view ...] [--out viz/data] [--check]

Views: only ``heatmap`` exists in v1 (V2–V5 land in later phases).
On every run the CLI prints the current HEAD SHA and UTC time to
STDOUT — the local-experimentation record (R3), e.g. against a dirty
tree; they are NEVER embedded in a bundle. ``--check`` regenerates the
bundle set in memory, verifies the committed bytes + hashes, and writes
nothing (the CI hook). matplotlib is imported lazily (Agg) ONLY for the
magma LUT export — everything else is matplotlib-free.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from cavity.viz.bundles import build_heatmap_bundles, js_wrapper, unwrap_js

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "viz" / "data"

_VIEWS = ("heatmap",)


def magma_lut() -> np.ndarray:
    """The 256×3 uint8 magma RGB LUT (colormap parity: the same
    `_style.SEQUENTIAL_THERMAL` map F3 renders with, converted by
    matplotlib's own bytes path). Lazy-Agg import — the only matplotlib
    touch in the viz layer."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cavity.figures import _style

    cmap = plt.get_cmap(_style.SEQUENTIAL_THERMAL)
    return cmap(np.arange(256), bytes=True)[:, :3]


def _stdout_record() -> None:
    """R3: SHA/UTC go to stdout only — never into a bundle."""
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
        head = f"{sha}{' (dirty tree)' if dirty else ''}"
    except (OSError, subprocess.CalledProcessError):
        head = "unavailable"
    utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # ASCII-only prints: Windows consoles default to cp1252
    print(f"HEAD {head} at {utc}")
    print("(stdout record only, R3 -- never embedded in bundles)")


def _wrapped_files(built: dict) -> dict[str, bytes]:
    """relative-path → file bytes for the full committed set: every bundle
    as a .js wrapper, plus the plain canonical index.json twin."""
    enc = built["wrapper_encoding"]
    files = {
        f"{name}.js": js_wrapper(name, raw, enc)
        for name, raw in built["canonical"].items()
    }
    files["index.json"] = built["canonical"]["index"]
    return files


def verify_data_dir(built: dict, out_dir: Path) -> list[str]:
    """Compare the on-disk bundle set against a regenerated build; returns
    a list of mismatch messages (empty = verified). Shared by --check and
    tests/test_viz_bundles.py."""
    problems: list[str] = []
    expected = _wrapped_files(built)
    for rel, want in sorted(expected.items()):
        path = out_dir / Path(rel)
        if not path.is_file():
            problems.append(f"missing: {rel}")
            continue
        got = path.read_bytes()
        if rel.endswith(".json"):
            if got != want:
                problems.append(f"canonical bytes differ: {rel}")
        elif unwrap_js(got) != built["canonical"][rel[: -len(".js")]]:
            problems.append(f"wrapped canonical content differs: {rel}")
    on_disk = {
        p.relative_to(out_dir).as_posix()
        for p in out_dir.rglob("*")
        if p.is_file()
    }
    for stray in sorted(on_disk - set(expected)):
        problems.append(f"unexpected file in data dir: {stray}")
    return problems


def _write(built: dict, out_dir: Path) -> None:
    files = _wrapped_files(built)
    for rel, data in sorted(files.items()):
        path = out_dir / Path(rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    total = sum(len(d) for d in files.values())
    canonical_total = sum(len(b) for b in built["canonical"].values())
    print(
        f"wrote {len(files)} files to {out_dir}\n"
        f"canonical JSON total: {canonical_total / 1e6:.3f} MB / "
        f"on-disk total: {total / 1e6:.3f} MB / "
        f"wrapper encoding: {built['wrapper_encoding']} "
        f"(measured gzip saving {built['gzip_saving_frac']:.1%}, "
        f"rule: gzip iff >= 30%)"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cavity.viz.export", description=__doc__
    )
    parser.add_argument(
        "views",
        nargs="*",
        default=["heatmap"],
        help="views to export (v1: heatmap only)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DATA_DIR,
        help="output directory (default: viz/data)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify committed bundles against a regeneration; write nothing",
    )
    args = parser.parse_args(argv)

    for view in args.views:
        if view not in _VIEWS:
            parser.error(
                f"view {view!r} is not built in v1 (available: {', '.join(_VIEWS)};"
                " V2-V5 land in later phases per viz/PLAN.md §6)"
            )

    _stdout_record()
    built = build_heatmap_bundles(magma_lut())

    if args.check:
        problems = verify_data_dir(built, args.out)
        if problems:
            for p in problems:
                print(f"CHECK FAIL {p}")
            return 1
        print(
            f"check OK: {len(_wrapped_files(built))} files verified against "
            f"regeneration (index sha256 {built['sha256']['index']})"
        )
        return 0

    _write(built, args.out)
    print(f"index sha256: {built['sha256']['index']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
