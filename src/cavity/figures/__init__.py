"""Publication-grade figure set rendered from EXISTING committed records.

Rendering only — no new physics, no solves, no COMSOL, no thermal or
extraction changes. Inputs are the archived §5a run
(refs/gate_runs/20260710T083340Z_live_comsol/), the byte-pinned margin
report machinery, the SHA-256-pinned Singh raw archive, and the
committed §6T/§7T constants and functions. Caption honesty follows the
`provenance/constants.py` discipline: every applicable SPEC status flag
appears verbatim in its figure's caption; the captions are committed
constants, pinned into docs/supervisor_onepager_2026-07.md by
tests/test_figures.py.

Uniform per-module contract:

- ``CAPTION: str``  — the ratified caption (committed, pinned verbatim);
- ``build_data() -> dict``  — pure, matplotlib-free; everything the
  figure plots;
- ``render(data) -> Figure``  — matplotlib imported lazily under Agg
  with the shared `_style` rcParams;
- ``main()``  — writes ``docs/figures/<name>.pdf`` + ``.png``.

Regenerate all six with ``python -m cavity.figures``; each module also
runs standalone (``python -m cavity.figures.f3_delta_t_map``).
"""

from __future__ import annotations

FIGURE_MODULES = (
    "f1_mode_maps",
    "f2_reproduction_table",
    "f3_delta_t_map",
    "f4_cavity_arm_envelope",
    "f5_margin_waterfall",
    "f6_singh_axis_map",
)
