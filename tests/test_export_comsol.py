"""Export layer, live tier (requires_comsol): solve -> export -> validate.

The one COMSOL-gated export test (§E of the export pass): a real
`run_forward_model` solve (the §8 PEC + lossy configuration of the live
gate — assumed a/L = 0.5 puck, geometry-independent closed check), then
`export_bundle` on the persisted SolveRecord and the full contract
validation: unit-energy normalisation holds on live fields, the bundle
p_e equals the extraction p_e, the picked mode is CONSUMED from
`picked_index` (never re-selected), and the bundle round-trips
identically. Everything else about the export layer is licence-free by
construction and lives in tests/test_export_schema.py.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.export import export_bundle, load_bundle, validate_bundle
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.provenance import GEOM

pytestmark = pytest.mark.requires_comsol


def test_live_solve_export_validate_round_trip(comsol_client, tmp_path):
    from cavity.forward_model.mesh import MeshConfig
    from cavity.forward_model.runner import (
        material_spec_for,
        run_forward_model,
    )

    # The live gate's §8 PEC + lossy configuration (providers.py):
    # assumed a/L = 0.5 puck, search near the ~3.1 GHz estimate, the
    # §2 e2e finest ladder mesh level.
    geom = CavityGeometry.from_nominal(
        DielectricShape.PUCK,
        dielectric_height_m=2.0 * GEOM.dielectric_radius_m,
    )
    study = EigenStudyConfig(
        wall_bc=WallBC.PEC, search_hz=3.1e9, n_modes=12
    )
    result = run_forward_model(
        geom,
        study,
        material_spec_for(study),
        MeshConfig(dielectric_max_h_m=1.25e-4, air_max_h_m=5.0e-4),
        client=comsol_client,
        cache_root=tmp_path / "solves",
    )
    record = result.record

    out = export_bundle(record, tmp_path / "bundle")
    bundle = validate_bundle(out)  # includes the unit-energy invariant
    summary = bundle.meta["summary"]

    # Bundle p_e == extraction p_e (same arrays, same primitive).
    assert summary["p_e"] == pytest.approx(
        result.extraction.p_e, rel=1.0e-12
    )
    assert summary["q"] == pytest.approx(result.extraction.q, rel=1.0e-12)

    # Picked mode consumed from picked_index, not re-selected.
    assert bundle.meta["solve"]["picked_index"] == record.picked_index
    assert summary["f_real_hz"] == float(
        record.spectrum_f_real_hz[record.picked_index]
    )
    assert summary["f_imag_hz"] == float(
        record.spectrum_f_imag_hz[record.picked_index]
    )

    # Live fields normalise to unit total energy (explicit re-check on
    # top of validate_bundle's invariant).
    raw_total = bundle.meta["normalisation"]["raw_total_energy_j"]
    assert raw_total > 0.0
    scale = 1.0 / np.sqrt(raw_total)
    assert np.array_equal(
        bundle.arrays["e_complex"], record.field_sample.e_complex * scale
    )
    assert np.array_equal(
        bundle.arrays["h_complex"], record.field_sample.h_complex * scale
    )

    # Round trip is bit-identical.
    again = load_bundle(out)
    for key, arr in bundle.arrays.items():
        assert np.array_equal(arr, again.arrays[key])
