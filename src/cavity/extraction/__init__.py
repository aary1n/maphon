"""Mode-quantity extraction — SPEC §3.

f, Q (sign-asserted against §8), V_mode (global + gain-region variants
both labelled and returned), p_e (required), F_m (standard Purcell form
from SPEC §3 — not Breeze's printed prefactor). Every volume integral
routes through `axisymmetric_volume_integral`; the 2*pi*r axisymmetric
Jacobian enters there, in one place.

Layout:
  fields.py      — typed FieldSample input contract
  quadrature.py  — the integration primitive (single Jacobian site)
  modal.py       — V_mode (global + local) and p_e
  qfactor.py     — Q with sign assertion + emw.Qfactor cross-check
  purcell.py     — F_m
  validate.py    — SPEC §8 PEC + lossy-dielectric Q consistency hook

Top-level `extract(field)` runs the full pipeline and returns an
`ExtractionResult` with both V_mode and both F_m variants populated.
"""

from __future__ import annotations

from dataclasses import dataclass

from cavity.extraction.fields import FieldSample
from cavity.extraction.modal import (
    ModeVolumes,
    electric_filling_factor,
    mode_volumes,
)
from cavity.extraction.purcell import magnetic_purcell_factor
from cavity.extraction.qfactor import q_from_eigenfrequency
from cavity.extraction.quadrature import axisymmetric_volume_integral
from cavity.extraction.validate import assert_pec_lossy_q_consistency


@dataclass(frozen=True)
class ExtractionResult:
    """SPEC §3 extracted quantities for a single eigenmode.

    `v_mode_global_m3` and `v_mode_local_m3` are both reported per
    SPEC §3 (the 0.2-0.41 cm^3 literature spread sits in this choice);
    correspondingly `f_m_global` and `f_m_local` are both returned.

    `q_emw_cross_check` echoes the COMSOL emw.Qfactor scalar that was
    used as a cross-check (None if not supplied). The primary Q is
    always `q` = f'/(2 f'').
    """

    f_hz: float
    q: float
    q_emw_cross_check: float | None
    v_mode_global_m3: float
    v_mode_local_m3: float
    p_e: float
    f_m_global: float
    f_m_local: float


def extract(field: FieldSample) -> ExtractionResult:
    """Compute every SPEC §3 mode quantity from a cached `FieldSample`."""
    f_hz = field.complex_eigenfrequency_hz.real
    q = q_from_eigenfrequency(
        field.complex_eigenfrequency_hz,
        q_emw_cross_check=field.q_emw_cross_check,
    )
    volumes = mode_volumes(field)
    p_e = electric_filling_factor(field)
    f_m_global = magnetic_purcell_factor(q, volumes.global_m3, f_hz)
    f_m_local = magnetic_purcell_factor(q, volumes.local_m3, f_hz)
    return ExtractionResult(
        f_hz=f_hz,
        q=q,
        q_emw_cross_check=field.q_emw_cross_check,
        v_mode_global_m3=volumes.global_m3,
        v_mode_local_m3=volumes.local_m3,
        p_e=p_e,
        f_m_global=f_m_global,
        f_m_local=f_m_local,
    )


__all__ = [
    "ExtractionResult",
    "FieldSample",
    "ModeVolumes",
    "assert_pec_lossy_q_consistency",
    "axisymmetric_volume_integral",
    "electric_filling_factor",
    "extract",
    "magnetic_purcell_factor",
    "mode_volumes",
    "q_from_eigenfrequency",
]
