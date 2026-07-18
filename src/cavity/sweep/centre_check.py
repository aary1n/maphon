"""L5 sweep-centre verification block — design doc §1 Phase 1b rider.

The pinned centre is IMPORT-ONLY (gate record 823e67969516bcf2,
refs/gate_runs/20260711T132705Z_rejudge/): no quantity here is
re-derived, and the pin test re-reads the record and asserts equality.
Sweep-centre definition, verbatim from the design doc:

    the Phase 1b model whose no-crystal limit reproduces the pinned
    gate-record values.

(Wording updated 2026-07-16 with the Q9 reframe — formerly the
ratified "no-bore/no-crystal limit": the recovered Booth geometry
contains a torus central opening, often termed the bore, but no
separately constructed or independently parameterised bore, so the
no-crystal limit is the same statement.)

BUILD MISMATCH, recorded 2026-07-18 (geometry re-base; no logic
change): the pinned record 823e67969516bcf2 is a BOOTH-BUILD gate
record, while the Layer-A sweep now runs on the Wu ring
(GEOM_WU_STO_RING). No Wu-build gate record exists yet — producing one
(and re-basing this centre definition onto it) is queued
licence-session work behind the W2 acceptance-window ratification. The
Booth pins stay import-only and untouched: they remain correct AS the
§5a anchor record; they no longer describe the sweep centre's build.

The §6 verification block is itemised exactly: (crystal ON/OFF at
nominal) × 2 mesh levels = 4, + 1 PEC arm (crystal ON, wall-split
diagnostic) = 5 solves — the draft's "6" over-counted by one.

GATES (enforced in code): the block cannot RUN until Q9 (crystal
placement) and Q11 (crystal εr — the repo carries only a bound) resolve with
non-mock resolutions; and even then the ComsolBackend refuses Phase 1b
specs until the SPEC §5b geometry pass exists. Mock-shape exercise goes
through `centre_verification_specs` with `mock_resolutions()`.

JUDGMENT (rider R2, ratified 2026-07-15): the "perturbs the pinned
centre only weakly" acceptance window is UNPINNED — named ratification
item W1, queued WITH Q9 + Q11 (due the moment both resolve, not after
them). Until W1 ratifies, this module reports deltas and REFUSES any
PASS/FAIL judgment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.provenance import DELOAD_K
from cavity.sweep.backend import (
    SWEEP_MESH_COARSER,
    SWEEP_MESH_FINEST,
    SWEEP_STUDY,
    SolveBackend,
)
from cavity.sweep.dofs import (
    MockResolutionError,
    ResolutionContext,
    SENTINEL_W1,
    UnresolvedTodoTraceError,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]

GATE_RUN_DIR = _REPO_ROOT / "refs" / "gate_runs" / "20260711T132705Z_rejudge"
GATE_RECORD_HASH = "823e67969516bcf2"

#: Manifest path of the canonical-branch record the constants below are
#: imported from (verified by tests/test_sweep_centre_check.py).
_CANONICAL_ARM_KEYS = ("branches", "canonical", "arms", "impedance", "finest")


@dataclass(frozen=True)
class PinnedCentre:
    """Import-only canonical-branch anchor values (§5a re-based GREEN).

    Full-precision values from the rejudge record's canonical impedance
    arm; the design doc's §1 citation (Q₀ = 6764.5852, p_e = 0.99750)
    is these values at print precision. Q_L = Q₀/(1+k), k = DELOAD_K —
    a convention application, not a re-derivation.
    """

    record_hash: str = GATE_RECORD_HASH
    q0: float = 6764.585235432756
    p_e: float = 0.9974999896719232
    f_hz: float = 1450382241.9771147

    @property
    def q_l(self) -> float:
        return self.q0 / (1.0 + DELOAD_K)


PINNED_CENTRE = PinnedCentre()

#: Verbatim sweep-centre definition (design doc §1 rider; wording
#: updated 2026-07-16 with the Q9 reframe — formerly
#: "no-bore/no-crystal limit").
SWEEP_CENTRE_DEFINITION = (
    "the Phase 1b model whose no-crystal limit reproduces the "
    "pinned gate-record values (record 823e67969516bcf2); no "
    "re-derivation of the centre is performed or permitted"
)


def read_gate_record_values() -> dict:
    """Re-read the canonical arm of the rejudge manifest (pin test)."""
    manifest = json.loads(
        (GATE_RUN_DIR / "checkpoint_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    node = manifest
    for key in _CANONICAL_ARM_KEYS:
        node = node[key]
    return {
        "record_hash": node["record_hash"],
        "q": node["q"],
        "p_e": node["p_e"],
        "f_hz": node["f_hz"],
    }


# ---------------------------------------------------------------------------
# The 5-solve verification block
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CentreVerificationSpec:
    """One of the five §6 verification solves (descriptor only — the
    Phase 1b geometry it describes has no engine yet, SPEC §5b)."""

    label: str
    crystal_on: bool
    mesh_level: str  # "finest" | "coarser"
    wall_bc: WallBC
    crystal_axial_offset_m: float
    crystal_epsilon_r: float

    @property
    def study(self) -> EigenStudyConfig:
        from dataclasses import replace

        return replace(SWEEP_STUDY, wall_bc=self.wall_bc)

    @property
    def mesh(self):
        return (
            SWEEP_MESH_FINEST
            if self.mesh_level == "finest"
            else SWEEP_MESH_COARSER
        )


def _require_questions(
    context: ResolutionContext,
    questions: tuple[str, ...],
    what: str,
    *,
    allow_mock: bool,
) -> None:
    missing = tuple(
        q for q in questions if context.get(q) is None
    )
    if missing:
        raise UnresolvedTodoTraceError(missing, what)
    if not allow_mock:
        mocked = tuple(
            q
            for q in questions
            if context.get(q) is not None and context.get(q).mock
        )
        if mocked:
            raise MockResolutionError(
                f"{what} refused — question(s) {list(mocked)} carry "
                "MOCK resolutions; the centre verification burns "
                "licence and can never run on test doubles"
            )


def centre_verification_specs(
    context: ResolutionContext,
) -> tuple[CentreVerificationSpec, ...]:
    """The itemised 5-solve block (4 + 1 PEC arm).

    Needs Q9 + Q11 resolutions (mock allowed — this only builds
    DESCRIPTORS for shape exercise; running them is separately gated).
    The PEC arm solves at the finest level (wall-split diagnostic
    pairing with the finest impedance arm; the level pairing is an
    implementation choice stated here, not a committed §6 quantity).
    """
    _require_questions(
        context,
        ("Q9", "Q11"),
        "centre-verification spec construction",
        allow_mock=True,
    )
    offset = float(
        context.get("Q9").payload["crystal_axial_offset_nominal_m"]
    )
    eps = float(context.get("Q11").payload["crystal_epsilon_r"])

    def spec(label, on, level, wall):
        return CentreVerificationSpec(
            label=label,
            crystal_on=on,
            mesh_level=level,
            wall_bc=wall,
            crystal_axial_offset_m=offset,
            crystal_epsilon_r=eps,
        )

    return (
        spec("phase1b_on_finest", True, "finest", WallBC.IMPEDANCE),
        spec("phase1b_off_finest", False, "finest", WallBC.IMPEDANCE),
        spec("phase1b_on_coarser", True, "coarser", WallBC.IMPEDANCE),
        spec("phase1b_off_coarser", False, "coarser", WallBC.IMPEDANCE),
        spec("phase1b_on_pec_wall_split", True, "finest", WallBC.PEC),
    )


def run_centre_verification(
    backend: SolveBackend, context: ResolutionContext
) -> None:
    """The REAL block — strictly gated; unreachable this pass.

    Refuses on unresolved Q9/Q11, refuses mock resolutions, and (once
    both pass) still refuses because the Phase 1b geometry engine does
    not exist (SPEC §5b — a separate licensed pass builds the crystal
    sub-domain; this module must not).
    """
    _require_questions(
        context,
        ("Q9", "Q11"),
        "centre verification run",
        allow_mock=False,
    )
    raise NotImplementedError(
        "centre verification cannot run: the axisymmetric geometry "
        "engine has no crystal sub-domain — building it is the "
        "SPEC §5b Phase 1b pass, not licensed by the Layer A design "
        f"doc. Sweep-centre definition on record: {SWEEP_CENTRE_DEFINITION}"
    )


# ---------------------------------------------------------------------------
# Reporting — deltas only; judgment refused until W1 ratifies
# ---------------------------------------------------------------------------


def centre_verification_report(
    off_arm_finest: dict, on_arm_finest: dict
) -> dict:
    """Deltas of the Phase 1b additions against the pinned centre.

    Inputs are summary-shaped dicts (f_real_hz, q, p_e) for the finest
    impedance arms. Returns deltas + an UNJUDGED verdict: the W1
    acceptance window is TODO-trace (rider R2 — queued with Q9 + Q11).
    """
    pinned = PINNED_CENTRE
    return {
        "pinned_centre": {
            "record_hash": pinned.record_hash,
            "q0": pinned.q0,
            "p_e": pinned.p_e,
            "f_hz": pinned.f_hz,
            "import_only": True,
        },
        "off_arm_vs_pinned": {
            "delta_f_hz": off_arm_finest["f_real_hz"] - pinned.f_hz,
            "delta_q0_rel": off_arm_finest["q"] / pinned.q0 - 1.0,
            "delta_p_e": off_arm_finest["p_e"] - pinned.p_e,
            "meaning": (
                "the no-crystal limit must reproduce the "
                "pinned values (sweep-centre definition)"
            ),
        },
        "phase1b_perturbation": {
            "delta_f_hz": (
                on_arm_finest["f_real_hz"] - off_arm_finest["f_real_hz"]
            ),
            "delta_q0_rel": on_arm_finest["q"] / off_arm_finest["q"] - 1.0,
            "delta_p_e": on_arm_finest["p_e"] - off_arm_finest["p_e"],
            "meaning": (
                "SPEC §5b: 'Booth argues it barely perturbs the mode; "
                "verify, don't assume'"
            ),
        },
        "judgment": {
            "status": "UNJUDGED",
            "window": None,
            "window_sentinel": SENTINEL_W1.question_id,
            "reason": SENTINEL_W1.description,
            "due": SENTINEL_W1.routes_to,
        },
    }


def judge_centre_verification(report: dict, window=None) -> None:
    """PASS/FAIL judgment — REFUSED until the W1 window ratifies.

    Exists so the refusal is executable, not implicit: any caller
    reaching for a verdict gets the W1 sentinel by name.
    """
    if window is None:
        raise UnresolvedTodoTraceError(
            ("W1",), "centre-verification PASS/FAIL judgment"
        )
    raise NotImplementedError(
        "W1 ratified-window judgment is implemented in the pass that "
        "ratifies W1 (queued with Q9 + Q11), not before"
    )
