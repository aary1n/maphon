# EM Field-Export Schema

**`export_schema_version: 1`** — this document is version-locked to the
bundles that carry it. A copy ships inside every bundle as
`FIELD_EXPORT_SCHEMA.md`, so no repository access is needed to consume one.

Reference implementation: `cavity.export` (writer `export_bundle`, validator
`validate_bundle`) in the STO TE01δ maser-cavity repository; this document is
authoritative for the contract, the code is its implementation.

## Changelog

| Version | Date | Change |
|---|---|---|
| 1 | 2026-07-09 | Initial schema: unit-energy-normalised (r, z) field maps, §7.T5(b) weight functionals, full §1 reproducibility metadata. |

Versioning policy: **stable keys are contract**. Renaming a key, changing its
units, or changing its semantics bumps `export_schema_version`, and readers
must refuse versions they do not implement (`load_bundle` does). *Adding* new
keys within a version is allowed; readers must ignore keys they do not know.

---

## 1. Purpose and consumers

One bundle = one solved eigenmode of the 2-D axisymmetric COMSOL forward
model (SPEC §2), exported with everything four consumers need:

1. **Observable-b differential detuning** (SPEC §7.T5(b)): the cavity-arm
   weight `w_e_per_m3` (+ companion `p_e`) and the spin-arm weight
   `w_spin_per_m3`, as densities on the (r, z) grid, co-registerable with the
   `cavity.thermal` ΔT fields. The §6T temperature coefficients are NOT here —
   they stay single-sourced in `cavity.provenance`.
2. **Maxwell–Bloch handoff** (Carrera, Jiang, Shu, Wu, Oxborrow,
   arXiv:2412.21166; consumers have **no repo access**): complex H over the
   gain region, total stored magnetic energy, f, Q, and the volume-weighted
   coupling-histogram recipe (§6 below).
3. **Layer A surrogate training data** (SPEC §7): the flat, stable-keyed
   scalar row in `export_meta.json → summary`, globbable across bundles and
   auditable back to the solve through `record_hash`.
4. **Inhomogeneous thermal line observable** (SPEC §7.T2 output 3): the
   spin-arm probe measure πᵢ = w_sᵢ·2πrᵢwᵢ (sums to 1) is exactly the
   `weights` argument of `cavity.thermal.broadening.line_observable_from_samples`.

The weights *serve* the §7.T5(b) prediction (spin arm calibrated, cavity arm
predicted); nothing in a bundle runs either arm.

## 2. Bundle layout

```
<bundle>/
  fields.npz              # arrays, see §4
  export_meta.json        # metadata, see §8
  FIELD_EXPORT_SCHEMA.md  # this document, copied in
```

`fields.npz` is a standard NumPy zip archive: readable from Python
(`numpy.load`), Julia (`NPZ.jl`), or anything that reads zip + NPY. No HDF5,
no custom binary.

## 3. Conventions (read before touching any array)

- **Units:** SI throughout. Coordinates in metres, E in V/m, H in A/m,
  energies in joules.
- **Frequency:** cyclic hertz (Hz), **never** angular rad/s. See the κ trap
  in §7.
- **Phasor convention:** e^{+iωt}. Complex permittivity
  ε_r = ε_r′·(1 − i·tan δ). **Im(f) > 0 ⇔ temporal decay.**
- **Q convention:** Q = f′/(2 f″) from the bare complex eigenfrequency
  (SPEC §11 item 4). Bundles carry Q pre-computed; consume it, do not
  re-derive it from `emw.Qfactor`-style interface scalars.
- **Geometry:** 2-D axisymmetric half-plane (r ≥ 0, z), azimuthal index
  **m = 0** (declared in metadata). Field components are cylindrical, ordered
  **(r, φ, z)** — right-handed (r̂, φ̂, ẑ).
- **Volume element:** dV = 2πr dr dz. See the trap in §6.
- **Grid:** flattened tensor-product (r, z) grid, `'ij'` ordering (r varies
  slowest). `shape_rz = (n_r, n_z)`; reshape any (N,) array via
  `arr.reshape(n_r, n_z)`.

**3-D reconstruction** (m = 0): field(r, φ, z) = field(r, z) for every φ —
components are given in the *local* cylindrical basis at each azimuth. To get
Cartesian components at azimuth φ:
E_x = E_r cos φ − E_φ sin φ, E_y = E_r sin φ + E_φ cos φ, E_z = E_z.

**Boundary fidelity caveat:** masks are *nodal*. A node whose trapezoid cell
straddles a material boundary is assigned wholly to one side, so mask-based
sub-region integrals carry an O(h) boundary-staircase error (empirically ~1e-2
class at the 201×301 default grid for sub-regions cut mid-domain; the
STO-boundary residual visible in the frozen gate run's closed-form check is
5.6e-5). Refine the export grid — not the mesh — if a masked integral's
convergence stalls; mesh convergence itself is SPEC §2's discipline.

## 4. Array keys (`fields.npz`)

N = number of grid nodes (= n_r·n_z); M = number of solved modes.

| Key | Shape | Dtype | Units | Definition |
|---|---|---|---|---|
| `r_m` | (N,) | float64 | m | Node radius. |
| `z_m` | (N,) | float64 | m | Node axial coordinate. |
| `weights_m2` | (N,) | float64 | m² | r–z **plane** quadrature weight (composite trapezoid). Does NOT include 2πr. |
| `shape_rz` | (2,) | int64 | — | (n_r, n_z) for reshaping, `'ij'` order. |
| `e_complex` | (N, 3) | complex128 | V/m | E of the picked mode, (r, φ, z), **unit-energy normalised** (§5). |
| `h_complex` | (N, 3) | complex128 | A/m | H of the picked mode, (r, φ, z), **unit-energy normalised** (§5). |
| `eps_r_complex` | (N,) | complex128 | — | Relative permittivity ε_r′(1 − i·tan δ) at each node. |
| `dielectric_mask` | (N,) | bool | — | True inside the STO. |
| `gain_region_mask` | (N,) | bool | — | True inside the gain region. **Check `summary.gain_mask_is_fallback` first** — see §9. |
| `w_e_per_m3` | (N,) | float64 | m⁻³ | Cavity-arm weight density (§5a): ∫ w_E dV = 1 over `dielectric_mask`. |
| `w_spin_per_m3` | (N,) | float64 | m⁻³ | Spin-arm weight density (§5b): ∫ w_s dV = 1 over `gain_region_mask`. |
| `spectrum_f_real_hz` | (M,) | float64 | Hz | Re(f) of every solved mode. |
| `spectrum_f_imag_hz` | (M,) | float64 | Hz | Im(f) of every solved mode (> 0 ⇔ decay). |
| `spectrum_q_emw` | (M,) | float64 | — | *(optional)* COMSOL `emw.Qfactor` per mode — cross-check only, never the primary Q. |

The **picked mode** (the TE01δ the bundle is about) is
`meta.solve.picked_index` into the `spectrum_*` arrays; its fields are the
`e_complex`/`h_complex` arrays and its scalars are in `meta.summary`. Mode
selection was done by field symmetry (SPEC §2), not eigenvalue order — the
criteria are recorded in `meta.mode_selection`; do not re-pick.

## 5. Normalisation, energies, and the weight functionals

### Normalisation: unit total stored EM energy

COMSOL eigenmode amplitudes are arbitrarily scaled; cross-solve comparison
(consumer 3) demands a convention. Stored fields satisfy

    U = U_E + U_H = 1 J,
    U_E = ∫ ε₀ ε_r′ |E|²/4 dV,   U_H = ∫ μ₀ |H|²/4 dV,

time-averaged peak-phasor densities, integrated with dV = 2πr dr dz. The raw
scale is recoverable: multiply both fields by
√(`normalisation.raw_total_energy_j`). Raw U_E, U_H are stored separately;
`u_e_fraction` ≈ 0.5 is a mode-health diagnostic (U_E = U_H at resonance).
All weights below are scale-invariant, so this convention costs consumers
nothing.

### (a) Cavity arm — `w_e_per_m3`

Bethe–Schwinger cavity perturbation for a small isotropic Δε confined to the
dielectric, with a uniform coefficient over the STO:

    δf = [−(f/2)·(dε_r/dT)/ε_r′]_§6T · p_e · ⟨ΔT⟩_wE,
    ⟨ΔT⟩_wE = ∫_STO w_E(r) ΔT(r) dV,
    w_E(r) = ε_r′(r)|E(r)|² / ∫_STO ε_r′|E|² dV,   ∫_STO w_E dV = 1.

The §6T bracket (`cavity_df_dt_hz_per_k`, +2.73 MHz/K at 300 K) lives in the
repo's provenance layer, not in bundles. The companion scalar
`summary.p_e` (STO share of total electric energy; frozen-gate value 0.9977)
carries the −0.2 % bookkeeping explicitly — no weight silently absorbs it.
ε_r′ = Re(ε_r): the imaginary part is loss, not stored energy. The uniform-ΔT
limit collapses to δf = (df/dT)·p_e·ΔT.

### (b) Spin arm — `w_spin_per_m3`

A spin at **r** couples to the mode with strength g(**r**) ∝ |H_proj(**r**)|
(Breeze et al. 2017, npj Quantum Inf. 3, 40: g_s = γ√(μ₀hf/2V_mode);
position-resolved form = g_j of arXiv:2412.21166). Linear-response ensemble
observables are g²-weighted:

    w_s(r) = |H_proj(r)|² / ∫_gain |H_proj|² dV,   ∫_gain w_s dV = 1.

**Which component is H_proj** is parameterised
(`meta.weights.w_spin_per_m3.projection`):

- `isotropic_h2` (**default**): |H_proj|² = |H|² — the published-framework
  convention (Breeze 2017's g_s; arXiv:2412.21166 uses the |H| magnitude).
- `axis_projected` (u_z) / `site_mixture`: the exact azimuthal average of
  |H·û|² for a molecular-y axis at cos θ = u_z to the cavity axis:
  ⟨|H·û|²⟩_φ = u_z²|H_z|² + ((1−u_z²)/2)(|H_r|²+|H_φ|²). At zero field the
  pentacene X–Z transition is driven through S_y alone (B₁ ∥ molecular y;
  Breeze 2017), so the projection is crystal-orientation- and host-site-
  dependent. **These variants are a derived, unratified refinement** — the
  default matches what the published Maxwell-Bloch framework consumes.

**Orientation caveat (honest gap):** the order-unity orientational dipole
matrix element (W20: "sizeable fraction of unity", never measured) cancels in
every *shape* observable because w_s is normalised; it re-enters only in
absolute-g claims, which bundles do not make. `h_phi_energy_share` (≈0 for a
clean TE01δ) is a mode-purity diagnostic, kept rather than dropped.
B vs H: μ_r = 1 everywhere, so the choice cancels in the normalised weight.

### Probe measure (consumer 4)

πᵢ = w_sᵢ · 2πrᵢ · wᵢ (dimensionless, sums to 1) is the per-node probe
measure over the gain region — the exact `weights` argument of
`line_observable_from_samples(delta_t, weights, df_dt)`. Uniform ΔT ⇒ pure
shift, exactly zero inhomogeneous width.

## 6. The volume-weighting trap + coupling-histogram recipe

**Trap:** the (r, z) nodes are uniform in the *plane*, NOT uniform in volume.
Every histogram, mean, or statistic over the 3-D mode must weight node i by
its volume measure

    dV_i = 2π · r_m[i] · weights_m2[i]     (m³; zero on the axis r = 0).

Binning g_j by *node count* instead of dV skews everything toward the axis.
The published framework's 10-bin coupling histogram (arXiv:2412.21166) is
volume-weighted; the 201×301 default grid is far past convergence for it.

**Worked, dependency-free recipe** (g_j = γ√(μ₀hf/2V_mode^j), with
V_mode^j = ∫μ₀|H|²dV / μ₀|H(r_j)|² — |H| magnitude, no orientation
projection, exactly the published framework's definition):

```python
import json
import numpy as np

b = np.load("fields.npz")
meta = json.load(open("export_meta.json"))

GAMMA_E = 1.76085963e11        # electron gyromagnetic ratio, rad s^-1 T^-1
MU_0    = 1.25663706e-6        # H/m
H_PLANCK = 6.62607015e-34      # J s
f = meta["summary"]["f_real_hz"]          # cyclic Hz

h2 = np.sum(np.abs(b["h_complex"])**2, axis=1)       # |H|^2, A^2/m^2
dv = 2.0 * np.pi * b["r_m"] * b["weights_m2"]        # node volumes, m^3
h2_integral = np.sum(h2 * dv)                        # = 4*U_H/mu0 = ∫|H|^2 dV

gain = b["gain_region_mask"]
v_mode_j = h2_integral / h2[gain]                    # per-spin mode volume, m^3
g_j = GAMMA_E * np.sqrt(MU_0 * H_PLANCK * f / (2.0 * v_mode_j))  # rad s^-1

# volume-weighted histogram — weights=dv, NEVER raw node counts:
counts, edges = np.histogram(g_j, bins=10, weights=dv[gain])
```

Note g_j above is **angular** (rad s⁻¹), matching the Breeze/Wu convention;
divide by 2π for cyclic Hz. γ√(μ₀hf/2V) ≡ γ√(μ₀ħω/2V) since hf = ħω. The
fields' unit-energy normalisation cancels in g_j (it is a ratio); the raw
scale is in the metadata if absolute amplitudes are ever needed.

## 7. Q, κ_c, and the W20 angular-"Hz" trap

Bundles store the **unloaded** Q only (eigensolve: material + wall losses; no
coupling port is modelled). The Maxwell–Bloch cavity decay rate is

    κ_c = 2πf / Q_L      [rad/s]   — LOADED Q_L, angular units,

and the loaded/unloaded split is **not** in this schema version (flagged,
separate pass). De-loading convention: Q₀ = Q_L·(1 + k) with k = 0.2
(Breeze 2017; Wu 2020's coupling is unstated — SPEC §11 item 3).

**Trap, verbatim class (do not re-import it):** W20 (Phys. Rev. Applied 14,
064017) prints *angular* rates with "Hz" labels. Check: κ_c = 2πf/Q_L =
"2.5 MHz" (p. -8) is 2.5×10⁶ **rad s⁻¹**, i.e. a linewidth κ_c/2π ≈ 400 kHz —
exactly W20's own "cavity's line width (approximately 400 kHz)" (p. -7).
Feeding W20's printed values into code expecting /2π units is a silent 2π ≈
6.3× error. Everything in this schema is **cyclic Hz**; convert deliberately.

## 8. Metadata glossary (`export_meta.json`)

Top-level keys (all required):

- **`export_schema_version`** *(int)* — must match this document's version;
  readers refuse otherwise.
- **`conventions`** — machine-readable restatement of §3.
- **`normalisation`** — convention name, `raw_total_energy_j`, `raw_u_e_j`,
  `raw_u_h_j`, `u_e_fraction` (§5).
- **`mode_selection`** — the field-symmetry criteria (thresholds) the §2
  selection uses, their source, and `picked_index_semantics`: `picked_index`
  indexes the `spectrum_*` arrays; the `solve.diagnostics` list covers only
  candidates with Im(f) > 0, so its positions need not align with spectrum
  indices. Selection is field-symmetry primary, proximity only a tiebreak —
  never a hardcoded index.
- **`weights`** — definitions, the spin projection used (+ its evidence
  rung), `gain_mask_is_fallback`, `h_phi_energy_share`,
  `magnetic_filling_factor`, companion `p_e`.
- **`q_loading`** — §7's unloaded-only statement and de-load convention.
- **`solve`** — the full SPEC §1 chain back to the solve: canonical
  `fingerprint` (geometry/materials/mesh/study/grid), `record_hash`,
  `comsol_version`, `mesh_element_count`, `interface_tag`, `picked_index`,
  solve `created_at_utc`, per-candidate mode `diagnostics`,
  `q_emw_cross_check`.
- **`exporter`** — `exported_at_utc`, `package`/`package_version`, and:
  - **`git_commit`** — exporter tree HEAD at export time (recorded, not
    hashed — a runtime fact, like the persistence layer's COMSOL version).
  - **`git_dirty`** *(bool)* — True when `git status --porcelain` was
    non-empty at export time. **A bundle minted from a dirty tree is not
    reproducible from `git_commit` alone**: uncommitted changes may have
    shaped it. Treat `git_dirty: true` bundles as development artifacts;
    handoff and citation-grade bundles must come from a clean tree.
    Both fields are `null` if git was unavailable.
- **`summary`** — the flat scalar row (consumer 3): f′, f″, Q, p_e, V_mode
  (global + local), F_m (both), raw energies, weight diagnostics,
  `record_hash`, `spin_projection_mode`, `gain_mask_is_fallback`. Keys are
  stable across bundles of one schema version.
- **`status_notes`** *(list of strings)* — honest labels a reader must
  surface: schema-example vs physics handoff (§9), PEC-wall status, dirty
  tree.

## 9. Gain-mask fallback semantics

`FieldSample.gain_region_mask` exists only once Phase 1b (bore + pentacene
crystal sub-domain) is built. Until then the exporter materialises the
fallback — the STO dielectric mask — and flags it:
`summary.gain_mask_is_fallback: true` plus a SCHEMA EXAMPLE status note.
Such bundles exercise every key of this contract but their spin-arm
quantities describe the **STO puck, not the pentacene gain region**: use them
to build readers, not physics. The first physics-handoff bundle requires
Phase 1b geometry (and impedance walls for a loaded-realistic Q).

## 10. Open asks recorded against consumer 2 (Maxwell–Bloch)

The published framework (arXiv:2412.21166) is underdetermined on: (i)
preferred consumption form — raw field maps vs the precomputed g-histogram
(both ingredients + the §6 recipe ship in every bundle); (ii) whether its
κ_c uses loaded or unloaded Q and which coupling k (§7); (iii) whether
E-field/loss maps are wanted for extensions; (iv) whether npz suits their
stack (NPZ.jl exists for Julia). These go to the Maxwell-Bloch authors; the
schema stores enough for every reading.
