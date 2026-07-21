"""Presentation-layer bundle exporters (viz/PLAN.md — ratified 2026-07-21).

Rendering only — presentation layer, NOT evidence (the `cavity.figures`
bright line, restated as binding): no new physics, no solves in the
COMSOL sense, no thermal or extraction changes. Never in the claims
register, never referenced by `publication.build`, can never alter a
claim grade.

Bundles re-package committed-constant closed-form solves and committed
records through the figure-module contract; every number in a bundle
traces to a committed function or constant, and every status-flag
string is a committed `captions.py` token sourced verbatim from a
figure CAPTION (R4) — never retyped inline. Header discipline (R3):
bundles stamp INPUT identity only — never the render-time clock, never
the git HEAD; the export CLI prints SHA/UTC to stdout as the
local-experimentation record. Deterministic bytes: regenerating from an
unchanged repo must reproduce every bundle bit-for-bit (the hash-pin
substrate, `tests/test_viz_bundles.py`).
"""

from __future__ import annotations
