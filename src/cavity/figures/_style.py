"""Shared rendering style for the figure set (rendering only — no physics).

One rcParams source for all six figures so the set reads as one system:
serif text with STIX mathtext (LaTeX-adjacent, NO usetex — regeneration
must be machine-independent), colourblind-safe perceptually-uniform
sequential maps (viridis for EM fields, magma for temperature), a small
validated categorical palette for multi-series line work, and a muted
provenance footer on every figure.

Provenance-footer discipline (same rule as `provenance/constants.py`
caption honesty): the footer stamps the identity of the figure's INPUTS
— archive run dir / record hash / archive commit from the committed
manifest, or the committed constants and SHA-256-pinned raw files —
NEVER the render-time clock or the render-time git commit. Output is
deterministic: regenerating from an unchanged repo must reproduce the
files (PDF metadata `CreationDate` is stripped for the same reason).

matplotlib is imported lazily here and only under the Agg backend (the
`report_3a.py` precedent); `build_data()` in the figure modules must
never import this module's matplotlib-touching functions.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIGURES_DIR = REPO_ROOT / "docs" / "figures"

# Categorical palette (dataviz-validated subset, light surface: lightness
# band, chroma floor, CVD separation and 3:1 contrast all PASS; fixed
# slot order, never cycled).
BLUE = "#2a78d6"     # slot 1 — primary series
ORANGE = "#eb6834"   # slot 2 — secondary series
VIOLET = "#4a3aa7"   # slot 3 — tertiary series
GREEN = "#008300"    # slot 4 — quaternary series
FAIL_RED = "#e34948"     # reserved status colour — FAIL rows only
INK = "#0b0b0b"          # primary text
INK_MUTED = "#52514e"    # secondary text / footers
GRID = "#d9d8d4"         # recessive gridlines
BAND_GREY = "#c8c7c2"    # neutral band fill

SEQUENTIAL_FIELD = "viridis"   # F1 |E|, |H| magnitude maps
SEQUENTIAL_THERMAL = "magma"   # F3 delta-T map


def apply_style() -> None:
    """Apply the shared rcParams (Agg backend, serif + STIX, no usetex)."""
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams.update(
        {
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["DejaVu Serif"],  # ships with matplotlib
            "mathtext.fontset": "stix",
            "font.size": 9.0,
            "axes.titlesize": 10.0,
            "axes.labelsize": 9.0,
            "xtick.labelsize": 8.0,
            "ytick.labelsize": 8.0,
            "legend.fontsize": 8.0,
            "axes.edgecolor": INK_MUTED,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK_MUTED,
            "ytick.color": INK_MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "lines.linewidth": 2.0,
            "legend.frameon": False,
            "figure.dpi": 100,
            "savefig.dpi": 300,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def provenance_footer(fig, text: str) -> None:
    """Stamp the input-identity footer (archive/constants — never the clock).

    Reserves a bottom band from the constrained-layout engine (when one
    is active) so the footer never collides with axis labels.
    """
    engine = fig.get_layout_engine()
    if engine is not None and hasattr(engine, "set"):
        engine.set(rect=(0.0, 0.06, 1.0, 0.94))
    fig.text(
        0.5,
        0.002,
        text,
        ha="center",
        va="bottom",
        fontsize=6.0,
        color=INK_MUTED,
        wrap=True,
    )


def save_figure(fig, stem: str, out_dir: Path | None = None) -> list[Path]:
    """Write `<stem>.pdf` + `<stem>.png`, deterministically.

    PDF `CreationDate` is stripped so byte content depends only on the
    figure, not the render clock (the footer discipline, enforced at the
    file level).
    """
    out = FIGURES_DIR if out_dir is None else Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext, meta in (
        (".pdf", {"CreationDate": None}),
        (".png", None),
    ):
        path = out / f"{stem}{ext}"
        fig.savefig(path, metadata=meta, bbox_inches="tight")
        paths.append(path)
    return paths
