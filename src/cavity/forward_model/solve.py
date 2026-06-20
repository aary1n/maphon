"""SPEC §2 / §3 — eigenfrequency solve + field-handle retrieval.

Returns the complex eigenfrequency (Re f, Im f) plus an opaque handle to
the field solution against which §3's volume integrals are evaluated.

The field-symmetry mode-ID filter (SPEC §2 mode-ID note: azimuthal E,
axial H antinode, H circulating in r-z) lives in
`solve_eigenfrequency` — the eigenpair picked off the list is decided
by the field pattern, not eigenvalue order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EigenResult:
    """One eigenpair from a §2 solve.

    `complex_eigenfrequency_hz`: f' + i f''. Q computed below per SPEC §3
    (Q = f' / (2 f''); sign asserted against §8 before f'' is trusted —
    SPEC §11 gap #4).

    `mesh_element_count` and `comsol_version` are recorded with every
    solve for SPEC §1 reproducibility.

    `field_handle`: opaque MPh field handle for extraction (§3). None
    until `solve_eigenfrequency` is wired up.
    """

    complex_eigenfrequency_hz: complex
    mesh_element_count: int
    comsol_version: str
    field_handle: Any = None

    @property
    def f_real_hz(self) -> float:
        return self.complex_eigenfrequency_hz.real

    @property
    def f_imag_hz(self) -> float:
        return self.complex_eigenfrequency_hz.imag

    @property
    def q_factor(self) -> float:
        """Q = f' / (2 f'') per SPEC §3.

        Asserted against the §8 1/(p_e * tan_delta) closed form before
        any downstream code trusts this sign. If COMSOL returns
        Im(f) <= 0 the convention is inverted and the result must not
        flow downstream silently.
        """
        if self.f_imag_hz <= 0:
            raise ValueError(
                "Im(f) must be > 0 for Q = f'/(2 f''); got "
                f"{self.f_imag_hz}. Check COMSOL eigenvalue sign "
                "convention (SPEC §8 + §11 gap #4)."
            )
        return self.f_real_hz / (2.0 * self.f_imag_hz)


def solve_eigenfrequency(model: Any, study: Any) -> EigenResult:
    """Run the eigenfrequency study and return the TE01delta result.

    Stub. Field-symmetry mode-ID (SPEC §2) lands here together with the
    MPh solve call.
    """
    raise NotImplementedError(
        "solve_eigenfrequency is not yet implemented; the field-symmetry "
        "mode-ID filter (SPEC §2) must precede any Q the rest of the "
        "pipeline consumes."
    )
