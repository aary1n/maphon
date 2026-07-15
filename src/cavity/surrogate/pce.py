"""L4 PCE scaffolding — SPEC §7-expanded §7.5 / design doc §9.

Polynomial chaos expansion on the RAW output basis (Q7 ruling: the
surrogates carry f, ln Q₀, ln η_H, ln V_mode, p_e; C₀/κc are COMPOSED
downstream in `cavity.sweep.compose`, and the CV gate honours §7.5's
intent by evaluating in composed space — `cavity.surrogate.cv_gate`).

Basis: total-degree multi-index set; order-2 full basis has
C(d+2, 2) terms — 45 at d = 8, 36 at d = 7 (§6/§9, pinned in tests).

Input standardisation (implementation assumption, flagged in the
ratified plan): each input maps to the unit interval through ITS OWN
CDF (`SamplingDim.cdf` — the same single-source map the design
transform uses), so the inputs are exactly U(0,1) under their sampling
law, and the tensorised ORTHONORMAL SHIFTED-LEGENDRE basis is
orthonormal w.r.t. the input measure by construction. Rung:
planning-assumption, numerics-only.

Fitting: ordinary least squares; analytic leave-one-out residuals from
the hat matrix (e_loo = e/(1 − h)), Q² = 1 − Σe_loo²/Σ(y − ȳ)² — the
brute-force refit equivalence is a committed test. Sparse order-3 LARS
enrichment is a LATER pass (rider R3: deferral approved; the
multi-index generator below is already order-general).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb

import numpy as np
from numpy.polynomial import legendre as npleg
from numpy.typing import NDArray

from cavity.sweep.design import SamplingDim


def n_basis_terms(d: int, order: int) -> int:
    """Total-degree basis size C(d + order, order)."""
    if d < 1 or order < 0:
        raise ValueError("need d >= 1 and order >= 0")
    return comb(d + order, order)


def total_degree_indices(
    d: int, order: int
) -> tuple[tuple[int, ...], ...]:
    """All multi-indices α with |α| <= order, graded-lexicographic."""
    if d < 1 or order < 0:
        raise ValueError("need d >= 1 and order >= 0")

    def compositions(total: int, slots: int):
        if slots == 1:
            yield (total,)
            return
        for head in range(total + 1):
            for tail in compositions(total - head, slots - 1):
                yield (head,) + tail

    indices: list[tuple[int, ...]] = []
    for degree in range(order + 1):
        indices.extend(sorted(compositions(degree, d)))
    assert len(indices) == n_basis_terms(d, order)
    return tuple(indices)


def legendre_orthonormal_1d(
    u: NDArray[np.floating], k: int
) -> NDArray[np.float64]:
    """Orthonormal shifted Legendre P̃_k on [0, 1]:
    P̃_k(u) = sqrt(2k + 1) · P_k(2u − 1); E[P̃_j P̃_k] = δ_jk under
    U(0, 1) (asserted numerically in tests)."""
    coeffs = np.zeros(k + 1)
    coeffs[k] = 1.0
    return np.sqrt(2.0 * k + 1.0) * npleg.legval(
        2.0 * np.asarray(u, dtype=np.float64) - 1.0, coeffs
    )


@dataclass(frozen=True)
class PCESurrogate:
    """One fitted PCE for one raw output."""

    dims: tuple[SamplingDim, ...]
    order: int
    indices: tuple[tuple[int, ...], ...]
    coeffs: NDArray[np.float64]
    q2: float
    loo_rmse: float

    @staticmethod
    def _standardise(
        dims: tuple[SamplingDim, ...], x: NDArray[np.floating]
    ) -> NDArray[np.float64]:
        x = np.asarray(x, dtype=np.float64)
        if x.ndim != 2 or x.shape[1] != len(dims):
            raise ValueError(
                f"x shape {x.shape} inconsistent with {len(dims)} dims"
            )
        return np.column_stack(
            [dims[j].cdf(x[:, j]) for j in range(len(dims))]
        )

    @staticmethod
    def _design_matrix(
        dims: tuple[SamplingDim, ...],
        indices: tuple[tuple[int, ...], ...],
        x: NDArray[np.floating],
    ) -> NDArray[np.float64]:
        u = PCESurrogate._standardise(dims, x)
        columns = []
        for alpha in indices:
            col = np.ones(u.shape[0])
            for j, k in enumerate(alpha):
                if k:
                    col = col * legendre_orthonormal_1d(u[:, j], k)
            columns.append(col)
        return np.column_stack(columns)

    @classmethod
    def fit(
        cls,
        dims: tuple[SamplingDim, ...] | list[SamplingDim],
        x: NDArray[np.floating],
        y: NDArray[np.floating],
        *,
        order: int = 2,
    ) -> "PCESurrogate":
        dims = tuple(dims)
        y = np.asarray(y, dtype=np.float64)
        indices = total_degree_indices(len(dims), order)
        n_terms = len(indices)
        if y.shape[0] != np.asarray(x).shape[0]:
            raise ValueError("x and y row counts differ")
        if y.shape[0] <= n_terms:
            raise ValueError(
                f"under-determined fit: {y.shape[0]} rows for "
                f"{n_terms} order-{order} terms — the §6 training "
                "blocks oversample at ~2.7x for exactly this reason"
            )
        a = cls._design_matrix(dims, indices, x)
        coeffs, _, rank, _ = np.linalg.lstsq(a, y, rcond=None)
        if rank < n_terms:
            raise ValueError(
                f"rank-deficient design matrix (rank {rank} < "
                f"{n_terms} terms) — the design does not identify the "
                "basis; add draws or reduce order"
            )

        # Analytic LOO via the hat matrix: h_i = a_i (AᵀA)⁻¹ a_iᵀ,
        # e_loo = e / (1 − h). Brute-force-refit equivalence is a
        # committed test (second code path).
        gram = a.T @ a
        h_diag = np.einsum("ij,ji->i", a, np.linalg.solve(gram, a.T))
        residuals = y - a @ coeffs
        denom = 1.0 - h_diag
        if np.any(denom <= 1.0e-12):
            raise ValueError(
                "hat-matrix leverage ~1: a draw is uniquely "
                "determining a basis direction; LOO undefined"
            )
        e_loo = residuals / denom
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        q2 = (
            1.0 - float(np.sum(e_loo**2)) / ss_tot
            if ss_tot > 0.0
            else float("nan")
        )
        return cls(
            dims=dims,
            order=order,
            indices=indices,
            coeffs=np.asarray(coeffs, dtype=np.float64),
            q2=q2,
            loo_rmse=float(np.sqrt(np.mean(e_loo**2))),
        )

    def predict(
        self, x: NDArray[np.floating]
    ) -> NDArray[np.float64]:
        a = self._design_matrix(self.dims, self.indices, x)
        return np.asarray(a @ self.coeffs, dtype=np.float64)
