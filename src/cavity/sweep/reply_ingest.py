"""Oxborrow-reply ingestion scaffolding — the blocker-independent tier of
docs/plans/oxborrow_reply_ingestion_and_wu_anchor.md.

Built BEFORE any reply exists, so that when Mark Oxborrow's reply lands the
ingestion changeset is a data change, not a code change. This module
implements: the reply-transcription schema, semantic payload validation
(beyond `SentinelResolution`'s key check), the §1 case-classification
tables, the D5 uniform-band convention, the Q13-coupled gap-form
arithmetic, and the structured dry-run / partial-reply report the plan's
§5 requires.

HARD GUARANTEES (each tested in tests/test_sweep_reply_ingest.py):

- NOTHING here writes to `cavity.sweep.resolutions` or any file. Minting a
  ratified resolution remains a human changeset; this module validates and
  reports only.
- A FIXTURE transcription can only ever yield a MOCK resolution object
  (rung PLANNING_ASSUMPTION, mock=True), which every solve-ready exit
  already refuses. No fixture value can reach production provenance or
  resolve a real sentinel.
- The Q13 evidence-favoured branch is never read into a default: an absent
  or question-unaware height stays absent (NON_RESPONSIVE, annotation
  only) — plan §2's prohibition, enforced here by construction.
- Gap-form Q2 arithmetic requires an explicit resolved height float; while
  Q13 is unresolved there is none to pass (`STO_HEIGHT_FORK` refuses float
  coercion), so the conversion is structurally impossible early — hidden
  coupling H6.

Input contract: a human TRANSCRIBES the archived reply into the explicit
schema below (never automatic prose parsing); the transcription cites the
archive path, and every numeric field is stated in SI metres. The
`fixture` flag marks synthetic test transcriptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from cavity.provenance.constants import GEOM_WU_STO_RING
from cavity.sweep.dofs import (
    DesignMode,
    ResolutionContext,
    Rung,
    SentinelResolution,
    _REQUIRED_PAYLOAD_KEYS,
)
from cavity.sweep.resolutions import ratified_resolutions

__all__ = [
    "ReplyClass",
    "ReplyItemError",
    "IngestOutcome",
    "MintInstruction",
    "DryRunReport",
    "uniform_band_from_informal",
    "p_tune_from_gap",
    "classify_q13",
    "classify_q2",
    "classify_q9",
    "ingest_reply",
    "build_d2_escape_hatch",
]


class ReplyClass(Enum):
    """Classification vocabulary of the plan's §1 case tables."""

    FULL = "full"
    PARTIAL = "partial"
    #: Q2 answered in gap form while Q13 is unresolved — "answered,
    #: awaiting Q13 arithmetic"; no number minted (plan §1.2).
    DEFERRED_FULL = "deferred-full"
    #: e.g. a question-unaware Q13 restatement (the 2026-07-17 email is
    #: the standing example) — dated rung annotation only, never resolving.
    NON_RESPONSIVE = "non-responsive"
    ABSENT = "absent"


class ReplyItemError(ValueError):
    """A transcription item fails semantic validation (bad units, inverted
    band, invented precision, missing evidence…). Refusal, not repair."""


# --- sanity windows (unit-slip guards, not physics constraints) ---------
# A transcription in mm instead of m is the likeliest silent corruption;
# these windows catch three-orders-of-magnitude slips while accepting any
# physically plausible bench value. STATUS: TRANSCRIPTION GUARDS at
# planning tier — deliberately ungraded (they bound transcription error,
# not physics; a genuine value outside them would surface as a refusal to
# investigate, never a silent clamp). Adversarial-review annotation,
# 2026-07-20.
_HEIGHT_WINDOW_M = (1e-3, 20e-3)  # STO ring height ~8.5/8.6 mm
_P_TUNE_WINDOW_M = (5e-3, 60e-3)  # internal height ~15-18 mm class
_OFFSET_WINDOW_M = (-10e-3, 10e-3)  # crystal axial offset within the bore
_GAP_WINDOW_M = (0.0, 40e-3)  # plate-to-STO gap (5-10 mm class)


def _require_finite(value: object, name: str) -> float:
    try:
        out = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ReplyItemError(f"{name}: not a number ({value!r})") from exc
    if not (out == out and abs(out) != float("inf")):
        raise ReplyItemError(f"{name}: non-finite value {out!r}")
    return out


def _require_window(value: float, window: tuple[float, float], name: str) -> float:
    lo, hi = window
    if not (lo <= value <= hi):
        raise ReplyItemError(
            f"{name} = {value} m is outside the sanity window [{lo}, {hi}] m "
            "— check the transcription's units (metres, not millimetres)"
        )
    return value


def uniform_band_from_informal(
    centre_m: float, slack_m: float, quote: str
) -> tuple[tuple[float, float], str]:
    """D5 (user-ratified 2026-07-20): informal slack ("give or take X") is
    read as the UNIFORM band centre ± slack — the single convention at
    every site, with the wording quoted. Returns (band, reading-note)."""
    if not quote.strip():
        raise ReplyItemError("informal band requires the verbatim quote")
    slack = _require_finite(slack_m, "slack_m")
    if slack <= 0:
        raise ReplyItemError(f"slack_m must be > 0, got {slack}")
    centre = _require_finite(centre_m, "centre_m")
    note = (
        f"D5 uniform reading of informal slack {quote!r}: band = "
        f"centre {centre} m ± {slack} m (planning-tier reading layered on "
        "the written number)"
    )
    return ((centre - slack, centre + slack), note)


def p_tune_from_gap(gap_m: float, q13_height_m: float) -> float:
    """Plan §1.2 conversion 2 (gap form): p_tune = deck_clearance + h(Q13)
    + g. FORBIDDEN while Q13 is unresolved — callers must pass the
    RESOLVED height as a float; the fork object refuses coercion, so no
    pre-resolution value exists to pass (H6). The derivation string is the
    caller's provenance obligation."""
    gap = _require_window(_require_finite(gap_m, "gap_m"), _GAP_WINDOW_M, "gap_m")
    height = _require_window(
        _require_finite(q13_height_m, "q13_height_m"),
        _HEIGHT_WINDOW_M,
        "q13_height_m",
    )
    return GEOM_WU_STO_RING.deck_clearance_m + height + gap


@dataclass(frozen=True)
class IngestOutcome:
    """One question's classification + (for FULL) the validated payload."""

    question_id: str
    classification: ReplyClass
    rung: Rung | None
    payload: dict | None
    notes: tuple[str, ...] = field(default=())
    provenance: str = ""


@dataclass(frozen=True)
class MintInstruction:
    """What the HUMAN changeset would append to
    `cavity.sweep.resolutions.RATIFIED_RESOLUTIONS`. Data, not code: this
    module never writes it anywhere.

    FIXTURE HARDENING (adversarial-review fix, 2026-07-20): a fixture
    instruction is marked as such, its provenance is FIXTURE-prefixed,
    and `validate_contract` NEVER constructs a production-shaped
    (mock=False) resolution from fixture data — the key-contract check
    runs through a mock instance instead. A determined caller copying
    fields out of a fixture instruction therefore copies a
    FIXTURE-prefixed provenance string into any hand-built resolution —
    the lie becomes visible in the register diff, which the human
    changeset review is the final gate on."""

    question_id: str
    payload: dict
    rung: Rung
    provenance: str
    fixture: bool = False

    def __post_init__(self) -> None:
        if self.fixture and not self.provenance.upper().startswith("FIXTURE"):
            object.__setattr__(
                self, "provenance", f"FIXTURE (resolves nothing): {self.provenance}"
            )

    def as_mock_resolution(self) -> SentinelResolution:
        """The ONLY resolution object a dry run may instantiate for
        pipeline exercise: forced mock=True + PLANNING_ASSUMPTION, refused
        by every solve-ready exit."""
        return SentinelResolution(
            question_id=self.question_id,
            payload=dict(self.payload),
            rung=Rung.PLANNING_ASSUMPTION,
            provenance=f"DRY-RUN MOCK of: {self.provenance}",
            mock=True,
        )

    def validate_contract(self) -> None:
        """Prove the payload satisfies the committed
        `SentinelResolution` key contract WITHOUT keeping the object.
        Fixture instructions validate through a MOCK instance only — no
        production-shaped resolution is ever constructed from fixture
        data. Nothing is registered either way — registration is a human
        changeset by design."""
        if self.fixture:
            self.as_mock_resolution()
            return
        SentinelResolution(
            question_id=self.question_id,
            payload=dict(self.payload),
            rung=self.rung,
            provenance=self.provenance,
            mock=False,
        )


# --- Q13 ----------------------------------------------------------------


def classify_q13(item: dict | None, *, archive_ref: str) -> IngestOutcome:
    """Plan §1.1 case table. `item` keys (transcription schema):
    height_m, question_aware(bool), measured(bool), precision_m(optional),
    quote(str). D1 (ratified): an explicitly responsive written answer
    resolves; a question-unaware restatement never does."""
    if item is None:
        return IngestOutcome("Q13", ReplyClass.ABSENT, None, None)
    quote = str(item.get("quote", "")).strip()
    if not quote:
        raise ReplyItemError("Q13: transcription must quote the sentence(s)")
    if not bool(item.get("question_aware", False)):
        return IngestOutcome(
            "Q13",
            ReplyClass.NON_RESPONSIVE,
            None,
            None,
            notes=(
                "question-UNAWARE restatement (D1): lands as a dated rung "
                "annotation on the fork record only; Q13 stays open",
            ),
            provenance=f"{archive_ref}: {quote!r} (non-responsive)",
        )
    height = _require_window(
        _require_finite(item.get("height_m"), "Q13 height_m"),
        _HEIGHT_WINDOW_M,
        "Q13 height_m",
    )
    measured = bool(item.get("measured", False))
    if not measured and item.get("precision_m") is not None:
        raise ReplyItemError(
            "Q13: precision_m on a non-measured (written-selection) answer "
            "— a caliper-class precision may only enter when HE states a "
            "measurement (plan §1.1: never substitute a precision of our "
            "own invention)"
        )
    payload: dict = {
        "sto_height_m": height,
        "selection_evidence": (
            f"Oxborrow {'caliper measurement' if measured else 'written reply'} "
            f"({archive_ref}), responsive to the explicit 8.5-vs-8.6 question: "
            f"{quote!r}"
            + ("" if measured else " — written selection, not a measurement")
        ),
    }
    notes: list[str] = []
    if measured and item.get("precision_m") is not None:
        precision = _require_finite(item["precision_m"], "Q13 precision_m")
        if precision <= 0:
            raise ReplyItemError(f"Q13 precision_m must be > 0, got {precision}")
        payload["sto_height_band_m"] = (height - precision, height + precision)
        notes.append("caliper band rides the payload (materialise_dims branch)")
    elif measured:
        notes.append(
            "measured value with NO stated precision: band key omitted — the "
            "machining placeholder applies; one-line follow-up queued (not "
            "blocking); never substitute a precision of our own"
        )
    return IngestOutcome(
        "Q13",
        ReplyClass.FULL,
        Rung.SUPERVISOR_CONFIRMED,
        payload,
        notes=tuple(notes),
        provenance=f"{archive_ref}: {quote!r}",
    )


# --- Q2 -----------------------------------------------------------------


def classify_q2(
    item: dict | None,
    *,
    archive_ref: str,
    q13_height_m: float | None = None,
) -> IngestOutcome:
    """Plan §1.2 case table. Parameterisations: 'internal_height' (direct),
    'gap' (Q13-coupled; DEFERRED_FULL while no resolved height float is
    supplied), 'screw_turns' (convertible only with a stated pitch).
    Partial forms (one end, uncommitted typicals) stay PARTIAL."""
    if item is None:
        return IngestOutcome("Q2", ReplyClass.ABSENT, None, None)
    quote = str(item.get("quote", "")).strip()
    if not quote:
        raise ReplyItemError("Q2: transcription must quote the sentence(s)")
    notes: list[str] = []
    rider = item.get("piston_gap_depth_m")
    if rider is not None:
        rider = _require_finite(rider, "piston_gap_depth_m")
        if rider <= 0:
            raise ReplyItemError("piston_gap_depth_m must be > 0")
        notes.append(
            "piston_gap_depth_m rider present: needs the H1 wiring change in "
            "draw_solve_spec (currently no consumer), not just the payload"
        )

    form = item.get("form")
    if form == "internal_height":
        raw = {k: item.get(k) for k in ("nominal_m", "min_m", "max_m")}
        missing = sorted(k for k, v in raw.items() if v is None)
        if missing:
            # One-ended / nominal-less answers are PARTIAL per the plan's
            # §1.2 table ("one end only … PARTIAL — sentinel stays"), never
            # an error and never completed with invented values
            # (adversarial-review fix, 2026-07-20).
            return IngestOutcome(
                "Q2",
                ReplyClass.PARTIAL,
                None,
                None,
                notes=(
                    f"internal-height answer missing {missing}: the defined "
                    "value(s) may land as dated rung annotations; "
                    "concrete-proposal follow-up asks for the rest (we "
                    "propose, he ratifies) — no invented completion",
                ),
                provenance=f"{archive_ref}: {quote!r}",
            )
        nominal = _require_window(
            _require_finite(raw["nominal_m"], "Q2 nominal_m"),
            _P_TUNE_WINDOW_M,
            "Q2 nominal_m",
        )
        lo = _require_window(
            _require_finite(raw["min_m"], "Q2 min_m"),
            _P_TUNE_WINDOW_M,
            "Q2 min_m",
        )
        hi = _require_window(
            _require_finite(raw["max_m"], "Q2 max_m"),
            _P_TUNE_WINDOW_M,
            "Q2 max_m",
        )
    elif form == "gap":
        if q13_height_m is None:
            return IngestOutcome(
                "Q2",
                ReplyClass.DEFERRED_FULL,
                None,
                None,
                notes=(
                    "gap-form travel while Q13 is unresolved: recorded as "
                    "'answered, awaiting Q13 arithmetic'; no number minted "
                    "(plan §1.2 conversion 2 is FORBIDDEN pre-Q13 — H6)",
                ),
                provenance=f"{archive_ref}: {quote!r} (gap form, deferred)",
            )
        if item.get("gap_nominal_m") is None:
            # FULL requires nominal + both ends (plan §1.2 table); a
            # midpoint nominal would be OUR invention, not his statement
            # (adversarial-review fix, 2026-07-20).
            return IngestOutcome(
                "Q2",
                ReplyClass.PARTIAL,
                None,
                None,
                notes=(
                    "gap-form travel ends stated but NO nominal: FULL "
                    "requires nominal + both ends; follow-up proposes the "
                    "recorded as-operated 15 mm print as the nominal FOR "
                    "HIM TO RATIFY (D3 keeps the print as record either "
                    "way) — never a silently invented midpoint",
                ),
                provenance=f"{archive_ref}: {quote!r} (gap ends only)",
            )
        lo = p_tune_from_gap(item.get("gap_min_m"), q13_height_m)
        hi = p_tune_from_gap(item.get("gap_max_m"), q13_height_m)
        nominal = p_tune_from_gap(item["gap_nominal_m"], q13_height_m)
        notes.append(
            "gap-form conversion: p_tune = deck_clearance (3.0 mm) + h(Q13) "
            f"= {q13_height_m} m + g — derivation recorded verbatim per plan "
            "§1.2"
        )
    elif form == "screw_turns":
        # Conversion 3 gives travel only when pitch AND an explicit
        # reference/range are all his; a symmetric ±turns·pitch/2 reading
        # was OUR convention, not ratified — retired (adversarial-review
        # fix, 2026-07-20). Screw answers are mechanism colour: PARTIAL.
        return IngestOutcome(
            "Q2",
            ReplyClass.PARTIAL,
            None,
            None,
            notes=(
                "screw-turns answer: mechanism colour only. If the reply's "
                "OWN arithmetic states explicit min/max heights, transcribe "
                "them as the internal_height form; no symmetric-about-"
                "nominal reading is ever applied on our side",
            ),
            provenance=f"{archive_ref}: {quote!r}",
        )
    else:
        return IngestOutcome(
            "Q2",
            ReplyClass.PARTIAL,
            None,
            None,
            notes=(
                "uncommitted/one-ended travel ('typical 5-10 mm' class): "
                "sentinel stays; dated annotation + concrete-proposal "
                "follow-up (we propose, he ratifies). D2 escape hatch is "
                "ARMED but fires only after the follow-up goes unanswered, "
                "with the proposal/follow-up/absence preserved verbatim — "
                "not from this transcription",
            ),
            provenance=f"{archive_ref}: {quote!r}",
        )

    if not (lo < hi):
        raise ReplyItemError(f"Q2 travel inverted: [{lo}, {hi}]")
    if not (lo <= nominal <= hi):
        raise ReplyItemError(
            f"Q2 nominal {nominal} outside travel [{lo}, {hi}]"
        )
    payload = {
        "p_tune_nominal": nominal,
        "p_tune_min": lo,
        "p_tune_max": hi,
        "mechanism": (
            "screw-suspended ceiling / 26-mm piston on a brass screw — "
            "already supervisor-written (2026-07-17) and in print (Wu 2020; "
            f"PRL SM); reply cited: {quote!r}"
        ),
    }
    if rider is not None:
        payload["piston_gap_depth_m"] = rider
    if abs(nominal - GEOM_WU_STO_RING.box_internal_height_asoperated_m) > 1e-9:
        notes.append(
            "nominal differs from the recorded as-operated 15 mm print: D3 "
            "applies — the reply value becomes the modelled W2 nominal at "
            "the written rung; 15 mm stays the print record, never averaged; "
            "audit the box_height_fallback_m call sites (H7)"
        )
    return IngestOutcome(
        "Q2",
        ReplyClass.FULL,
        Rung.SUPERVISOR_CONFIRMED,
        payload,
        notes=tuple(notes),
        provenance=f"{archive_ref}: {quote!r}",
    )


# --- Q9 -----------------------------------------------------------------


def classify_q9(item: dict | None, *, archive_ref: str) -> IngestOutcome:
    """Plan §1.3 case table: FULL needs all three payload numbers; the
    informal-slack form resolves via D5 only when the slack covers BOTH
    coordinates; 'nominally centred, no tolerance' stays PARTIAL."""
    if item is None:
        return IngestOutcome("Q9", ReplyClass.ABSENT, None, None)
    quote = str(item.get("quote", "")).strip()
    if not quote:
        raise ReplyItemError("Q9: transcription must quote the sentence(s)")

    if item.get("informal_slack_m") is not None:
        if not bool(item.get("slack_covers_both", False)):
            return IngestOutcome(
                "Q9",
                ReplyClass.PARTIAL,
                None,
                None,
                notes=(
                    "informal slack plausibly covers only one coordinate: "
                    "mint nothing; ask which (plan §1.3)",
                ),
                provenance=f"{archive_ref}: {quote!r}",
            )
        if item.get("nominal_m") is None:
            raise ReplyItemError(
                "Q9 informal-slack form requires an explicit nominal_m from "
                "the transcriber (0.0 only when the reply itself says "
                "centred/mid-height) — no physical default is ever assumed"
            )
        centre = _require_window(
            _require_finite(item["nominal_m"], "Q9 nominal_m"),
            _OFFSET_WINDOW_M,
            "Q9 nominal_m",
        )
        band, reading = uniform_band_from_informal(
            centre, item["informal_slack_m"], quote
        )
        payload = {
            "crystal_axial_offset_nominal_m": centre,
            "crystal_axial_offset_band_m": band,
            "centring_tolerance_m": float(item["informal_slack_m"]),
        }
        return IngestOutcome(
            "Q9",
            ReplyClass.FULL,
            Rung.SUPERVISOR_CONFIRMED,
            payload,
            notes=(reading,),
            provenance=f"{archive_ref}: {quote!r} ({reading})",
        )

    have = {
        k: item.get(k)
        for k in (
            "axial_offset_nominal_m",
            "axial_offset_band_m",
            "centring_tolerance_m",
        )
    }
    if any(v is None for v in have.values()):
        missing = sorted(k for k, v in have.items() if v is None)
        return IngestOutcome(
            "Q9",
            ReplyClass.PARTIAL,
            None,
            None,
            notes=(
                f"partial placement answer — missing {missing}: rung "
                "annotations only (the 2026-07-16 eccentricity-partial "
                "mirror); no resolution minted; concrete-proposal follow-up "
                "(containment bounds may be STATED, never minted as bands)",
            ),
            provenance=f"{archive_ref}: {quote!r}",
        )
    nominal = _require_window(
        _require_finite(have["axial_offset_nominal_m"], "Q9 nominal"),
        _OFFSET_WINDOW_M,
        "Q9 nominal",
    )
    band_raw = have["axial_offset_band_m"]
    lo = _require_finite(band_raw[0], "Q9 band lo")
    hi = _require_finite(band_raw[1], "Q9 band hi")
    if not (lo < hi):
        raise ReplyItemError(f"Q9 band inverted: [{lo}, {hi}]")
    if not (lo <= nominal <= hi):
        raise ReplyItemError(f"Q9 nominal {nominal} outside band [{lo}, {hi}]")
    tol = _require_finite(have["centring_tolerance_m"], "Q9 centring tolerance")
    if tol < 0:
        raise ReplyItemError(f"Q9 centring tolerance must be >= 0, got {tol}")
    payload = {
        "crystal_axial_offset_nominal_m": nominal,
        "crystal_axial_offset_band_m": (lo, hi),
        "centring_tolerance_m": tol,
    }
    return IngestOutcome(
        "Q9",
        ReplyClass.FULL,
        Rung.SUPERVISOR_CONFIRMED,
        payload,
        notes=(
            "post-resolution obligation H2: the §7.4 first-order "
            "eccentricity estimate becomes due BEFORE the main sweep — the "
            "resolution changeset must schedule it",
        ),
        provenance=f"{archive_ref}: {quote!r}",
    )


# --- assembly + dry-run report ------------------------------------------

#: Operations that stay prohibited while the named questions are open —
#: the report's "downstream operations remain prohibited" section.
_PROHIBITED_BY_QUESTION: dict[str, tuple[str, ...]] = {
    "Q13": (
        "the W2 Wu-anchor solve (hard precondition: Q13 resolved)",
        "any geometry build in EITHER design mode (sto_height_m is a noise dim)",
        "gap-form Q2 arithmetic (H6)",
    ),
    "Q2": (
        "the d = 8 baseline (θ, p) training campaign (d = 7 remains the fallback)",
        "piston-step recess modelling (gap depth rides Q2)",
    ),
    "Q9": (
        "crystal placement in Phase 1b solves at anything above a labelled "
        "planning placement",
        "the centre-verification block (with Q11; SPEC §5b engine also required)",
    ),
}

#: Work the plan's §5 declares LEGAL IMMEDIATELY on any reply, complete or
#: not — the report's "newly licensed" section.
_LEGAL_IMMEDIATELY: tuple[str, ...] = (
    "archive + MANIFEST.sha256 + integrity test (§0 — unconditional step zero)",
    "dated rung annotations on sentinels/DofSpecs for anything he DID state",
    "SPEC §11 dated status lines",
    "the concrete-proposal follow-up email (we propose, he ratifies)",
    "test re-scope PREP (drafted, not merged)",
    "symbolic recording of gap-form arithmetic pending Q13",
    "W2 runner scaffolding as zero-licence code (licence gate keeps it inert)",
    "Phase 1b engine work per its own plan (Q1 ruling)",
)


@dataclass(frozen=True)
class DryRunReport:
    """The plan §5 structured report: what was learned, at which rung,
    which sentinels remain unresolved, which downstream operations remain
    prohibited, and what work is newly licensed."""

    fixture: bool
    archive_ref: str
    outcomes: tuple[IngestOutcome, ...]
    mint_instructions: tuple[MintInstruction, ...]
    unresolved_after_mint: dict[str, tuple[str, ...]]
    prohibited: tuple[str, ...]
    newly_licensed: tuple[str, ...]

    def to_markdown(self) -> str:
        lines = [
            "# Reply-ingestion dry run"
            + (" — FIXTURE (synthetic; resolves nothing)" if self.fixture else ""),
            "",
            f"Archive reference: `{self.archive_ref}`",
            "",
            "**Nothing below is minted by this tool.** Ratified resolutions "
            "enter `cavity.sweep.resolutions.RATIFIED_RESOLUTIONS` only via "
            "a human changeset with the archive committed and the refusal "
            "tests re-scoped (declared collection delta).",
            "",
            "## What was learned",
        ]
        for o in self.outcomes:
            rung = o.rung.value if o.rung else "—"
            lines.append(
                f"- **{o.question_id}**: {o.classification.value} (rung: {rung})"
            )
            for n in o.notes:
                lines.append(f"  - {n}")
        lines += ["", "## Sentinels remaining unresolved (after a real mint)"]
        for mode, missing in self.unresolved_after_mint.items():
            state = ", ".join(missing) if missing else "none — mode fully resolved"
            lines.append(f"- {mode}: {state}")
        lines += ["", "## Downstream operations remaining prohibited"]
        lines += [f"- {p}" for p in self.prohibited] or ["- none"]
        lines += ["", "## Work newly licensed (plan §5)"]
        lines += [f"- {w}" for w in self.newly_licensed]
        return "\n".join(lines) + "\n"


def ingest_reply(
    transcription: dict,
    *,
    fixture: bool,
) -> DryRunReport:
    """Classify a transcribed reply and produce the §5 structured report.

    `fixture=True` marks synthetic transcriptions: outcomes are DOWNGRADED
    to PLANNING_ASSUMPTION, mint instructions are fixture-marked with
    FIXTURE-prefixed provenance, and `as_mock_resolution` is the only
    resolution object a fixture can yield. `fixture=False` requires the
    cited archive directory to EXIST in the repo with a MANIFEST.sha256
    (plan §0: archive before reading numbers; the hash verification itself
    rides the calibration CI integrity gate — cavity cannot import
    calibration across the one-way boundary). A REAL reply's mint remains
    a human changeset either way.

    Gap-form Q2 height source (adversarial-review fix, 2026-07-20): the
    conversion consumes a resolved height ONLY from (a) this same reply's
    FULL Q13 outcome, or (b) an already-RATIFIED non-mock Q13 in
    `cavity.sweep.resolutions` — never a caller-supplied float, so the
    evidence-favoured fork branch has no path in.
    """
    archive_ref = str(transcription.get("archive", "")).strip()
    if not archive_ref:
        raise ReplyItemError(
            "transcription must cite the archive path "
            "(calibration/data/raw/oxborrow_<topic>_<date>/ — plan §0: "
            "archive BEFORE reading numbers out of the reply)"
        )
    if fixture and "FIXTURE" not in archive_ref.upper():
        raise ReplyItemError(
            "fixture transcriptions must mark the archive ref with 'FIXTURE' "
            "so no synthetic value can masquerade as an archived reply"
        )
    if not fixture:
        repo_root = Path(__file__).resolve().parents[3]
        archive_dir = repo_root / archive_ref
        if not (archive_dir.is_dir() and (archive_dir / "MANIFEST.sha256").is_file()):
            raise ReplyItemError(
                f"non-fixture ingest requires an existing committed archive "
                f"with MANIFEST.sha256 at {archive_ref!r} (plan §0 step "
                "zero); archive the reply before transcribing it"
            )

    items = transcription.get("items", {})
    q13 = classify_q13(items.get("Q13"), archive_ref=archive_ref)
    height: float | None = None
    if q13.classification is ReplyClass.FULL:
        height = q13.payload["sto_height_m"]  # type: ignore[index]
    else:
        ratified_q13 = ratified_resolutions().get("Q13")
        if ratified_q13 is not None and not ratified_q13.mock:
            height = float(ratified_q13.payload["sto_height_m"])
    q2 = classify_q2(items.get("Q2"), archive_ref=archive_ref, q13_height_m=height)
    q9 = classify_q9(items.get("Q9"), archive_ref=archive_ref)
    outcomes = (q13, q2, q9)

    if fixture:
        # Fixture data never carries a supervisor rung — downgrade every
        # outcome to PLANNING_ASSUMPTION (adversarial-review fix).
        outcomes = tuple(
            IngestOutcome(
                question_id=o.question_id,
                classification=o.classification,
                rung=Rung.PLANNING_ASSUMPTION if o.rung is not None else None,
                payload=o.payload,
                notes=o.notes
                + (("rung downgraded: FIXTURE data (resolves nothing)",)
                   if o.rung is not None
                   else ()),
                provenance=o.provenance,
            )
            for o in outcomes
        )

    mints: list[MintInstruction] = []
    for o in outcomes:
        if o.classification is ReplyClass.FULL:
            assert o.payload is not None and o.rung is not None
            mi = MintInstruction(
                question_id=o.question_id,
                payload=o.payload,
                rung=o.rung,
                provenance=o.provenance,
                fixture=fixture,
            )
            mi.validate_contract()  # key contract only; registers nothing
            mints.append(mi)

    # Hypothetical post-mint state, computed with MOCK stand-ins so the
    # exercise itself can never satisfy a solve-ready exit.
    # (2026-07-21 register change: Q13/Q2 are now ratified with written
    # confirmation pending (in-person measurements — provenance
    # corrected 2026-07-22), so a written reply re-answering them is a
    # RUNG UPGRADE — the mint stand-in supersedes the same-question
    # ratified entry here; without the dedupe ResolutionContext refuses
    # the duplicate.)
    minted_qids = {m.question_id for m in mints}
    hypothetical = ResolutionContext(
        resolutions=tuple(
            r
            for r in ratified_resolutions().resolutions
            if r.question_id not in minted_qids
        )
        + tuple(m.as_mock_resolution() for m in mints)
    )
    unresolved_after = {
        mode.value: hypothetical.unresolved(mode) for mode in DesignMode
    }
    open_questions = sorted(
        {q for missing in unresolved_after.values() for q in missing}
    )
    prohibited = tuple(
        p for q in open_questions for p in _PROHIBITED_BY_QUESTION.get(q, ())
    ) + (
        "EVERYTHING solve-ready until the human mint changeset lands "
        "(this dry run registers nothing)",
    )
    for key in _REQUIRED_PAYLOAD_KEYS:  # cheap invariant: contract intact
        assert key in {"Q2", "Q9", "Q11", "Q13"}

    return DryRunReport(
        fixture=fixture,
        archive_ref=archive_ref,
        outcomes=outcomes,
        mint_instructions=tuple(mints),
        unresolved_after_mint=unresolved_after,
        prohibited=prohibited,
        newly_licensed=_LEGAL_IMMEDIATELY,
    )


def build_d2_escape_hatch(
    *,
    proposal_text: str,
    proposed_nominal_m: float,
    proposed_min_m: float,
    proposed_max_m: float,
    followup_dates: tuple[str, ...],
    followup_archive_refs: tuple[str, ...],
    no_reply_as_of: str,
    elapsed_days: float,
) -> MintInstruction:
    """The ARMED D2 escape hatch (user-ratified 2026-07-20), mechanised
    as a validated transaction (adversarial-review fix): fires only after
    the concrete-proposal follow-up went unanswered. Produces the
    PLANNING_ASSUMPTION (mock=False) Q2 mint instruction whose provenance
    preserves VERBATIM (i) the exact proposal, (ii) the follow-up date(s)
    and archive path(s) — each of which must exist committed with a
    manifest — and (iii) the recorded absence of a reply with elapsed
    time. Registration remains the human changeset; a later real answer
    supersedes in place with a dated note, never a silent edit."""
    if not proposal_text.strip():
        raise ReplyItemError("D2: the exact proposal text is required verbatim")
    if not followup_dates or not all(d.strip() for d in followup_dates):
        raise ReplyItemError("D2: follow-up date(s) required")
    if not no_reply_as_of.strip():
        raise ReplyItemError("D2: the no-reply-as-of date is required")
    if not elapsed_days > 0:
        raise ReplyItemError("D2: elapsed_days must be > 0")
    if not followup_archive_refs:
        raise ReplyItemError("D2: follow-up archive path(s) required")
    repo_root = Path(__file__).resolve().parents[3]
    for ref in followup_archive_refs:
        archive_dir = repo_root / ref
        if not (
            archive_dir.is_dir() and (archive_dir / "MANIFEST.sha256").is_file()
        ):
            raise ReplyItemError(
                f"D2: follow-up archive {ref!r} must exist committed with a "
                "MANIFEST.sha256 before the escape hatch may fire"
            )
    nominal = _require_window(
        _require_finite(proposed_nominal_m, "D2 nominal"),
        _P_TUNE_WINDOW_M,
        "D2 nominal",
    )
    lo = _require_window(
        _require_finite(proposed_min_m, "D2 min"), _P_TUNE_WINDOW_M, "D2 min"
    )
    hi = _require_window(
        _require_finite(proposed_max_m, "D2 max"), _P_TUNE_WINDOW_M, "D2 max"
    )
    if not (lo < hi):
        raise ReplyItemError(f"D2 travel inverted: [{lo}, {hi}]")
    if not (lo <= nominal <= hi):
        raise ReplyItemError(f"D2 nominal {nominal} outside [{lo}, {hi}]")
    provenance = (
        "D2 ESCAPE HATCH (user-ratified 2026-07-20; planning assumption, "
        "supersede-in-place on a real answer). "
        f"Proposal sent, verbatim: {proposal_text!r}. Proposed band read "
        "under the D5 uniform convention. Follow-up(s): "
        f"{', '.join(followup_dates)} (archives: "
        f"{', '.join(followup_archive_refs)}). No reply recorded as of "
        f"{no_reply_as_of} ({elapsed_days:g} days elapsed)."
    )
    mi = MintInstruction(
        question_id="Q2",
        payload={
            "p_tune_nominal": nominal,
            "p_tune_min": lo,
            "p_tune_max": hi,
            "mechanism": (
                "screw-suspended ceiling / 26-mm piston on a brass screw "
                "(supervisor-written 2026-07-17; in print, Wu 2020 + PRL SM); "
                "travel band = the D2 proposed band, unconfirmed"
            ),
        },
        rung=Rung.PLANNING_ASSUMPTION,
        provenance=provenance,
        fixture=False,
    )
    mi.validate_contract()
    return mi
