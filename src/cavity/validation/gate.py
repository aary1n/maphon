"""SPEC §5 Phase-1 validation gate — orchestration and judgment.

The §5 table (verbatim text and acceptance windows live in
`cavity.provenance.gate_targets.GATE_ROWS`; every anchor value there
is referenced from `cavity.provenance.constants`, never re-typed):

  - Analytic benchmark passes      empty-cavity TE011 < 0.1% error
  - f                              1.45 GHz, >=4 s.f.
  - Booth two-point                Q ~ 6,980; V_mode vs the corrected
                                   Booth-implied anchor (finding
                                   2026-07-11: the print carries a
                                   225/360 partial-revolution factor)
  - Confinement trend              tightening toward 0.2 raises Q
                                   toward ~10,000; order-1e7 F_m
                                   judged HERE (its Breeze anchor)
  - Wall-loss split                Q_diel 9-10k, wall fraction 23-27%
  - F_m                            ±1% consistency vs BOOTH_IMPLIED_F_M
                                   at the Booth point

Design: the gate CONSUMES payloads from a `SolveProvider`
(`validation.providers`) and never solves anything itself. A payload
present -> the check is judged pass/fail; `Unavailable` -> status
`deferred_requires_comsol` with the provider's reason in the notes.
Synthetic, cached and live providers therefore share this ONE code
path (SPEC §1: CI never assumes a COMSOL licence).

Q convention (SPEC §11 gap #4, resolved 2026-07-02): the gate consumes
`ExtractionResult.q` = f'/(2 f'') from the bare solver `freq`. It
never re-derives Q and never reads imag(emw.freq). The §8 closed check
here calls the existing `assert_pec_lossy_q_consistency` guard — it
does not fork the tolerance or the formula.

Phase 1 complete = all six rows pass (SPEC §5 heading). No Phase 2
work — static or thermal — until `GateReport.phase1_complete` is True.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from cavity.extraction import (
    assert_pec_lossy_q_consistency,
    magnetic_purcell_factor,
)
from cavity.forward_model.persistence import utc_timestamp
from cavity.provenance import EXTRACTION_TOL, TARGET, TARGETS
from cavity.provenance.gate_targets import (
    CONFINEMENT_ENDPOINT_V_MODE_MAX_M3,
    CONFINEMENT_MIN_POINTS,
    GATE_ROWS,
    GateCheckSpec,
    GateRowSpec,
    GateWindow,
)
from cavity.validation.analytic import f_te_mnp
from cavity.validation.providers import (
    BoothPayload,
    ConfinementPayload,
    EmptyCavityPayload,
    PecLossyPayload,
    ReproducibilityMetadata,
    SolveProvider,
    Unavailable,
    WallLossPayload,
)

GATE_REPORT_SCHEMA_VERSION = 1


class CheckStatus(str, Enum):
    """Per-check verdict. `DEFERRED` = the row's input requires a
    COMSOL solve this provider could not supply — not a failure."""

    PASS = "pass"
    FAIL = "fail"
    DEFERRED = "deferred_requires_comsol"


@dataclass(frozen=True)
class GateCheckResult:
    """One judged check: everything needed to audit the verdict.

    `margin` conventions (see `GateWindow`): two-sided windows report
    distance-to-nearest-edge over the half-width (1.0 at centre, 0.0
    at an edge, negative outside); upper-only residual windows report
    headroom (hi - measured)/hi; structural checks report None.

    `inputs` records exactly the numbers the verdict was computed
    from ("inputs-judged-on"), so a report line can be re-derived by
    hand without the payload.
    """

    name: str
    row_id: str
    target: str
    target_value: float | None
    measured: float | None
    window: GateWindow
    status: CheckStatus
    margin: float | None
    inputs: dict
    provenance: str
    tolerance_rationale: str
    notes: str


@dataclass(frozen=True)
class GateRowResult:
    """One §5 row: verbatim table text + its judged checks.

    Row status = worst of its checks (fail > deferred > pass), so a
    row is only green when every one of its checks passed on real
    numbers.
    """

    row_id: str
    check_text: str
    target_text: str
    source_text: str
    status: CheckStatus
    checks: tuple[GateCheckResult, ...]


@dataclass(frozen=True)
class GateReport:
    """Full §5 gate outcome. `phase1_complete` = all six rows PASS."""

    schema_version: int
    created_at_utc: str
    provider_kind: str
    phase1_complete: bool
    n_pass: int
    n_fail: int
    n_deferred: int
    rows: tuple[GateRowResult, ...]
    reproducibility: ReproducibilityMetadata


# --- window arithmetic --------------------------------------------------


def evaluate_window(
    measured: float, window: GateWindow
) -> tuple[CheckStatus, float | None]:
    """Inclusive-bounds verdict + margin per the GateWindow contract."""
    lo, hi = window.lo, window.hi
    if lo is not None and hi is not None:
        inside = lo <= measured <= hi
        half_width = 0.5 * (hi - lo)
        margin = min(measured - lo, hi - measured) / half_width
        return (CheckStatus.PASS if inside else CheckStatus.FAIL), margin
    if hi is not None:
        inside = measured <= hi
        margin = (hi - measured) / hi
        return (CheckStatus.PASS if inside else CheckStatus.FAIL), margin
    if lo is not None:
        inside = measured >= lo
        return (CheckStatus.PASS if inside else CheckStatus.FAIL), None
    raise ValueError("GateWindow must bound at least one side")


def _spec(row: GateRowSpec, check_id: str) -> GateCheckSpec:
    for check in row.checks:
        if check.check_id == check_id:
            return check
    raise KeyError(f"no check {check_id!r} in row {row.row_id!r}")


def _row_spec(row_id: str) -> GateRowSpec:
    for row in GATE_ROWS:
        if row.row_id == row_id:
            return row
    raise KeyError(f"no §5 row {row_id!r}")


def _result(
    spec: GateCheckSpec,
    row: GateRowSpec,
    *,
    measured: float | None,
    status: CheckStatus,
    margin: float | None,
    inputs: dict,
    notes: str,
) -> GateCheckResult:
    return GateCheckResult(
        name=spec.check_id,
        row_id=row.row_id,
        target=spec.description,
        target_value=spec.target_value,
        measured=measured,
        window=spec.window,
        status=status,
        margin=margin,
        inputs=inputs,
        provenance=spec.provenance,
        tolerance_rationale=spec.tolerance_rationale,
        notes=notes,
    )


def _deferred_check(
    spec: GateCheckSpec, row: GateRowSpec, reason: str
) -> GateCheckResult:
    notes = f"deferred: {reason}"
    if row.blocked_on:
        notes += f" [row blocked on: {row.blocked_on}]"
    return _result(
        spec,
        row,
        measured=None,
        status=CheckStatus.DEFERRED,
        margin=None,
        inputs={},
        notes=notes,
    )


def _aggregate(checks: tuple[GateCheckResult, ...]) -> CheckStatus:
    statuses = {c.status for c in checks}
    if CheckStatus.FAIL in statuses:
        return CheckStatus.FAIL
    if CheckStatus.DEFERRED in statuses:
        return CheckStatus.DEFERRED
    return CheckStatus.PASS


def _row(
    row: GateRowSpec, checks: tuple[GateCheckResult, ...]
) -> GateRowResult:
    return GateRowResult(
        row_id=row.row_id,
        check_text=row.check_text,
        target_text=row.target_text,
        source_text=row.source_text,
        status=_aggregate(checks),
        checks=checks,
    )


def _deferred_row(row: GateRowSpec, reason: str) -> GateRowResult:
    return _row(
        row, tuple(_deferred_check(c, row, reason) for c in row.checks)
    )


# --- row evaluators ------------------------------------------------------


def _eval_analytic_row(
    empty: EmptyCavityPayload | Unavailable,
    pec: PecLossyPayload | Unavailable,
) -> GateRowResult:
    row = _row_spec("analytic_benchmark")
    checks: list[GateCheckResult] = []

    te_spec = _spec(row, "analytic_benchmark/te011")
    if isinstance(empty, Unavailable):
        checks.append(_deferred_check(te_spec, row, empty.reason))
    else:
        f_analytic = f_te_mnp(
            0, 1, 1, empty.box_radius_m, empty.box_height_m
        )
        rel_errors = [
            abs(f / f_analytic - 1.0) for f in empty.spectrum_f_real_hz
        ]
        measured = min(rel_errors)
        status, margin = evaluate_window(measured, te_spec.window)
        best = min(
            empty.spectrum_f_real_hz,
            key=lambda f: abs(f / f_analytic - 1.0),
        )
        checks.append(
            _result(
                te_spec,
                row,
                measured=measured,
                status=status,
                margin=margin,
                inputs={
                    "f_analytic_te011_hz": f_analytic,
                    "closest_eigenfrequency_hz": best,
                    "n_spectrum_candidates": len(
                        empty.spectrum_f_real_hz
                    ),
                    "box_radius_m": empty.box_radius_m,
                    "box_height_m": empty.box_height_m,
                },
                notes=(
                    "min relative error over the solved spectrum "
                    "against the closed-form TE011 (x'_01 = 3.8317)"
                ),
            )
        )

    pec_spec = _spec(row, "analytic_benchmark/pec_lossy_q")
    if isinstance(pec, Unavailable):
        checks.append(_deferred_check(pec_spec, row, pec.reason))
    else:
        checks.append(_eval_pec_lossy(pec_spec, row, pec))

    return _row(row, tuple(checks))


def _eval_pec_lossy(
    spec: GateCheckSpec, row: GateRowSpec, payload: PecLossyPayload
) -> GateCheckResult:
    ext = payload.extraction
    tol = EXTRACTION_TOL.q_pec_lossy_rel_tol
    rel_error = abs(ext.q * ext.p_e * payload.tan_delta - 1.0)
    status = CheckStatus.PASS if rel_error < tol else CheckStatus.FAIL
    margin = (tol - rel_error) / tol

    guard_note = ""
    try:
        assert_pec_lossy_q_consistency(ext.q, ext.p_e, payload.tan_delta)
    except (AssertionError, ValueError) as exc:
        status = CheckStatus.FAIL
        guard_note = f" Guard assert_pec_lossy_q_consistency raised: {exc}"

    return _result(
        spec,
        row,
        measured=rel_error,
        status=status,
        margin=margin,
        inputs={
            "q": ext.q,
            "p_e": ext.p_e,
            "tan_delta": payload.tan_delta,
        },
        notes=(
            "margin is numerical-residual headroom on the closed-form "
            "identity Q*p_e*tan_delta = 1 (mesh/extraction residual), "
            "not a statement of Q-convention correctness — the "
            "convention guard is assert_pec_lossy_q_consistency "
            "(invoked here) and the §8 PEC-lossy tests." + guard_note
        ),
    )


def _booth_material_mismatch(payload: BoothPayload) -> str | None:
    expected = TARGETS.booth.epsilon_r_real
    if payload.epsilon_r_real is None:
        return None
    if math.isclose(payload.epsilon_r_real, expected, rel_tol=1e-9):
        return None
    return (
        f"material mismatch: solved at eps_r = "
        f"{payload.epsilon_r_real}, but TARGETS.booth pairs its "
        f"anchors with eps_r = {expected} (pairing a target with the "
        "wrong eps_r chases a phantom ~14 MHz shift — "
        "provenance/constants.py)."
    )


def _eval_booth_anchored_check(
    spec: GateCheckSpec,
    row: GateRowSpec,
    payload: BoothPayload,
    measured: float,
    inputs: dict,
    notes: str,
) -> GateCheckResult:
    status, margin = evaluate_window(measured, spec.window)
    mismatch = _booth_material_mismatch(payload)
    if mismatch is not None:
        status = CheckStatus.FAIL
        notes = f"{notes} {mismatch}".strip()
    if payload.epsilon_r_real is not None:
        inputs = {**inputs, "epsilon_r_real": payload.epsilon_r_real}
    return _result(
        spec,
        row,
        measured=measured,
        status=status,
        margin=margin,
        inputs=inputs,
        notes=notes,
    )


def _eval_f_row(payload: BoothPayload | Unavailable) -> GateRowResult:
    row = _row_spec("f")
    spec = _spec(row, "f/f_at_booth_geometry")
    if isinstance(payload, Unavailable):
        return _deferred_row(row, payload.reason)
    ext = payload.extraction
    return _row(
        row,
        (
            _eval_booth_anchored_check(
                spec,
                row,
                payload,
                measured=ext.f_hz,
                inputs={"f_hz": ext.f_hz},
                notes=(
                    "judged on the walls-on Booth-geometry "
                    "extraction; convergence to 4 s.f. is the §2 "
                    "mesh study's assertion, presupposed here."
                ),
            ),
        ),
    )


def _eval_booth_row(payload: BoothPayload | Unavailable) -> GateRowResult:
    row = _row_spec("booth_two_point")
    if isinstance(payload, Unavailable):
        return _deferred_row(row, payload.reason)
    ext = payload.extraction
    q_check = _eval_booth_anchored_check(
        _spec(row, "booth_two_point/q"),
        row,
        payload,
        measured=ext.q,
        inputs={"q": ext.q, "f_hz": ext.f_hz},
        notes="Q = f'/(2 f'') from the §3 extraction (never re-derived).",
    )
    v_check = _eval_booth_anchored_check(
        _spec(row, "booth_two_point/v_mode"),
        row,
        payload,
        measured=ext.v_mode_global_m3,
        inputs={
            "v_mode_global_m3": ext.v_mode_global_m3,
            "v_mode_local_m3": ext.v_mode_local_m3,
        },
        notes=(
            "judged on the global-max variant; local variant "
            "recorded for diagnosis (SPEC §3 reports both)."
        ),
    )
    return _row(row, (q_check, v_check))


def _eval_confinement_row(
    payload: ConfinementPayload | Unavailable,
) -> GateRowResult:
    row = _row_spec("confinement_trend")
    if isinstance(payload, Unavailable):
        return _deferred_row(row, payload.reason)

    mono_spec = _spec(row, "confinement_trend/monotonic")
    end_spec = _spec(row, "confinement_trend/endpoint_q")
    fm_spec = _spec(row, "confinement_trend/f_m_order")

    # Loose -> tight confinement (descending V_mode).
    pts = sorted(payload.points, key=lambda p: -p.v_mode_m3)
    inputs = {
        "n_points": len(pts),
        "v_mode_m3": [p.v_mode_m3 for p in pts],
        "q": [p.q for p in pts],
    }

    if len(pts) < CONFINEMENT_MIN_POINTS:
        note = (
            f"only {len(pts)} point(s): SPEC §5 demands a continuous "
            f"trend, not two unrelated points (need >= "
            f"{CONFINEMENT_MIN_POINTS})."
        )
        checks = tuple(
            _result(
                spec,
                row,
                measured=None,
                status=CheckStatus.FAIL,
                margin=None,
                inputs=inputs,
                notes=note,
            )
            for spec in (mono_spec, end_spec, fm_spec)
        )
        return _row(row, checks)

    deltas = [b.q - a.q for a, b in zip(pts, pts[1:])]
    min_delta = min(deltas)
    mono_check = _result(
        mono_spec,
        row,
        measured=min_delta,
        status=(
            CheckStatus.PASS if min_delta > 0.0 else CheckStatus.FAIL
        ),
        margin=None,
        inputs=inputs,
        notes=(
            "strictly monotone requirement: every Q increment as "
            "V_mode tightens must be > 0 (no numeric margin — "
            "structural check)."
        ),
    )

    endpoint = pts[-1]
    status, margin = evaluate_window(endpoint.q, end_spec.window)
    notes = "Q at the tightest sampled V_mode."
    if endpoint.v_mode_m3 > CONFINEMENT_ENDPOINT_V_MODE_MAX_M3:
        status = CheckStatus.FAIL
        notes += (
            f" Sweep did not reach the Breeze confinement point: "
            f"tightest V_mode = {endpoint.v_mode_m3} m^3 > "
            f"{CONFINEMENT_ENDPOINT_V_MODE_MAX_M3} m^3."
        )
    end_check = _result(
        end_spec,
        row,
        measured=endpoint.q,
        status=status,
        margin=margin,
        inputs={**inputs, "endpoint_v_mode_m3": endpoint.v_mode_m3},
        notes=notes,
    )

    # order-1e7 F_m judged at the confinement endpoint — its Breeze
    # anchor lives at V ~ 0.2 cm^3, not at Booth's ~0.65 cm^3 point
    # (re-scoped 2026-07-11; the Booth point carries the tighter ±1%
    # f_m/booth_consistency check instead).
    endpoint_f_m = magnetic_purcell_factor(
        endpoint.q, endpoint.v_mode_m3, TARGET.f_design_hz
    )
    fm_status, fm_margin = evaluate_window(endpoint_f_m, fm_spec.window)
    fm_check = _result(
        fm_spec,
        row,
        measured=endpoint_f_m,
        status=fm_status,
        margin=fm_margin,
        inputs={
            **inputs,
            "endpoint_v_mode_m3": endpoint.v_mode_m3,
            "endpoint_q": endpoint.q,
            "f_hz": TARGET.f_design_hz,
        },
        notes=(
            "F_m via the §3 formula at the tightest sampled point; "
            "f = TARGET.f_design_hz (the §5 trend row holds the "
            "1.45 GHz design point by construction)."
        ),
    )
    return _row(row, (mono_check, end_check, fm_check))


def _eval_wall_loss_row(
    payload: WallLossPayload | Unavailable,
) -> GateRowResult:
    row = _row_spec("wall_loss_split")
    if isinstance(payload, Unavailable):
        return _deferred_row(row, payload.reason)
    d = payload.decomposition
    inputs = {
        "q_total": d.q_total,
        "q_diel": d.q_diel,
        "q_wall": d.q_wall,
        "sigma_q_wall": d.sigma_q_wall,
        "wall_fraction": d.wall_fraction,
        "below_resolution": d.below_resolution,
    }

    q_spec = _spec(row, "wall_loss_split/q_diel")
    q_status, q_margin = evaluate_window(d.q_diel, q_spec.window)
    q_check = _result(
        q_spec,
        row,
        measured=d.q_diel,
        status=q_status,
        margin=q_margin,
        inputs=inputs,
        notes=(
            "Q_diel is the PEC-solve Q directly (closed cavity); "
            "unaffected by the reciprocal-subtraction cancellation."
        ),
    )

    f_spec = _spec(row, "wall_loss_split/wall_fraction")
    f_status, f_margin = evaluate_window(d.wall_fraction, f_spec.window)
    notes = "wall fraction = Q_total / Q_wall from the §4 decomposition."
    if d.below_resolution:
        f_status = CheckStatus.FAIL
        notes += (
            " Decomposition is below_resolution: sigma(Q_wall)/Q_wall "
            "exceeds the §4 threshold, so the split is not resolved — "
            "at the Booth regime (~25% wall fraction) it must be."
        )
    f_check = _result(
        f_spec,
        row,
        measured=d.wall_fraction,
        status=f_status,
        margin=f_margin,
        inputs=inputs,
        notes=notes,
    )
    return _row(row, (q_check, f_check))


def _eval_f_m_row(payload: BoothPayload | Unavailable) -> GateRowResult:
    # Booth-point F_m = ±1% consistency vs BOOTH_IMPLIED_F_M (finding
    # 2026-07-11): the old [1e7, 1e8) order window here was satisfiable
    # only through the x1.6-inflated V_mode print, and replacing an
    # order-of-magnitude window with a 1% consistency check is a
    # TIGHTENING — the order-1e7 physics window now lives at the
    # confinement endpoint (its Breeze anchor), deferred with that row.
    row = _row_spec("f_m")
    spec = _spec(row, "f_m/booth_consistency")
    if isinstance(payload, Unavailable):
        return _deferred_row(row, payload.reason)
    ext = payload.extraction
    return _row(
        row,
        (
            _eval_booth_anchored_check(
                spec,
                row,
                payload,
                measured=ext.f_m_global,
                inputs={
                    "f_m_global": ext.f_m_global,
                    "f_m_local": ext.f_m_local,
                    "q": ext.q,
                    "v_mode_global_m3": ext.v_mode_global_m3,
                    "f_hz": ext.f_hz,
                },
                notes=(
                    "±1% consistency vs the Booth-implied F_m anchor "
                    "(§3 formula at printed Q, corrected V, 1.45 GHz); "
                    "judged on the global-max V_mode variant (the "
                    "conservative, smaller-F_m choice); local "
                    "variant recorded for diagnosis."
                ),
            ),
        ),
    )


# --- orchestration --------------------------------------------------------


def run_gate(provider: SolveProvider) -> GateReport:
    """Run all six §5 rows against one provider and aggregate.

    The Booth walls-on payload is fetched ONCE and shared by the f,
    Booth two-point and F_m rows — the three collapse together to
    point-checks when Booth's .mph lands. `reproducibility()` is
    called last so live providers report the solves that actually
    ran.
    """
    booth = provider.booth_walls_on()
    rows = (
        _eval_analytic_row(provider.empty_cavity(), provider.pec_lossy()),
        _eval_f_row(booth),
        _eval_booth_row(booth),
        _eval_confinement_row(provider.confinement_trend()),
        _eval_wall_loss_row(provider.wall_loss_split()),
        _eval_f_m_row(booth),
    )
    statuses = [r.status for r in rows]
    return GateReport(
        schema_version=GATE_REPORT_SCHEMA_VERSION,
        created_at_utc=utc_timestamp(),
        provider_kind=provider.kind,
        phase1_complete=all(s is CheckStatus.PASS for s in statuses),
        n_pass=sum(s is CheckStatus.PASS for s in statuses),
        n_fail=sum(s is CheckStatus.FAIL for s in statuses),
        n_deferred=sum(s is CheckStatus.DEFERRED for s in statuses),
        rows=rows,
        reproducibility=provider.reproducibility(),
    )


__all__ = [
    "GATE_REPORT_SCHEMA_VERSION",
    "CheckStatus",
    "GateCheckResult",
    "GateReport",
    "GateRowResult",
    "evaluate_window",
    "run_gate",
]
