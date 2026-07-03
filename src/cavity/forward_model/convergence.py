"""SPEC §2 mesh-convergence assessment — the sigma source for §4.

The convergence study solves the same geometry at >= 3 mesh refinement
levels (coarse -> fine) and this module judges the sequence:

  (i)  asymptotic regime: the level-to-level deltas in f' AND f'' must
       shrink monotonically. If they do not, the mesh is not in the
       asymptotic regime and NO sigma is emitted — `ConvergenceError`
       is raised instead. A fabricated sigma from a non-converged mesh
       would relocate the provenance trap into the §4 error
       propagation (see `validation.wall_loss`, which requires its Q
       uncertainties to come from exactly this residual).
  (ii) the finest-pair residuals |Δf'| and |Δf''| are the 1-sigma
       discretisation uncertainties on f' and f''. sigma_Q follows by
       linear propagation of Q = f'/(2 f'').

Pure Python — the COMSOL loop that produces the per-level
eigenfrequencies lives in `runner.py`; this assessment is
synthetic-testable without a licence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from cavity.extraction.qfactor import q_from_eigenfrequency

MIN_CONVERGENCE_LEVELS = 3


class ConvergenceError(RuntimeError):
    """Mesh sequence is not in the asymptotic regime — no sigma emitted."""


@dataclass(frozen=True)
class ConvergenceAssessment:
    """Verdict on a coarse->fine eigenfrequency sequence.

    `sigma_f_real_hz` / `sigma_f_imag_hz` are the finest-pair residuals
    |Δf'| and |Δf''| — the discretisation 1-sigma that
    `validation.wall_loss.decompose_wall_loss` requires for its Q
    uncertainties. `sigma_q` propagates them through Q = f'/(2 f''):

        sigma_Q = Q * sqrt( (sigma_f'/f')^2 + (sigma_f''/f'')^2 )

    `q_finest` is computed by the §3 extraction primitive
    (`q_from_eigenfrequency`) — not re-derived here.
    """

    complex_eigenfrequencies_hz: tuple[complex, ...]
    deltas_f_real_hz: tuple[float, ...]
    deltas_f_imag_hz: tuple[float, ...]
    sigma_f_real_hz: float
    sigma_f_imag_hz: float
    q_finest: float
    sigma_q: float


def _monotonically_shrinking(deltas: Sequence[float]) -> bool:
    """Each delta strictly below its predecessor (an exact-zero delta
    counts as converged and may repeat)."""
    return all(
        later < earlier or later == 0.0
        for earlier, later in zip(deltas, deltas[1:])
    )


def assess_convergence(
    complex_eigenfrequencies_hz: Sequence[complex],
) -> ConvergenceAssessment:
    """Judge a coarse->fine eigenfrequency sequence and emit sigma.

    Args:
        complex_eigenfrequencies_hz: the identified TE01delta
            eigenfrequency at each refinement level, ordered coarse ->
            fine, >= MIN_CONVERGENCE_LEVELS entries. Mode identity at
            every level is the caller's job (field-symmetry check per
            level — mode ordering is not stable across meshes).

    Raises:
        ConvergenceError: fewer than three levels, or the deltas in f'
            or f'' do not shrink monotonically. Per SPEC §2 the study
            must not emit sigma from a non-asymptotic sequence.
    """
    freqs = tuple(complex(f) for f in complex_eigenfrequencies_hz)
    if len(freqs) < MIN_CONVERGENCE_LEVELS:
        raise ConvergenceError(
            f"convergence study needs >= {MIN_CONVERGENCE_LEVELS} mesh "
            f"refinement levels; got {len(freqs)}"
        )

    deltas_re = tuple(
        abs(b.real - a.real) for a, b in zip(freqs, freqs[1:])
    )
    deltas_im = tuple(
        abs(b.imag - a.imag) for a, b in zip(freqs, freqs[1:])
    )

    problems = []
    if not _monotonically_shrinking(deltas_re):
        problems.append(f"f' deltas not monotonically shrinking: {deltas_re}")
    if not _monotonically_shrinking(deltas_im):
        problems.append(f"f'' deltas not monotonically shrinking: {deltas_im}")
    if problems:
        raise ConvergenceError(
            "mesh sequence is not in the asymptotic regime — refusing to "
            "emit sigma (SPEC §2). " + "; ".join(problems) + ". "
            f"Eigenfrequencies (coarse->fine): {freqs}. Refine further or "
            "inspect mode identification per level."
        )

    sigma_re = deltas_re[-1]
    sigma_im = deltas_im[-1]

    finest = freqs[-1]
    q_finest = q_from_eigenfrequency(finest)
    sigma_q = q_finest * math.hypot(
        sigma_re / finest.real, sigma_im / finest.imag
    )

    return ConvergenceAssessment(
        complex_eigenfrequencies_hz=freqs,
        deltas_f_real_hz=deltas_re,
        deltas_f_imag_hz=deltas_im,
        sigma_f_real_hz=sigma_re,
        sigma_f_imag_hz=sigma_im,
        q_finest=q_finest,
        sigma_q=sigma_q,
    )
