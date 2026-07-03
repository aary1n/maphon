"""SPEC §2 — model assembly via MPh.

This module touches COMSOL through the MPh wrapper. MPh is lazy-imported
because SPEC §1 forbids assuming COMSOL is available in CI; importing
this module without MPh installed must not error. Calling `build_model`
without MPh raises `ComsolUnavailable` with the install hint.

Conventions (SPEC §11 gap #4, resolved 2026-07-02):
  - packaged RF interface (`Electromagnetic Waves, Frequency Domain`),
    NOT a custom weak-form PDE;
  - the interface tag is never hardcoded downstream — whatever tag MPh
    assigns at creation is read back off the node and carried in
    `BuiltModel.interface_tag` (default expectation "emw", but a
    supervisor model with a non-emw tag has been observed, so shared
    code always parameterises it).

Geometry: 2D axisymmetric (r, z), m = 0. All dimensions come from the
`CavityGeometry` instance (ultimately `provenance.GEOM`) — no numeric
geometry literals in this module.

Walls: `WallBC.IMPEDANCE` adds an Impedance BC on the three exterior
wall edges (bottom, top, radial) with user-defined copper properties
from `MaterialSpec.copper`; the r = 0 edge keeps COMSOL's automatic
axial-symmetry condition. `WallBC.PEC` adds nothing — the emw default
exterior condition is PEC — which is exactly the §4 Q_diel variant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.study import EigenStudyConfig, WallBC


class ComsolUnavailable(RuntimeError):
    """Raised when MPh/COMSOL is required but unavailable.

    SPEC §1: COMSOL is not assumed available in CI. The pure-Python
    parts of `forward_model` (geometry, materials, mesh, study,
    gridding, mode_id, convergence) and all of `validation.analytic`
    work without it; `build_model` and the solve/runner layer do not.
    """


def is_comsol_available() -> bool:
    """True if MPh imports cleanly. Does not start a COMSOL session."""
    try:
        import mph  # noqa: F401
    except ImportError:
        return False
    return True


def _require_mph() -> Any:
    try:
        import mph
    except ImportError as exc:  # pragma: no cover -- exercised on COMSOL-less hosts
        raise ComsolUnavailable(
            "MPh is required for COMSOL model assembly. "
            "Install with: pip install mph"
        ) from exc
    return mph


def validate_wall_bc_consistency(
    materials: MaterialSpec, study: EigenStudyConfig
) -> None:
    """`MaterialSpec.wall_pec` and `EigenStudyConfig.wall_bc` encode the
    same §4 switch from two directions; a disagreement means the caller
    is about to run a mislabelled solve, which would silently corrupt
    the wall-loss decomposition. Checked before any COMSOL contact.
    """
    pec_from_study = study.wall_bc is WallBC.PEC
    if materials.wall_pec != pec_from_study:
        raise ValueError(
            "wall-BC switch mismatch: MaterialSpec.wall_pec="
            f"{materials.wall_pec} but EigenStudyConfig.wall_bc="
            f"{study.wall_bc}. The §4 decomposition depends on these "
            "labels being truthful; make them agree."
        )


@dataclass(frozen=True)
class BuiltModel:
    """Handles into one assembled §2 model.

    `interface_tag` is read back from the created physics node — never
    assumed. `size_global` / `size_dielectric` are the two mesh Size
    features the convergence runner retunes between refinement levels
    (geometry, physics and study are level-invariant, so the model is
    built once and re-meshed per level).
    """

    model: Any
    client: Any
    interface_tag: str
    geometry: Any
    mesh: Any
    study: Any
    size_global: Any
    size_dielectric: Any
    dielectric_selection_tag: str
    wall_bc: WallBC
    comsol_version: str


def _walls_selection(model: Any, geom: CavityGeometry) -> Any:
    """Box-select the three exterior wall edges (bottom, top, radial).

    Thin box selections with `condition = inside` catch exactly the
    edges lying on z = 0, z = H and r = R; the axis edge (r = 0) spans
    the full height and falls inside none of them, so it keeps the
    automatic axial-symmetry condition. Interior (dielectric) edges sit
    near mid-height/mid-radius and are likewise excluded.
    """
    selections = model / "selections"
    pad = 1e-6 * min(geom.box_radius_m, geom.box_height_m)
    r_hi = geom.box_radius_m
    z_hi = geom.box_height_m
    spans = {
        "wall z=0": (-pad, r_hi + pad, -pad, +pad),
        "wall z=H": (-pad, r_hi + pad, z_hi - pad, z_hi + pad),
        "wall r=R": (r_hi - pad, r_hi + pad, -pad, z_hi + pad),
    }
    boxes = []
    for name, (xmin, xmax, ymin, ymax) in spans.items():
        box = selections.create("Box", name=name)
        box.property("entitydim", 1)
        box.property("xmin", xmin)
        box.property("xmax", xmax)
        box.property("ymin", ymin)
        box.property("ymax", ymax)
        box.property("condition", "inside")
        boxes.append(box)
    union = selections.create("Union", name="cavity walls")
    union.property("entitydim", 1)
    union.property("input", [box.tag() for box in boxes])
    return union


def _sto_permittivity_expression(materials: MaterialSpec) -> str:
    """eps_r' * (1 - i*tan_delta) as a COMSOL expression string.

    Kept in formula form (not a pre-evaluated complex literal) so the
    .mph inspection shows the SPEC §2 model transparently.
    """
    sto = materials.sto
    return f"{sto.epsilon_r_real!r}*(1-{sto.tan_delta!r}*i)"


def apply_mesh_config(built_size_global: Any, built_size_dielectric: Any,
                      mesh_cfg: MeshConfig) -> None:
    """Push a `MeshConfig` onto the two Size features (global + dielectric).

    Used both at build time and by the convergence runner between
    refinement levels. `hcurve` is the COMSOL curvature factor: the
    curved-dielectric-boundary requirement (SPEC §2, Booth's corner
    warning) maps to a small factor so elements track the curved
    interface; the diagnostic `False` setting relaxes it to the loosest
    factor to demonstrate why that poisons Q.
    """
    hcurve = 0.2 if mesh_cfg.curved_dielectric_boundary else 1.0

    built_size_global.property("custom", "on")
    built_size_global.property("hmax", str(mesh_cfg.air_max_h_m))
    built_size_global.property("hcurve", str(hcurve))

    built_size_dielectric.property("custom", "on")
    built_size_dielectric.property("hmax", str(mesh_cfg.dielectric_max_h_m))
    built_size_dielectric.property("hmaxactive", True)
    built_size_dielectric.property("hcurve", str(hcurve))
    built_size_dielectric.property("hcurveactive", True)


def _set_azimuthal_mode_number(physics_node: Any, m: int) -> None:
    """Set the azimuthal mode number on the 2D-axisym emw interface.

    The property container name varies across COMSOL versions; each
    known candidate is tried. The interface default is m = 0 — exactly
    the SPEC §2 target — so failure to set is fatal only when a
    non-zero m was requested.
    """
    candidates = (
        ("outofplanewavenumber", "m"),
        ("outofplanewavenumber", "mFloor"),
        ("AzimuthalModeNumber", "m"),
    )
    for prop, name in candidates:
        try:
            physics_node.java.prop(prop).set(name, int(m))
            return
        except Exception:
            continue
    if m != 0:
        raise RuntimeError(
            f"could not set azimuthal mode number m={m} on physics "
            f"interface '{physics_node.tag()}' — none of the known "
            f"property names {candidates} exist in this COMSOL version."
        )
    # m == 0 is the interface default; proceeding is safe.


def mesh_element_count(mesh_node: Any) -> int:
    """Total mesh element count, for the SPEC §1 solve log."""
    java = mesh_node.java
    attempts = (
        lambda: int(java.getNumElem()),
        lambda: int(java.stat().getNumElem()),
        lambda: int(java.getNumElem("tri")) + int(java.getNumElem("quad")),
    )
    errors = []
    for attempt in attempts:
        try:
            return attempt()
        except Exception as exc:
            errors.append(repr(exc))
    raise RuntimeError(
        "could not read the mesh element count from COMSOL "
        f"(SPEC §1 requires logging it). Attempts failed with: {errors}"
    )


def build_model(
    geom: CavityGeometry,
    materials: MaterialSpec,
    mesh_cfg: MeshConfig,
    study: EigenStudyConfig,
    *,
    client: Any = None,
    model_name: str = "sto_te01delta_forward_model",
) -> BuiltModel:
    """Assemble the §2 axisymmetric model via MPh.

    Builds geometry (puck/torus switch), materials (air + complex-eps
    STO), the packaged RF interface, wall BC per `study.wall_bc`, the
    two-tier mesh with curved dielectric boundary, and the
    eigenfrequency study searching near `study.search_hz`. Does NOT
    run the mesh or the solve — the runner owns execution so the
    convergence loop can re-mesh without rebuilding.

    Raises:
        ValueError: wall-BC switch mismatch (checked before any COMSOL
            contact).
        ComsolUnavailable: MPh is not installed.
    """
    validate_wall_bc_consistency(materials, study)
    mph = _require_mph()

    if client is None:
        client = mph.start()
    model = client.create(model_name)

    # --- component + axisymmetric 2D geometry -------------------------
    (model / "components").create(True, name="component")
    geometry = (model / "geometries").create(2, name="geometry")
    geometry.java.axisymmetric(True)

    box = geometry.create("Rectangle", name="cavity box")
    box.property("size", [geom.box_radius_m, geom.box_height_m])
    box.property("selresult", True)

    z0 = geom.dielectric_centre_z_m
    if geom.dielectric_shape is DielectricShape.PUCK:
        assert geom.dielectric_height_m is not None
        dielectric = geometry.create("Rectangle", name="dielectric puck")
        dielectric.property(
            "size", [geom.dielectric_radius_m, geom.dielectric_height_m]
        )
        dielectric.property(
            "pos", [0.0, z0 - 0.5 * geom.dielectric_height_m]
        )
    else:
        assert geom.dielectric_minor_radius_m is not None
        dielectric = geometry.create("Circle", name="dielectric torus")
        dielectric.property("r", geom.dielectric_minor_radius_m)
        dielectric.property("pos", [geom.dielectric_radius_m, z0])
    dielectric.property("selresult", True)

    model.build(geometry)
    diel_sel_tag = f"{geometry.tag()}_{dielectric.tag()}_dom"

    # --- materials: air everywhere, STO overriding on the dielectric --
    materials_group = model / "materials"
    air = materials_group.create("Common", name="air")
    air.select("all")
    for name, value in (
        ("relpermittivity", "1"),
        ("relpermeability", "1"),
        ("electricconductivity", "0"),
    ):
        air.java.propertyGroup("def").set(name, value)

    sto = materials_group.create("Common", name="STO")
    sto.java.selection().named(diel_sel_tag)
    for name, value in (
        ("relpermittivity", _sto_permittivity_expression(materials)),
        ("relpermeability", f"{materials.sto.mu_r!r}"),
        ("electricconductivity", f"{materials.sto.sigma!r}"),
    ):
        sto.java.propertyGroup("def").set(name, value)

    # --- physics: packaged RF interface (SPEC §11 gap #4, resolved) ---
    emw = (model / "physics").create(
        "ElectromagneticWaves", geometry, name="electromagnetic waves"
    )
    interface_tag = str(emw.tag())
    _set_azimuthal_mode_number(emw, study.target.azimuthal_index_m)

    if study.wall_bc is WallBC.IMPEDANCE:
        walls = _walls_selection(model, geom)
        impedance = emw.create("Impedance", 1, name="copper walls")
        impedance.select(walls)
        copper = materials.copper
        # Boundary-material property names pinned empirically on
        # COMSOL 6.0 (sigmabnd/murbnd/epsilonr + `_mat` source switch).
        for name, value in (
            ("sigmabnd_mat", "userdef"),
            ("sigmabnd", f"{copper.sigma!r}[S/m]"),
            ("murbnd_mat", "userdef"),
            ("murbnd", f"{copper.mu_r!r}"),
            ("epsilonr_mat", "userdef"),
            ("epsilonr", "1"),
        ):
            impedance.property(name, value)
    # WallBC.PEC: the emw default exterior condition is PEC — add nothing.

    # --- mesh: two-tier size + free triangular ------------------------
    mesh = (model / "meshes").create(geometry, name="mesh")
    size_global = mesh / "Size"
    free_tri = mesh.create("FreeTri", name="free triangular")
    size_dielectric = free_tri.create("Size", name="dielectric size")
    size_dielectric.java.selection().geom(geometry.tag(), 2)
    size_dielectric.java.selection().named(diel_sel_tag)
    apply_mesh_config(size_global, size_dielectric, mesh_cfg)

    # --- eigenfrequency study -----------------------------------------
    study_node = (model / "studies").create(name="eigenfrequency study")
    eig = study_node.create("Eigenfrequency", name="eigenfrequency")
    eig.property("neigsactive", True)
    eig.property("neigs", study.n_modes)
    eig.property("shift", f"{study.search_hz!r}[Hz]")

    return BuiltModel(
        model=model,
        client=client,
        interface_tag=interface_tag,
        geometry=geometry,
        mesh=mesh,
        study=study_node,
        size_global=size_global,
        size_dielectric=size_dielectric,
        dielectric_selection_tag=diel_sel_tag,
        wall_bc=study.wall_bc,
        comsol_version=str(client.version),
    )
