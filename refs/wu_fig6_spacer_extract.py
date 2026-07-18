"""Wu 2020 PRA 14, 064017 Fig. 6 — vector extraction of the overlay paths.

Companion record: refs/wu_fig6_spacer_digitization.md (regenerate its
numbers by re-running this script; never hand-edit the values there).

The three coloured outlines in Fig. 6 (p. 064017-6) are vector paths in
the PDF, not raster content: cyan = STO ring cross-section (the
calibration object — its r and z extents are literature prints), red =
the cross-linked-polystyrene spacer, magenta = the crystal as drawn in
Wu's own simulation. This script re-derives the spacer fields of
`cavity.provenance.constants.WuSTORingGeometry` from the archived
primary-source PDF and exits non-zero if any derived value disagrees
with the committed constant (house rule: scoping numbers are computed
and re-fittable, never eyeballed).

Calibration knowns (all literature prints, independent of the spacer
values being derived): r maps via the cyan rectangle's x-extent to
sto_inner_radius..sto_outer_radius; z maps via its y-extent to
deck_clearance..deck_clearance + height, computed for BOTH branches of
the Q13 height fork {8.5, 8.6} mm. Derived dimensions are rounded to
0.1 mm and must agree across the two branches; the grade on every
derived number is FIGURE-DERIVED +/- ~0.3 mm (the overlays are
hand-placed annotations with a ~2-3% y/x aspect mismatch vs the printed
ring dims — reported below).

Run from anywhere:  python refs/wu_fig6_spacer_extract.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz  # PyMuPDF

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from cavity.provenance import GEOM_WU_STO_RING, STO_HEIGHT_FORK  # noqa: E402

PDF = (
    _REPO_ROOT
    / "calibration/data/raw/wu_build_papers_2026-07-18/wu2020_pra_14_064017.pdf"
)

# Fig. 6 overlay stroke colours as authored in the PDF (RGB, 0..1).
COLOURS = {
    "cyan_sto": (0.0, 1.0, 1.0),
    "red_spacer": (1.0, 0.0, 0.0),
    "magenta_crystal": (1.0, 0.416, 0.973),
}
COLOUR_TOL = 0.15


def _find_fig6_page(doc: fitz.Document) -> fitz.Page:
    for page in doc:
        if "FIG. 6" in page.get_text():
            return page
    raise SystemExit("STOP: no page containing 'FIG. 6' found in the PDF")


def _coloured_paths(page: fitz.Page) -> dict[str, dict]:
    """Exactly one stroke path per overlay colour, else STOP."""
    found: dict[str, list[dict]] = {name: [] for name in COLOURS}
    for d in page.get_drawings():
        col = d.get("color")
        if col is None:
            continue
        for name, ref in COLOURS.items():
            if all(abs(c - r) <= COLOUR_TOL for c, r in zip(col, ref)):
                found[name].append(d)
    bad = {n: len(ps) for n, ps in found.items() if len(ps) != 1}
    if bad:
        raise SystemExit(f"STOP: expected exactly one path per colour, got {bad}")
    return {n: ps[0] for n, ps in found.items()}


def _polyline_points(drawing: dict) -> list[tuple[float, float]]:
    """Ordered vertex list of a line-segment path ('l' items)."""
    pts: list[tuple[float, float]] = []
    for item in drawing["items"]:
        if item[0] != "l":
            raise SystemExit(f"STOP: unexpected path item {item[0]!r} in spacer path")
        p1, p2 = item[1], item[2]
        if not pts:
            pts.append((p1.x, p1.y))
        pts.append((p2.x, p2.y))
    return pts


def main() -> None:
    g = GEOM_WU_STO_RING
    doc = fitz.open(PDF)
    page = _find_fig6_page(doc)
    paths = _coloured_paths(page)

    # --- calibration from the cyan STO rectangle (literature prints) ---
    (kind, cyan_rect) = paths["cyan_sto"]["items"][0][0], paths["cyan_sto"]["items"][0][1]
    if kind != "re":
        raise SystemExit("STOP: cyan STO path is not a rectangle")
    r_in_mm = g.sto_inner_radius_m * 1e3   # 2.025 (print)
    r_out_mm = g.sto_outer_radius_m * 1e3  # 6.0  (print)
    deck_mm = g.deck_clearance_m * 1e3     # 3.0  (print)
    sx = (cyan_rect.x1 - cyan_rect.x0) / (r_out_mm - r_in_mm)  # pt per mm (radial)

    def r_of(x: float) -> float:
        return r_in_mm + (x - cyan_rect.x0) / sx

    branches: dict[float, dict] = {}
    for h_m in STO_HEIGHT_FORK.candidates:
        h_mm = h_m * 1e3
        sy = (cyan_rect.y1 - cyan_rect.y0) / h_mm  # pt per mm (axial; y down)

        def z_of(y: float) -> float:
            return deck_mm + (cyan_rect.y1 - y) / sy

        verts = [(r_of(x), z_of(y)) for x, y in _polyline_points(paths["red_spacer"])]
        rs = sorted({round(r, 3) for r, _ in verts})
        zs = sorted({round(z, 3) for _, z in verts})
        mag = paths["magenta_crystal"]["items"][0][1]  # crystal rectangle
        branches[h_mm] = {
            "aspect_pct": (sy / sx - 1.0) * 100.0,
            "verts": verts,
            # radial stations of the stepped seat (branch-independent):
            "base_inner": rs[0],
            "lip_inner": rs[1],
            "base_outer": rs[2],
            # axial stations: base bottom, seat top (ring underside), lip top
            "base_bottom": zs[0],
            "seat_top": max(z for _, z in verts if z < deck_mm + 1.0),
            "lip_top": zs[-1],
            "crystal": (
                r_of(mag.x0),
                r_of(mag.x1),
                z_of(mag.y1),
                z_of(mag.y0),
            ),
        }

    # --- report ---
    print(f"source: {PDF.name}  (Fig. 6, page index {page.number})")
    print(f"radial scale: {sx:.4f} pt/mm (cyan x-extent over the printed radii)")
    for h_mm, b in branches.items():
        print(f"\n-- height branch {h_mm:.1f} mm "
              f"(y/x aspect mismatch {b['aspect_pct']:+.1f}%) --")
        print("  red spacer vertices (r, z) mm: "
              + " -> ".join(f"({r:.2f}, {z:.2f})" for r, z in b["verts"]))
        print(f"  base annulus r {b['base_inner']:.2f}..{b['base_outer']:.2f}, "
              f"z {b['base_bottom']:.2f}..{b['seat_top']:.2f}")
        print(f"  lip r {b['lip_inner']:.2f}..{b['base_outer']:.2f}, "
              f"top z {b['lip_top']:.2f} "
              f"(height above ring underside {b['lip_top'] - deck_mm:.2f})")
        c = b["crystal"]
        print(f"  magenta crystal r {c[0]:.2f}..{c[1]:.2f}, z {c[2]:.2f}..{c[3]:.2f}")

    # --- derived values (0.1 mm rounding), stable across the fork ---
    def stable(key_fn) -> float:
        vals = {round(key_fn(b), 1) for b in branches.values()}
        if len(vals) != 1:
            raise SystemExit(f"STOP: fork branches disagree after rounding: {vals}")
        return vals.pop()

    derived = {
        "spacer_base_inner_radius_m": stable(lambda b: b["base_inner"]),
        "spacer_base_outer_radius_m": stable(lambda b: b["base_outer"]),
        "spacer_lip_inner_radius_m": stable(lambda b: b["lip_inner"]),
        "spacer_lip_outer_radius_m": stable(lambda b: b["base_outer"]),
        "spacer_lip_height_m": stable(lambda b: b["lip_top"] - deck_mm),
    }
    # The base HEIGHT is the seat identification, not a drawn span: the ring
    # underside sits on the seat top, so the base occupies the full deck
    # clearance. Checkable from the figure: the seat top must round to the
    # printed 3.0 mm deck clearance. The drawn base bottom floats ~0.1-0.2 mm
    # above the deck (hand-placed-annotation slop, within the +/-0.3 grade)
    # and the SM's sub-deck "post ... into a hole in the PCB" is unmodelled.
    seat_top = stable(lambda b: b["seat_top"])
    bottoms = sorted(round(b["base_bottom"], 2) for b in branches.values())
    print(f"\nseat top (rounded): {seat_top} mm  "
          f"[must equal printed deck clearance {deck_mm:.1f}]")
    print(f"drawn base bottom: {bottoms[0]:.2f}..{bottoms[-1]:.2f} mm above the "
          f"deck plane across the fork branches [annotation slop, within the "
          f"+/-0.3 grade; recorded, not a derived constant]")

    failures = []
    if seat_top != round(deck_mm, 1):
        failures.append(f"seat top {seat_top} != deck clearance {deck_mm:.1f}")
    if g.spacer_base_height_m != g.deck_clearance_m:
        failures.append("spacer_base_height_m != deck_clearance_m (seat identity)")
    print(f"\n{'field':32s} {'derived mm':>10s} {'constant mm':>12s}")
    for field, mm in derived.items():
        const_mm = round(getattr(g, field) * 1e3, 6)
        ok = abs(mm - const_mm) < 1e-9
        print(f"{field:32s} {mm:>10.1f} {const_mm:>12.1f} {'ok' if ok else 'MISMATCH'}")
        if not ok:
            failures.append(f"{field}: derived {mm} vs constant {const_mm}")

    if failures:
        print("\nSTOP: re-extracted values disagree with provenance constants:")
        for f in failures:
            print("  -", f)
        raise SystemExit(1)
    print("\nPASS: all spacer constants match the re-extracted Fig. 6 values.")


if __name__ == "__main__":
    main()
