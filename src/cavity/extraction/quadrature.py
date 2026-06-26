"""SPEC §3 axisymmetric volume-integral primitive.

The 2*pi*r Jacobian enters here, in one place. Every higher-level
quantity (V_mode, p_e, energy norms) calls this primitive; no
re-implementation of axisymmetric integration is permitted elsewhere
in the package.

    int_V g dV = 2*pi * int_int g(r, z) * r * dr * dz
              ~= 2*pi * sum_i w_i * r_i * g_i

where w_i (m^2) are the r-z plane quadrature weights at each node. The
COMSOL-side alternative — building the integral with an `intop(2*pi*r *
<integrand>)` operator — is the other permitted path (SPEC §3); whether
the Jacobian rides in the integrand string or here in the primitive,
the comment `# JACOBIAN` must mark every site that applies 2*pi*r.

Raw `numpy.trapz` on unstructured-mesh nodes is forbidden (SPEC §3 +
the user-supplied hard requirements): without explicit weights there is
no faithful r-weighted volume measure.
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import NDArray


def axisymmetric_volume_integral(
    g: NDArray,
    r_m: NDArray[np.floating],
    weights_m2: NDArray[np.floating],
) -> complex:
    """int_V g dV via the explicit 2*pi*r axisymmetric Jacobian.

    Args:
        g: (N,) integrand values at the nodes; real or complex.
        r_m: (N,) node radii in metres (>= 0).
        weights_m2: (N,) r-z plane quadrature weights in m^2 (> 0).

    Returns:
        The integral in (units of g) * m^3. Returned as a Python
        complex so callers handle complex integrands uniformly; for
        purely real g the imaginary part is exactly 0.
    """
    if g.shape != r_m.shape or r_m.shape != weights_m2.shape:
        raise ValueError(
            "shape mismatch: "
            f"g={g.shape}, r_m={r_m.shape}, weights_m2={weights_m2.shape}"
        )
    # JACOBIAN: axisymmetric volume element dV = 2*pi * r * dr * dz applied
    # explicitly here. Every higher-level quantity routes through this call;
    # no re-implementation is allowed.
    integrand = weights_m2 * r_m * g
    return complex(2.0 * math.pi * integrand.sum())
