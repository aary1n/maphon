"""V1 heatmap bundles (viz/PLAN.md §3.1–§3.2, §4) — pure build functions.

Presentation layer, not evidence (package docstring). matplotlib-free by
contract (the figure-module `build_data` discipline): the magma LUT is
computed by the export CLI (lazy Agg) and passed IN. Deterministic
bytes: canonical JSON + the §3.1 array transport; headers stamp INPUT
identity only (R3 — no clock, no HEAD sha, ever).

Scenario lattice (§4, flood-only per R2): axes k × deposition × h_conv
× h_rad × base BC, enumerated in lexicographic axis-index order; the
all-insulated cells (base = Robin ∧ h_eff = 0) are structurally invalid
(CylinderSpec rejects them — no steady state) and are recorded in the
manifest, not silently missing. h_eff = h_conv + h_rad applies jointly
to side + top through the committed composition
`radiation.h_top_with_radiation`; a Robin base takes the same h_eff.
The D1 fork is base-only (a Dirichlet side flips to the J₀-zeros branch
with its documented ~1/N flood deficit tail — excluded from v1, §4).

Mode truncation (recorded, never silent): trailing theta rows whose
per-mode field contribution is < TRUNCATION_REL relative to the field
peak are dropped; `n_kept` and the summed dropped-tail bound
`truncation_bound_rel` ride each scenario bundle. Prefix semantics keep
the first-N partial-sum identity (the mode-count-slider licence) exact
for every n ≤ n_kept.
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import itertools
import json
import math
from dataclasses import dataclass

import numpy as np

from cavity.figures import _style
from cavity.figures.f3_delta_t_map import (
    CAPTION as F3_CAPTION,
)
from cavity.figures.f3_delta_t_map import (
    N_MODES,
    N_R,
    N_Z,
    P_ABS_W,
)
from cavity.provenance.constants import (
    CRYSTAL,
    EMISSIVITY_PTP,
    H_CONV_AIR,
    K_PTP,
    L_ABS_PUMP,
)
from cavity.thermal.cylinder import CylinderSpec, PumpSource, SurfaceBC, solve
from cavity.thermal.radiation import h_rad_linearized, h_top_with_radiation
from cavity.viz import captions

SCHEMA_VERSION = 1
P_REF_W = P_ABS_W  # 0.05 W — ILLUSTRATIVE (imported from F3, never retyped)
P_DISPLAY_MAX_W = 0.2  # 0–200 mW display range — a stated display choice (§4)
H_RAD_T_AMB_K = 300.0  # the F3 / radiation.py fixed-ambient convention
N_GRID = (4, 8, 16, 32, 48, 64)  # vol-avg/deficit readout steps (§3.2)
TRUNCATION_REL = 1e-9  # per-mode field-contribution drop threshold (§3.2)
GZIP_MIN_SAVING = 0.30  # below this measured saving, wrappers embed plain JSON

# --- axes (§1.5 committed sources; value order fixes the lattice order) ------

# (slug, committed constant reference, value)
_K_AXIS = (
    ("k-lo", "K_PTP.k_band_lo_w_m_k", K_PTP.k_band_lo_w_m_k),
    ("k-mid", "K_PTP.k_mid_w_m_k", K_PTP.k_mid_w_m_k),
    ("k-hi", "K_PTP.k_band_hi_w_m_k", K_PTP.k_band_hi_w_m_k),
)

# (slug, axial_form, l_abs grid index or None)
_DEP_AXIS = tuple(
    (f"bl-{round(l_abs * 1e6)}um", "beer_lambert", i)
    for i, l_abs in enumerate(L_ABS_PUMP.l_abs_scoping_grid_m)
) + (("uniform", "uniform", None), ("surface", "surface", None))

# (slug, committed constant reference or None [the §7.T4 h → 0 floor], value)
_HC_AXIS = (
    ("hc-0", None, 0.0),
    ("hc-5", "H_CONV_AIR.h_band_lo_w_m2_k", H_CONV_AIR.h_band_lo_w_m2_k),
    ("hc-20", "H_CONV_AIR.h_band_hi_w_m2_k", H_CONV_AIR.h_band_hi_w_m2_k),
)

# (slug, epsilon used in the committed composition)
_RAD_AXIS = (("rad-off", 0.0), ("rad-on", EMISSIVITY_PTP.eps_nominal))

# (slug, base kind)
_BASE_AXIS = (("base-dir", "dirichlet"), ("base-rob", "robin"))

_INVALID_REASON = (
    "all-insulated (base = Robin and h_eff = 0): no steady state — "
    "CylinderSpec rejects this cell structurally (viz/PLAN.md §4)"
)


@dataclass(frozen=True)
class HeatmapScenario:
    """One cell of the v1 flood-only lattice: axis indices in the §4 axis
    order (k, deposition, h_conv, h_rad, base)."""

    i_k: int
    i_dep: int
    i_hc: int
    i_rad: int
    i_base: int

    @property
    def scenario_id(self) -> str:
        return "_".join(
            (
                _K_AXIS[self.i_k][0],
                _DEP_AXIS[self.i_dep][0],
                _HC_AXIS[self.i_hc][0],
                _RAD_AXIS[self.i_rad][0],
                _BASE_AXIS[self.i_base][0],
            )
        )

    @property
    def k_w_m_k(self) -> float:
        return _K_AXIS[self.i_k][2]

    @property
    def h_conv_w_m2_k(self) -> float:
        return _HC_AXIS[self.i_hc][2]

    @property
    def epsilon(self) -> float:
        return _RAD_AXIS[self.i_rad][1]

    @property
    def h_eff_w_m2_k(self) -> float:
        """h_conv + h_rad through the committed additive composition
        (ε = 0 returns h_conv exactly — the rad-off branch)."""
        return h_top_with_radiation(self.h_conv_w_m2_k, self.epsilon, H_RAD_T_AMB_K)

    @property
    def base_is_dirichlet(self) -> bool:
        return _BASE_AXIS[self.i_base][1] == "dirichlet"

    @property
    def valid(self) -> bool:
        return self.base_is_dirichlet or self.h_eff_w_m2_k > 0.0

    @property
    def axial_form(self) -> str:
        return _DEP_AXIS[self.i_dep][1]

    @property
    def l_abs_m(self) -> float | None:
        idx = _DEP_AXIS[self.i_dep][2]
        return None if idx is None else L_ABS_PUMP.l_abs_scoping_grid_m[idx]

    @property
    def basis_id(self) -> str:
        """Radial-basis key: (side-BC kind, Bi_s). Bi_s = 0 shares one
        basis across k; nonzero h_eff × k pairs have no Bi collisions
        (computed, PLAN §3.2)."""
        if self.h_eff_w_m2_k == 0.0:
            return "rb_bi0"
        return (
            f"rb_{_K_AXIS[self.i_k][0]}_{_HC_AXIS[self.i_hc][0]}"
            f"_{_RAD_AXIS[self.i_rad][0]}"
        )


def enumerate_scenarios() -> tuple[HeatmapScenario, ...]:
    """The full 288-cell lattice in deterministic lexicographic order over
    axis indices (§3.2); includes the 24 structurally invalid cells."""
    return tuple(
        HeatmapScenario(*idx)
        for idx in itertools.product(
            range(len(_K_AXIS)),
            range(len(_DEP_AXIS)),
            range(len(_HC_AXIS)),
            range(len(_RAD_AXIS)),
            range(len(_BASE_AXIS)),
        )
    )


# the F3 committed worked-example stack (§3.2 default): k mid, Beer-Lambert
# at grid[5] = 200 µm, h_conv band-high, radiation on, Dirichlet base
DEFAULT_SCENARIO = HeatmapScenario(1, 5, 2, 1, 0)
DEFAULT_SCENARIO_ID = DEFAULT_SCENARIO.scenario_id


def heatmap_grids() -> tuple[np.ndarray, np.ndarray]:
    """The shared F3 sampling grid (121 r × 161 z) on the CRYSTAL dims."""
    return (
        np.linspace(0.0, CRYSTAL.diameter_m / 2.0, N_R),
        np.linspace(0.0, CRYSTAL.height_m, N_Z),
    )


def scenario_solver_inputs(sc: HeatmapScenario) -> tuple[CylinderSpec, PumpSource]:
    """Committed-constant solver inputs for a lattice cell (flood radial
    profile per R2; h_eff jointly on side + top, Robin base takes the same
    h_eff)."""
    if not sc.valid:
        raise ValueError(_INVALID_REASON)
    h_eff = sc.h_eff_w_m2_k
    base = SurfaceBC.dirichlet() if sc.base_is_dirichlet else SurfaceBC.robin(h_eff)
    spec = CylinderSpec(
        CRYSTAL.diameter_m / 2.0,
        CRYSTAL.height_m,
        sc.k_w_m_k,
        SurfaceBC.robin(h_eff),
        SurfaceBC.robin(h_eff),
        base,
    )
    src = PumpSource(P_REF_W, sc.axial_form, "flood", l_abs_m=sc.l_abs_m)
    return spec, src


# --- status flags (captions.py tokens only — R4) -----------------------------

_ALWAYS_FLAGS = (
    captions.FLAG_ILLUSTRATIVE,  # P_ref is illustrative
    captions.FLAG_PLANNING_ASSUMPTIONS,  # D1–D7 ride every cell
    captions.FLAG_LINEAR_IN_P,  # the P-slider licence
    captions.FLAG_FLOOD_D3,  # flood-only lattice (R2)
)
_K_FLAGS = (captions.FLAG_K_FLOOR_LIQUID,)
_BL_FLAGS = (
    captions.FLAG_UNSOURCED_SCOPING,
    captions.FLAG_NOMINAL_DOPING,
    captions.FLAG_END_FIRE_D2,
)
_AXIAL_FLAGS = (captions.FLAG_END_FIRE_D2,)  # uniform/surface: axial family
_HC_FLAGS = (captions.FLAG_H_CONV_CEILING,)
_RAD_ON_FLAGS = (captions.FLAG_H_RAD_BAND,)
_BASE_DIR_FLAGS = (captions.FLAG_BASE_DIRICHLET_D1,)


def _scenario_flags(sc: HeatmapScenario) -> list[str]:
    flags = list(_ALWAYS_FLAGS) + list(_K_FLAGS) + list(_HC_FLAGS)
    flags += _BL_FLAGS if sc.axial_form == "beer_lambert" else _AXIAL_FLAGS
    if sc.epsilon > 0.0:
        flags += _RAD_ON_FLAGS
    if sc.base_is_dirichlet:
        flags += _BASE_DIR_FLAGS
    return captions.ordered_flags(flags)


def _scenario_constants(sc: HeatmapScenario) -> dict[str, float]:
    """Input identity: committed-constant references consumed by this cell
    (name → value, emitted from the imported objects — R3 deterministic)."""
    consts: dict[str, float] = {
        "CRYSTAL.diameter_m": CRYSTAL.diameter_m,
        "CRYSTAL.height_m": CRYSTAL.height_m,
        _K_AXIS[sc.i_k][1]: sc.k_w_m_k,
    }
    dep_idx = _DEP_AXIS[sc.i_dep][2]
    if dep_idx is not None:
        consts[f"L_ABS_PUMP.l_abs_scoping_grid_m[{dep_idx}]"] = sc.l_abs_m
    hc_ref = _HC_AXIS[sc.i_hc][1]
    if hc_ref is not None:
        consts[hc_ref] = sc.h_conv_w_m2_k
    if sc.epsilon > 0.0:
        consts["EMISSIVITY_PTP.eps_nominal"] = sc.epsilon
        consts[
            f"h_rad_linearized(EMISSIVITY_PTP.eps_nominal, {H_RAD_T_AMB_K})"
        ] = h_rad_linearized(sc.epsilon, H_RAD_T_AMB_K)
    return consts


# --- deterministic serialisation (§3.1) --------------------------------------

_DTYPES = {"f4": "<f4", "f8": "<f8", "u1": "u1"}


def encode_array(arr, dtype: str) -> dict:
    """§3.1 array transport: little-endian row-major raw bytes, base64."""
    cast = np.ascontiguousarray(np.asarray(arr), dtype=_DTYPES[dtype])
    return {
        "dtype": dtype,
        "shape": list(cast.shape),
        "b64": base64.b64encode(cast.tobytes()).decode("ascii"),
    }


def decode_array(obj: dict) -> np.ndarray:
    raw = base64.b64decode(obj["b64"])
    return np.frombuffer(raw, dtype=_DTYPES[obj["dtype"]]).reshape(obj["shape"])


def canonical_json_bytes(obj) -> bytes:
    """Canonical bytes — the hash-pin substrate: sorted keys, compact
    separators, ASCII-escaped, trailing newline, UTF-8. NaN/inf are
    rejected outright (allow_nan=False): a non-finite value in a bundle
    is a build error, never silently emitted."""
    return (
        json.dumps(
            obj,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def js_wrapper(name: str, canonical: bytes, encoding: str) -> bytes:
    """Script-tag-loadable delivery (§3.1, the file:// constraint):
    window.VIZ_DATA["<name>"] = base64(gzip(canonical JSON)) — or base64
    of the plain JSON when the measured gzip saving fell below 30%. The
    loader discriminates by the gzip magic bytes after base64 decode; the
    hash pin is always on the DECOMPRESSED canonical JSON."""
    if encoding == "gzip":
        blob = gzip.compress(canonical, compresslevel=9, mtime=0)
    elif encoding == "plain":
        blob = canonical
    else:
        raise ValueError(f"unknown wrapper encoding {encoding!r}")
    b64 = base64.b64encode(blob).decode("ascii")
    return (
        "window.VIZ_DATA = window.VIZ_DATA || {};\n"
        f'window.VIZ_DATA["{name}"] = "{b64}";\n'
    ).encode("ascii")


def unwrap_js(wrapped: bytes) -> bytes:
    """Recover the canonical JSON bytes from a .js wrapper (gzip-sniffed)."""
    text = wrapped.decode("ascii")
    start = text.index('= "') + 3
    end = text.index('";', start)
    blob = base64.b64decode(text[start:end])
    if blob[:2] == b"\x1f\x8b":
        return gzip.decompress(blob)
    return blob


def _envelope(generator: str, inputs: dict, flags: list[str], payload: dict) -> dict:
    return {
        "viz_bundle_schema_version": SCHEMA_VERSION,
        "view": "heatmap",
        "generator": generator,
        "inputs": inputs,
        "caption": F3_CAPTION,
        "status_flags": flags,
        "payload": payload,
    }


# --- bundle builders ---------------------------------------------------------


def heatmap_bundle(scenario: HeatmapScenario) -> dict:
    """One scenario bundle (§3.2): truncated per-mode theta rows + scalars
    + the N-grid readout steps, at P_ref (the client rescales by exact
    linearity). Raises on a structurally invalid cell."""
    spec, src = scenario_solver_inputs(scenario)
    sol = solve(spec, src, n_modes=N_MODES)
    r_m, z_m = heatmap_grids()
    dec = sol.modal_decomposition(r_m, z_m)
    theta = dec["theta_k"]  # (N_MODES, N_Z), kelvin at P_ref

    # prefix truncation: |J₀| ≤ 1 with equality at r = 0, so a row's field
    # contribution is bounded by max|theta row|
    row_bound = np.abs(theta).max(axis=1)
    field = np.einsum("ni,nj->ij", theta, dec["radial_basis"])
    peak_ref = float(np.abs(field).max())
    keep = np.nonzero(row_bound >= TRUNCATION_REL * peak_ref)[0]
    n_kept = int(keep.max()) + 1 if keep.size else 1
    truncation_bound_rel = float(row_bound[n_kept:].sum() / peak_ref)

    bp = sol.boundary_power_w()
    n_grid: dict[str, dict[str, float]] = {}
    for n in N_GRID:
        s = sol if n == N_MODES else solve(spec, src, n_modes=n)
        bpn = bp if n == N_MODES else s.boundary_power_w()
        n_grid[str(n)] = {
            "peak_k": float(s.peak_k),
            "vol_avg_k": float(s.volume_average_k()),
            "deficit_rel": abs(P_REF_W - bpn["total"]) / P_REF_W,
        }

    payload = {
        "scenario_id": scenario.scenario_id,
        "basis_id": scenario.basis_id,
        "theta_k": encode_array(theta[:n_kept], "f4"),
        "f_hat": encode_array(dec["f_hat"][:n_kept], "f4"),
        "n_kept": n_kept,
        "truncation_bound_rel": truncation_bound_rel,
        "peak_k": float(sol.peak_k),
        "vol_avg_k": float(sol.volume_average_k()),
        "boundary_power_w": {k: float(v) for k, v in bp.items()},
        "deficit_rel": abs(P_REF_W - bp["total"]) / P_REF_W,
        "tail_estimate_rel": float(sol.tail_estimate_rel("peak")),
        "n_grid_scalars": n_grid,
    }
    inputs = {
        "constants": _scenario_constants(scenario),
        "solver": {"n_modes": N_MODES, "grid_r": N_R, "grid_z": N_Z},
        "scenario": {
            "id": scenario.scenario_id,
            "axes": [
                scenario.i_k,
                scenario.i_dep,
                scenario.i_hc,
                scenario.i_rad,
                scenario.i_base,
            ],
            "k_w_m_k": scenario.k_w_m_k,
            "axial_form": scenario.axial_form,
            "l_abs_m": scenario.l_abs_m,
            "radial_form": "flood",
            "h_conv_w_m2_k": scenario.h_conv_w_m2_k,
            "h_rad_w_m2_k": scenario.h_eff_w_m2_k - scenario.h_conv_w_m2_k,
            "h_eff_w_m2_k": scenario.h_eff_w_m2_k,
            "base_bc": _BASE_AXIS[scenario.i_base][1],
            "p_ref_w": P_REF_W,
        },
    }
    return _envelope(
        "cavity.viz.bundles:heatmap_bundle",
        inputs,
        _scenario_flags(scenario),
        payload,
    )


def radial_basis_bundle(sc: HeatmapScenario) -> dict:
    """The deduplicated radial basis for a scenario's (side kind, Bi_s)
    key (§3.2): exact float64 eigenvalues + f32 J₀ rows on the shared r
    grid. Rows pair index-for-index with any sharing scenario's theta_k
    (identical solve-path floats: same Bi expression, same grid)."""
    radius = CRYSTAL.diameter_m / 2.0
    r_m, _ = heatmap_grids()
    spec, src = scenario_solver_inputs(sc)
    sol = solve(spec, src, n_modes=N_MODES)
    dec = sol.modal_decomposition(r_m, np.array([0.0]))
    bi = sc.h_eff_w_m2_k * radius / sc.k_w_m_k
    flags = list(_ALWAYS_FLAGS[1:2])  # planning-assumption BCs define Bi
    if bi > 0.0:
        flags += _K_FLAGS + _HC_FLAGS
        if sc.epsilon > 0.0:
            flags += _RAD_ON_FLAGS
    payload = {
        "basis_id": sc.basis_id,
        "side_bc": "robin",
        "bi_side": bi,
        "has_constant_mode": bool(bi == 0.0),
        "x_n": encode_array(dec["x_n"], "f8"),
        "radial_basis": encode_array(dec["radial_basis"], "f4"),
    }
    inputs = {
        "constants": {
            "CRYSTAL.diameter_m": CRYSTAL.diameter_m,
            _K_AXIS[sc.i_k][1]: sc.k_w_m_k,
        },
        "solver": {"n_modes": N_MODES, "grid_r": N_R},
    }
    return _envelope(
        "cavity.viz.bundles:radial_basis_bundle",
        inputs,
        captions.ordered_flags(flags),
        payload,
    )


def _axes_manifest() -> list[dict]:
    """The §1.5 axis table as data: per axis id, committed source, ordered
    values, display labels, per-value flag lists (captions.py tokens)."""
    k_axis = {
        "id": "k",
        "source": "K_PTP",
        "unit": "W m^-1 K^-1",
        "value_ids": [v[0] for v in _K_AXIS],
        "values": [v[2] for v in _K_AXIS],
        "labels": [
            "k = 0.1 (band floor)",
            "k = 0.316 (geometric band mid)",
            "k = 1.0 (band ceiling)",
        ],
        "flags": [captions.ordered_flags(_K_FLAGS) for _ in _K_AXIS],
    }
    dep_axis = {
        "id": "deposition",
        "source": "PumpSource.axial_form × L_ABS_PUMP.l_abs_scoping_grid_m",
        "unit": "m (l_abs, beer_lambert values only)",
        "value_ids": [v[0] for v in _DEP_AXIS],
        "values": [
            None if v[2] is None else L_ABS_PUMP.l_abs_scoping_grid_m[v[2]]
            for v in _DEP_AXIS
        ],
        "labels": [
            *(
                f"Beer–Lambert, l_abs = {round(l_abs * 1e6)} µm"
                for l_abs in L_ABS_PUMP.l_abs_scoping_grid_m
            ),
            "uniform (l_abs ≫ L limit)",
            "surface (exact l_abs → 0 limit)",
        ],
        "flags": [
            captions.ordered_flags(
                _BL_FLAGS if v[1] == "beer_lambert" else _AXIAL_FLAGS
            )
            for v in _DEP_AXIS
        ],
    }
    hc_axis = {
        "id": "h_conv",
        "source": "H_CONV_AIR",
        "unit": "W m^-2 K^-1",
        "value_ids": [v[0] for v in _HC_AXIS],
        "values": [v[2] for v in _HC_AXIS],
        "labels": [
            "h_conv = 0 (§7.T4 floor)",
            "h_conv = 5 (band low)",
            "h_conv = 20 (band high)",
        ],
        "flags": [captions.ordered_flags(_HC_FLAGS) for _ in _HC_AXIS],
    }
    rad_axis = {
        "id": "h_rad",
        "source": "h_rad_linearized(EMISSIVITY_PTP.eps_nominal, 300.0)",
        "unit": "W m^-2 K^-1",
        "value_ids": [v[0] for v in _RAD_AXIS],
        "values": [h_rad_linearized(v[1], H_RAD_T_AMB_K) for v in _RAD_AXIS],
        "labels": ["h_rad off", "h_rad on (ε = 0.90, 300 K)"],
        "flags": [
            [],
            captions.ordered_flags(_RAD_ON_FLAGS),
        ],
    }
    base_axis = {
        "id": "base",
        "source": "D1 (planning assumption, §11 item-10)",
        "unit": None,
        "value_ids": [v[0] for v in _BASE_AXIS],
        "values": [v[1] for v in _BASE_AXIS],
        "labels": [
            "Dirichlet base (D1 worked example)",
            "Robin base (same h_eff as side/top)",
        ],
        "flags": [captions.ordered_flags(_BASE_DIR_FLAGS), []],
    }
    radial_axis = {
        "id": "radial_profile",
        "source": "D3 (F3-pinned; flood-only per ruling R2)",
        "unit": None,
        "value_ids": ["flood"],
        "values": ["flood"],
        "labels": ["flood"],
        "flags": [captions.ordered_flags((captions.FLAG_FLOOD_D3,))],
        # reserved slot names in the schema, UNPOPULATED (R2): populating
        # them requires a committed parameter source that does not exist
        "reserved_slots": ["disc", "gaussian"],
    }
    return [k_axis, dep_axis, hc_axis, rad_axis, base_axis, radial_axis]


def build_heatmap_bundles(lut_rgb_u8: np.ndarray) -> dict:
    """Build the full v1 bundle set (scenarios + bases + index manifest).

    Returns {
      "bundles":   {relname: bundle dict}   (relname e.g. "scenario/<id>"),
      "canonical": {relname: canonical JSON bytes},
      "sha256":    {relname: hex digest},
      "wrapper_encoding": "gzip" | "plain"  (the §3.1 ≥30%-saving rule,
                          measured on scenario + bases canonical bytes),
      "gzip_saving_frac": measured saving,
    }
    The index manifest records every scenario (invalid cells with their
    structural reason), every basis, the per-bundle sha256 pins, and the
    §3.2 shared block (grids, P_ref, LUT, default scenario, max deficit).
    """
    lut = np.asarray(lut_rgb_u8)
    if lut.shape != (256, 3) or lut.dtype != np.uint8:
        raise ValueError("LUT must be a 256×3 uint8 RGB array")

    bundles: dict[str, dict] = {}
    canonical: dict[str, bytes] = {}
    shas: dict[str, str] = {}
    scenario_rows: list[dict] = []
    basis_rows: list[dict] = []
    basis_seen: dict[str, HeatmapScenario] = {}
    max_deficit = 0.0

    for sc in enumerate_scenarios():
        row: dict = {
            "id": sc.scenario_id,
            "axes": [sc.i_k, sc.i_dep, sc.i_hc, sc.i_rad, sc.i_base],
        }
        if not sc.valid:
            row["invalid"] = _INVALID_REASON
            scenario_rows.append(row)
            continue
        bundle = heatmap_bundle(sc)
        name = f"scenario/{sc.scenario_id}"
        raw = canonical_json_bytes(bundle)
        bundles[name] = bundle
        canonical[name] = raw
        shas[name] = sha256_hex(raw)
        row.update(
            {
                "basis_id": sc.basis_id,
                "sha256": shas[name],
                "peak_k": bundle["payload"]["peak_k"],
                "vol_avg_k": bundle["payload"]["vol_avg_k"],
            }
        )
        scenario_rows.append(row)
        max_deficit = max(max_deficit, bundle["payload"]["deficit_rel"])
        basis_seen.setdefault(sc.basis_id, sc)

    for basis_id, sc in basis_seen.items():
        bundle = radial_basis_bundle(sc)
        name = f"bases/{basis_id}"
        raw = canonical_json_bytes(bundle)
        bundles[name] = bundle
        canonical[name] = raw
        shas[name] = sha256_hex(raw)
        basis_rows.append(
            {
                "id": basis_id,
                "sha256": shas[name],
                "bi_side": bundle["payload"]["bi_side"],
                "has_constant_mode": bundle["payload"]["has_constant_mode"],
            }
        )

    # §3.1 compression decision, measured on the committed payload bundles
    # (the index does not exist yet — it records the outcome)
    plain_total = sum(len(b) for b in canonical.values())
    gz_total = sum(
        len(gzip.compress(b, compresslevel=9, mtime=0)) for b in canonical.values()
    )
    saving = 1.0 - gz_total / plain_total
    encoding = "gzip" if saving >= GZIP_MIN_SAVING else "plain"

    r_m, z_m = heatmap_grids()
    shared = {
        "r_mm": encode_array(r_m * 1e3, "f8"),
        "z_mm": encode_array(z_m * 1e3, "f8"),
        "p_ref_w": P_REF_W,
        "p_display_max_w": P_DISPLAY_MAX_W,
        "n_modes": N_MODES,
        "truncation_rel": TRUNCATION_REL,
        "lut_name": _style.SEQUENTIAL_THERMAL,
        "lut_rgb_u8": encode_array(lut, "u1"),
        "default_scenario_id": DEFAULT_SCENARIO_ID,
        "max_deficit_rel": max_deficit,
        "wrapper_encoding": encoding,
        "canonical_bytes_total": plain_total,
    }
    index = _envelope(
        "cavity.viz.bundles:build_heatmap_bundles",
        {
            "constants": {
                "CRYSTAL.diameter_m": CRYSTAL.diameter_m,
                "CRYSTAL.height_m": CRYSTAL.height_m,
                "K_PTP.k_band_lo_w_m_k": K_PTP.k_band_lo_w_m_k,
                "K_PTP.k_mid_w_m_k": K_PTP.k_mid_w_m_k,
                "K_PTP.k_band_hi_w_m_k": K_PTP.k_band_hi_w_m_k,
                "H_CONV_AIR.h_band_lo_w_m2_k": H_CONV_AIR.h_band_lo_w_m2_k,
                "H_CONV_AIR.h_band_hi_w_m2_k": H_CONV_AIR.h_band_hi_w_m2_k,
                "EMISSIVITY_PTP.eps_nominal": EMISSIVITY_PTP.eps_nominal,
                f"h_rad_linearized(EMISSIVITY_PTP.eps_nominal, {H_RAD_T_AMB_K})": (
                    h_rad_linearized(EMISSIVITY_PTP.eps_nominal, H_RAD_T_AMB_K)
                ),
                **{
                    f"L_ABS_PUMP.l_abs_scoping_grid_m[{i}]": l_abs
                    for i, l_abs in enumerate(L_ABS_PUMP.l_abs_scoping_grid_m)
                },
            },
            "solver": {"n_modes": N_MODES, "grid_r": N_R, "grid_z": N_Z},
        },
        captions.ordered_flags(captions.FLAG_ORDER),
        {
            "axes": _axes_manifest(),
            "scenarios": scenario_rows,
            "bases": basis_rows,
            "shared": shared,
        },
    )
    raw = canonical_json_bytes(index)
    bundles["index"] = index
    canonical["index"] = raw
    shas["index"] = sha256_hex(raw)
    return {
        "bundles": bundles,
        "canonical": canonical,
        "sha256": shas,
        "wrapper_encoding": encoding,
        "gzip_saving_frac": saving,
    }


def _self_check() -> None:
    """Cheap internal consistency guards evaluated at import: the lattice
    arithmetic of PLAN §4 (fail loudly if an axis edit breaks the count)."""
    scenarios = enumerate_scenarios()
    n_valid = sum(1 for s in scenarios if s.valid)
    if len(scenarios) != 288 or n_valid != 264:
        raise AssertionError(
            f"lattice arithmetic broke: {len(scenarios)} cells, {n_valid} valid"
        )
    if not DEFAULT_SCENARIO.valid or math.isclose(
        DEFAULT_SCENARIO.h_eff_w_m2_k, 0.0
    ):
        raise AssertionError("default scenario must be a valid Robin-side cell")


_self_check()
