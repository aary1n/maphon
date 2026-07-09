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
  weights.py     — §7.T5(b) normalised weight functionals (cavity-arm
                   w_E + companion p_e; spin-arm w_s with parameterised
                   SpinProjection, |H|^2 default)

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
from cavity.extraction.quadrature import (
    axisymmetric_node_volumes,
    axisymmetric_volume_integral,
)
from cavity.extraction.validate import assert_pec_lossy_q_consistency
from cavity.extraction.weights import (
    CavityArmWeight,
    SpinArmWeight,
    SpinProjection,
    WeightField,
    cavity_arm_weight,
    projected_h2_density,
    spin_arm_weight,
)


@dataclass(frozen=True)
class ExtractionResult:
    """SPEC §3 extracted quantities for a single eigenmode.

    `complex_eigenfrequency_hz` is propagated from the input
    `FieldSample` so downstream layers (e.g. §4 wall-loss
    decomposition) can independently re-derive Q via f'/(2 f'')
    without reaching back into the source `FieldSample`. The
    cancellation-prone reciprocal subtraction 1/Q_total - 1/Q_diel
    must be auditable at every layer, which means the upstream Q
    cannot be reduced to a single rounded float on the way through.

    `v_mode_global_m3` and `v_mode_local_m3` are both reported per
    SPEC §3 (the 0.2-0.41 cm^3 literature spread sits in this choice);
    correspondingly `f_m_global` and `f_m_local` are both returned.

    `q_emw_cross_check` echoes the COMSOL emw.Qfactor scalar that was
    used as a cross-check (None if not supplied). The primary Q is
    always `q` = f'/(2 f'').
    """

    f_hz: float
    complex_eigenfrequency_hz: complex
    q: float
    q_emw_cross_check: float | None
    v_mode_global_m3: float
    v_mode_local_m3: float
    p_e: float
    f_m_global: float
    f_m_local: float


def extract(field: FieldSample) -> ExtractionResult:
    """Compute every SPEC §3 mode quantity from a cached `FieldSample`."""
    f_complex = field.complex_eigenfrequency_hz
    f_hz = f_complex.real
    q = q_from_eigenfrequency(
        f_complex,
        q_emw_cross_check=field.q_emw_cross_check,
    )
    volumes = mode_volumes(field)
    p_e = electric_filling_factor(field)
    f_m_global = magnetic_purcell_factor(q, volumes.global_m3, f_hz)
    f_m_local = magnetic_purcell_factor(q, volumes.local_m3, f_hz)
    return ExtractionResult(
        f_hz=f_hz,
        complex_eigenfrequency_hz=f_complex,
        q=q,
        q_emw_cross_check=field.q_emw_cross_check,
        v_mode_global_m3=volumes.global_m3,
        v_mode_local_m3=volumes.local_m3,
        p_e=p_e,
        f_m_global=f_m_global,
        f_m_local=f_m_local,
    )


__all__ = [
    "CavityArmWeight",
    "ExtractionResult",
    "FieldSample",
    "ModeVolumes",
    "SpinArmWeight",
    "SpinProjection",
    "WeightField",
    "assert_pec_lossy_q_consistency",
    "axisymmetric_node_volumes",
    "axisymmetric_volume_integral",
    "cavity_arm_weight",
    "electric_filling_factor",
    "extract",
    "magnetic_purcell_factor",
    "mode_volumes",
    "projected_h2_density",
    "q_from_eigenfrequency",
    "spin_arm_weight",
]
