# PLAN — SPEC changeset: geometry re-base, Booth torus → Wu ring

**Status: PLAN ONLY — nothing in this document has been implemented. Awaiting ratification.**
*(Status update 2026-07-18, dated — the line above is the drafting-time record: the plan was RATIFIED and EXECUTED as the 2026-07-18 geometry re-base changeset. Deviation from §Ordered-sequence step 1: the R10a email archive DEFERRED — no .eml export landed, collected count 841 not 842, deferral stated in the archive commit. The `.gitattributes` +1 line proved a no-op — the existing blanket `*.pdf` LFS rule already covers the archive path.)*
Prompt of record: PLAN CHECKPOINT 2026-07-18 (R1–R11). Zero-licence changeset: code + SPEC + tests + archives. No COMSOL solve.

---

## Context

Oxborrow's written recommendation (2026-07-17) re-bases the simulation on the published Wu build — Wu, Mirkhanov, Ng & Oxborrow, PRL 127, 053604 (2021) + SM, cross-verified against Wu et al., PR Applied 14, 064017 (2020): the same physical cavity (same Gaskell Quartz STO ring, same Q_L = 3600, same f, same lab). This replaces the Booth torus as the *modelled* geometry; **Booth's torus is not deleted or modified** — it remains the §5a solver-correctness anchor, and all archived records stay untouched. The changeset lands the Wu geometry as graded constants, re-parameterises the Layer-A DOF table, closes SPEC §11 gap #3 (Wu coupling now stated in print: k = 1), re-derives `TOL.tan_delta_max`, and archives the primary sources. All ratified decisions R1–R11 are taken as given; this plan maps them onto the repo.

---

## Verification record (what I checked, this session)

### Zotero — both papers found, all quoted numbers re-verified against the PDFs

| Zotero item | Attachments (attach-check) |
|---|---|
| **Wu 2020** PRA 14, 064017 — "Room-Temperature Quasi-CW Pentacene Maser…" (item `X4MH9DCL`) | Full-text PDF (`8ZL66UT2`) — **genuine PDF** (`%PDF-1.4`, 10 pp, 1.48 MB). The floating `PhysRevApplied_14_064017.pdf` ZIP-of-extracts problem does **not** afflict the Zotero copy. |
| **Wu 2021** PRL 127, 053604 — "Bench-Top Cooling of a Microwave Mode…" (item `8QAXJG8Y`) | Main PDF (`73WWZCKU`, `%PDF-1.4`, 6 pp) **and separate SM attachment** `Cooling_PRL_SM_Proof.pdf` (`EWVFZX3N`, `%PDF-1.5`, 7 pp). ⚠ The SM copy is a **PROOF** version, not the published SM — record this on the archive's provenance note (numbers verified below are from this proof; no discrepancy found, but the grade statement should say "SM proof copy"). |
| Duplicate PRL entry (item `A4MTHR59`) | Main PDF only. Not used; candidate for a later Zotero dedup pass (not this changeset). |

**Every number in the prompt verified verbatim — no discrepancies with the prompt. No STOP condition fired.**

| Quantity | Prompt value | Found in paper (verbatim) | Where |
|---|---|---|---|
| STO O.D. | 12.0 mm → `6.0e-3` radius | "outer diameter (O.D.) = 12.0 mm" | Wu 2020 §III.C (p. 064017-6) |
| STO I.D. | 4.05 mm → `2.025e-3` radius | "I.D. = 4.05 mm" | Wu 2020 §III.C |
| SM's bore round | "4-mm bore" is a round of 4.05 | "the STO ring's 4-mm bore"; "outer and inner diameters of 12 and 4 mm" | PRL SM p. 1 (×2); PRA §III.A |
| STO height fork | {8.5, 8.6} mm | **8.6**: "height = 8.6 mm" (Wu 2020 §III.C) AND PRL Fig. 1(c) photo label "8.6 mm" (beside "12 mm"). **8.5**: "8.5 mm in height" (PRL SM p. 1). Fork confirmed exactly as stated; 8.6 evidence-favoured (2 sources vs 1). | both papers |
| Box inner radius | 14.0e-3 | Fig. 6 caption: "The width of the entire region of the simulation (14 mm) corresponds to the radius of the copper enclosure" | Wu 2020 Fig. 6 caption |
| 28-mm cap caveat | nominal pipe-fitting size | "a **standard copper pipe fitting**, viz. a 28-mm end-feed end cap" | PRL SM p. 1 |
| Box internal height (as-operated nominal) | 15e-3 | Fig. 6 caption "height of the region (15 mm) … between the tuning plate and the copper sheet"; SM "internal height (≈15 mm)" | Wu 2020 Fig. 6 caption; PRL SM p. 1 |
| Deck clearance | 3.0e-3 | "raises the STO ring 3 mm above a copper conducting plane" (PRA); "held the STO ring ∼3 mm above the PCB" (SM) | both |
| Piston radius | 13.0e-3 | "an internal piston in the form of a 26-mm dia. copper disk suspended by a brass screw" | PRL SM p. 1 |
| Tuning mechanism in print | screw-adjustable ceiling | "mechanically tuned (varying the height of the cavity's internal metal 'ceiling' suspended on a screw)" | Wu 2020 §III.C |
| Spacer identity | Polypenco Q200.5, Elder Engineering Ltd., cross-linked PS | "A support made of cross-linked polystyrene (viz., Polypenco Q200.5, Elder Engineering Ltd.)" | Wu 2020 §III.C |
| Spacer ≡ Rexolite bridge | (for ε_r sourcing) | "A post made of cross-linked polystyrene (**an equivalent of Rexolite**), mounted into a hole in the PCB … held the STO ring … **concentrically** with respect to the cavity's side wall" | PRL SM p. 1 |
| Coupling | k = 1 STATED | "An inductive loop (coupling coefficient k = 1)"; "where k = 1 is the coupling coefficient of the output port" | Wu 2020 §III.C and §IV |
| Q_L | 3600 | "loaded quality factor (Q_L) … measured to be 3600 using a vector-network analyzer (Agilent 8753C)" | Wu 2020 §III.C |
| Q_0 corroboration | 7200 | "Q_L ≈ 3600 **at critical coupling**, equating to an unloaded quality factor of Q_0 ≈ 2Q_L = 7200"; again "under critical coupling, Q_0 = Q_ex = 7200" | PRL SM pp. 1, 3 |
| f | 1.4495e9 | "f_mode = f_XZ = 1.4495 GHz" | Wu 2020 §III.C (also PRA Fig. 1, PRL Eq. 1 context) |
| V_mode (held out of gate) | ≈ 0.32e-6 m³ | "V_mode … estimated to be ≈ 0.32 cm³" (COMSOL FEM); PRA prints the rougher "∼0.3 cm³" | PRL SM p. 1; Wu 2020 §III.C |
| κ_s same-build point | 1.1 MHz (angular) | "κ_s = 1.1 MHz is the spin-dephasing rate … larger than … FID … (0.7 MHz) [36]. The difference may arise from a concentration effect [43]: our … 0.1%, whereas … approximately 0.01%." | Wu 2020 p. 064017-8 |
| κ_c same-build point | 2.5 MHz (angular) | "κ_c = 2πf_XZ/Q_L = 2.5 MHz is the cavity decay rate" | Wu 2020 p. 064017-8 |
| Crystal volume indicator | ~100 mm³ | "with an approximate volume of 100 mm³" | Wu 2020 §III.C |
| Crystal bore-fill indicators (R5) | 3 quoted | "slotted snugly into the STO ring's 4-mm bore **(though did not entirely fill it)**" ⚠ carry the parenthetical; pump path "≤ 4 mm in length/depth through the crystal" (and Eq. S2: "l the thickness of the crystal (≤4 mm)"); the 100 mm³ ⇒ ~4 mm dia at 8 mm height | PRL SM pp. 1–2; Wu 2020 §III.C |
| — bonus 4th indicator (found this pass) | — | PRA §III.B: crystal grown inside a **PTFE sleeve, I.D. 4 mm × height 8 mm** ("limiting the crystal's radial growth to the same diameter"); "The bead of Pc:Ptp fits snugly into the STO ring" | Wu 2020 §III.B |
| — bonus 5th indicator (Fig. 6 digitization, below) | — | Wu's own simulation draws the crystal at r ≈ 0–1.95 mm (dia ≈ 3.9 mm) × full ring height (≈8.5 mm), i.e. bore-filling and TALLER than Breeze's 8 mm | Wu 2020 Fig. 6 (vector overlay, digitized) |

**R8 docstring cross-check (Breeze/npj keep k = 0.2):** the `DELOAD_K` comment (constants.py:281–285) states "Breeze 2017 and Salvadori npj 2020 use k = 0.2; reusing it for Wu … is an assumption". Consistent with R8's claim — **no flag**.

### Fig. 6 — the spacer cross-section, LOOKED AT and digitized (settles the pedestal-vs-plug fork)

The three coloured outlines in Fig. 6 are **vector paths in the PDF** (not raster) — extracted exactly with PyMuPDF and calibrated against the cyan STO rectangle (known r: 2.025→6.0 mm; z: 3.0→3.0+height, both fork branches computed). Digitized values are stable to <0.05 mm across the 8.5/8.6 branches; the overlays themselves are hand-placed annotations with ~2–3% aspect mismatch vs the printed ring dims, so grade every derived dimension **FIGURE-DERIVED, ±≈0.3 mm**:

- **RED (spacer) = stepped ANNULAR SEAT, not a plug.** Vertices (r, z) mm: (2.50, 3.0) → (2.50, ≈0.1) → (8.10, ≈0.1) → (8.10, 4.51) → (6.12, 4.51) → (6.12, 3.0) → close. I.e.: a base annulus inner r ≈ 2.5 mm, outer r ≈ 8.1 mm, spanning the full 3 mm deck clearance, plus an **outer registration lip** (r ≈ 6.1→8.1 mm, rising ≈1.5 mm above the ring's underside) that wraps the ring's outside — matching the SM's "held the STO ring … concentrically". **Nothing under the bore** (no material at r < 2.5): the support does not plug the bore. **Fork verdict: pedestal/seat branch WINS; the plug branch dies.** Residual tension to record, not resolve: the SM says "post mounted into a hole in the PCB" (suggests a column continuing below deck level, outside the simulated region z<0) — the sub-deck form is unmodelled either way.
- **MAGENTA (crystal, Wu's own sim):** r ≈ −0.08…1.95 mm (axis-touching within slop) × z 3.0…≈11.5 — dia ≈ 3.9 mm at FULL ring height (≈8.5, not 8.0). This is the 5th bore-filling indicator above and also hints Wu simulated a taller-than-Breeze crystal. Feeds the R5 flag text, resolves nothing (ask is with Oxborrow).
- **CYAN (STO):** consistent with prints (used as the calibration object).

Digitization scripts + rendered crops are in the session scratchpad; the implementation pass should re-run the extraction and commit it as a small `refs/wu_fig6_spacer_digitization.md` + script-pinned numbers (house rule: scoping numbers are computed, re-fittable, never eyeballed).

### Spacer ε_r sourcing (R1)

Chain, graded honestly:
1. PRL SM (in print, same build): the support material is "cross-linked polystyrene (**an equivalent of Rexolite**)" — the class-bridge is the authors' own, not ours.
2. Rexolite 1422 manufacturer datasheet (C-Lec Plastics; mirrored at spacematdb.com/spacemat/manudatasheets/REXOLITE1422.pdf): **dielectric constant 2.53, stated flat up to 500 GHz**, dissipation factor ≤ ~5e-4 class.
3. Gap carried on the grade: Polypenco Q200.5 (the actual product, Wu 2020) is a cross-linked-PS *class sibling* of Rexolite 1422, not the identical resin — grade `eps_r = 2.53` as **DATASHEET-CLASS-ANALOG** (Rexolite-class datasheet + the SM's printed equivalence), NOT a measured property of the as-built part. tanδ of the spacer is deliberately NOT graded this pass (loss budget untouched; note only).

### What I could NOT verify (reported honestly, not substituted)

- **Gmail is unreachable this session** (MCP token expired; needs interactive re-auth). Therefore unverified: (a) the Oxborrow geometry email dated 2026-07-17 (R10a's archive target and the changeset's authorizing document), (b) the sent 2026-07-18 travel-band ask (R4). The plan proceeds on the prompt's description; the R10a archive step at implementation time requires Gmail re-auth first (or a user-side .eml export). **STOP point S6 below covers the case where the email's wording differs from the prompt's summary.**
- The **published** PRL SM (vs the proof copy in Zotero) — not fetched; every SM number above is from the proof. If the implementation wants the published SM alongside, that is a separate Zotero pull; the archive provenance note records "proof" either way.
- Booth's and Breeze/npj's k = 0.2 verified **at docstring level only** (per R8's ask) — not re-verified against Breeze 2017's PDF this pass.

### In-repo discrepancies surfaced (two-sided wording; neither resolved unilaterally)

1. **`TARGETS.wu_measured.f_hz = 1.4493e9` (constants.py:1161) vs Wu 2020's printed 1.4495 GHz.** The repo value follows the B15-lineage reading (provenance table, f_XZ row: "W20 cites B15 for a number B15 doesn't print"; B15's measured peak is 1.4493) — a defensible branch, but **undocumented at the entry** (the source string is silent). The prompt's R7 anchor (1.4495e9) matches the print. **Dissolved by the plan's R7 design** (new `wu_ring` entry at the ratified print 1.4495e9; `wu_measured` frozen byte-identical with a dated note documenting its 1.4493 as the record-time lineage reading) — no side is picked, both readings end up documented at their own entries.
2. **PRL SM proof copy** — see above; archive-note matter only.

---

## Numbers that land in code (each with source + grade, inline)

| Constant (proposed field) | Value | Source | Grade |
|---|---|---|---|
| `sto_outer_radius_m` | `6.0e-3` | Wu 2020 §III.C "O.D. = 12.0 mm" | LITERATURE (print, exact) |
| `sto_inner_radius_m` | `2.025e-3` | Wu 2020 §III.C "I.D. = 4.05 mm"; PRL SM's "4-mm bore" recorded as the round of this | LITERATURE (print, exact; SM-round note carried) |
| `sto_height_m` | **FORK {8.5e-3, 8.6e-3}** — no plain float lands anywhere | 8.6: Wu 2020 text + PRL Fig. 1(c) label; 8.5: PRL SM text | FORKED — **Q13** sentinel (NB "Q12" is already burned: it is the RESOLVED uniform-k ruling, `docs/plans/layer_a_sweep_design.md:593`, cited by `compose.py:7,84`); 8.6 recorded evidence-favoured (2 sources vs 1); resolution = Oxborrow written reply or caliper |
| `box_inner_radius_m` | `14.0e-3` | Wu 2020 Fig. 6 caption (region width 14 mm = enclosure radius) | LITERATURE (caption) — carry caveat: SM's "28-mm end-feed end cap" is a NOMINAL pipe-fitting size ("standard copper pipe fitting"), so the true barrel I.R. may differ from 14.0 by the fitting tolerance |
| `box_internal_height_nominal_m` (record field, NOT the DOF) | `15e-3` | Wu 2020 Fig. 6 caption; PRL SM "≈15 mm" | LITERATURE (as-operated/as-simulated nominal); the DOF is `p_tune` (Q2, travel band OPEN — Oxborrow asked 2026-07-18) |
| `deck_clearance_m` | `3.0e-3` | Wu 2020 "3 mm above a copper conducting plane"; PRL SM "∼3 mm above the PCB" | LITERATURE (print; SM carries the tilde) |
| `piston_radius_m` | `13.0e-3` | PRL SM "26-mm dia. copper disk" | LITERATURE (print). The 1 mm annular gap to the 14-mm barrel is MODELLED, not simplified away (ratified) |
| spacer form + dims | stepped annular seat; digitized vertices above | Wu 2020 Fig. 6 (vector-extracted); PRL SM "post … held the STO ring concentrically" | FIGURE-DERIVED ±≈0.3 mm; pedestal-vs-plug fork SETTLED (seat); sub-deck form unmodelled |
| spacer `epsilon_r` | `2.53` | Rexolite 1422 datasheet (C-Lec) via the PRL SM's own "equivalent of Rexolite" | DATASHEET-CLASS-ANALOG (product-identity gap stated) |
| Wu crystal dims (planning) | dia `3.0e-3` × `8.0e-3` | provenance.CRYSTAL (Breeze 2017) | PLANNING-ASSUMPTION + **cross-build-transfer flag**: five Wu-side indicators lean ~4 mm bore-filling (SM "slotted snugly … (though did not entirely fill it)"; pump path ≤ 4 mm; 100 mm³ @ 8 mm ⇒ ~4 mm dia; PTFE growth mold I.D. 4 mm × 8 mm; Fig. 6 sim crystal ≈3.9 mm dia × full ring height). Ask in Oxborrow email queue. Placement stays Q9-open. |
| New anchor: f | `1.4495e9` | Wu 2020 (print) | LITERATURE — see surfaced discrepancy #1 re. wu_measured's 1.4493 lineage branch |
| New anchor: Q_L | `3600` | Wu 2020 (VNA-measured) | LITERATURE |
| New anchor: stated coupling k | `1.0` | Wu 2020 "(coupling coefficient k = 1)" — STATED in print | LITERATURE ⇒ Q_0 = Q_L(1+k) = **7200**, independently corroborated by PRL SM "Q_0 ≈ 2Q_L = 7200" |
| New anchor: V_mode | `0.32e-6` m³ | PRL SM (COMSOL estimate) | RECORDED, **HELD OUT of every gate** until its integration convention is checked against the Booth convention (the 225/360 lesson). No acceptance window attaches to it this pass. |
| `TOL.tan_delta_max` | `2.3e-4` → **`1.4e-4`** | re-derivation at Q_0 = 7200: 1/7200 = 1.3889e-4, rounded 2 s.f. (same convention as the old 1/4320 = 2.3148e-4 → 2.3e-4) | DERIVED (assumption-free on coupling now; still attributes ALL loss to the dielectric — conservative-ceiling reading unchanged). Old value preserved as dated superseded record. |
| κ_s annotation (R9) | 1.1 MHz (0.1%) / 0.7 MHz FID (0.01%) / κ_c 2.5 MHz — ALL ANGULAR per the unit trap | Wu 2020 p. -8 | ANNOTATION ONLY on `SpinResonanceLinewidth` docstring: same-build published κ_s point + concentration-effect attribution; cyclic equivalents κ_s/2π ≈ 0.175 MHz, κ_c/2π ≈ 0.398 MHz (≈ f/Q_L = 402.6 kHz ✓); feeds the linewidth-branch question, resolves nothing |

---

## Design decisions (mechanics per R1–R11)

### R1 — `WuSTORingGeometry` (provenance/constants.py, inserted after `BoothTE01DeltaGeometry`:185)

Proposed name: **`WuSTORingGeometry`**, instance **`GEOM_WU_STO_RING`** (alongside `GEOM_BOOTH_TE01D` at :1107). Frozen dataclass with defaulted fields (repo convention), docstring carrying the full provenance chain incl. the fork story and the 28-mm-nominal caveat:

```python
@dataclass(frozen=True)
class WuSTORingGeometry:
    sto_outer_radius_m: float = 6.0e-3
    sto_inner_radius_m: float = 2.025e-3
    sto_height_m: ForkedConstant = STO_HEIGHT_FORK      # {8.5e-3, 8.6e-3}, 8.6 evidence-favoured
    box_inner_radius_m: float = 14.0e-3                  # R1's ratified field name
    box_internal_height_asoperated_m: float = 15e-3      # RECORD ONLY — the DOF is p_tune (Q2)
    deck_clearance_m: float = 3.0e-3
    piston_radius_m: float = 13.0e-3                     # 1 mm annular gap to barrel MODELLED (ratified)
    # spacer (figure-derived ±0.3 mm; Fig. 6 digitization, committed as refs/…):
    spacer_base_inner_radius_m: float = 2.5e-3
    spacer_base_outer_radius_m: float = 8.1e-3
    spacer_base_height_m: float = 3.0e-3                 # == deck_clearance_m (ring seats on the BASE)
    spacer_lip_inner_radius_m: float = 6.1e-3            # lip wraps OUTSIDE the ring (≥ sto_outer_radius_m)
    spacer_lip_outer_radius_m: float = 8.1e-3
    spacer_lip_height_m: float = 1.5e-3                  # lip top ≈ z 4.5 mm
    # Wu-build crystal, PLANNING-ASSUMPTION + cross-build-transfer flag (R5):
    crystal_diameter_m: float = 3.0e-3                   # = provenance.CRYSTAL (Breeze 2017)
    crystal_height_m: float = 8.0e-3
```

- **`ForkedConstant`** (new small frozen class in constants.py, before `PublishedTarget`): `candidates: tuple[float, ...]`, `candidate_sources: tuple[str, ...]`, `evidence_favoured: float`, `resolution_route: str` ("Q13: Oxborrow written reply or caliper"); `__post_init__` validates ≥2 candidates / sources aligned / favoured ∈ candidates; `__float__` raises `TypeError` naming the route — **no plain float exists anywhere for the height**. Module-level `STO_HEIGHT_FORK = ForkedConstant(candidates=(8.5e-3, 8.6e-3), …, evidence_favoured=8.6e-3, …)`.
- **`CrossLinkedPolystyrene`** frozen dataclass + instance `CLPS`: `epsilon_r_real = 2.53` (grade chain in docstring: PRL SM's own "equivalent of Rexolite" → Rexolite 1422 datasheet, C-Lec; DATASHEET-CLASS-ANALOG, product-identity gap stated), `tan_delta` NOT graded this pass (loss budget untouched — recorded as such), `mu_r = 1.0`, `sigma = 0.0`.
- Layering preserved: provenance imports nothing from `cavity.sweep`; the fork *record* lives here, the fork *gate* (Q13) lives in dofs.py and machine-reads the record.
- Exports added to `provenance/__init__.py` (imports + `__all__`): `ForkedConstant`, `STO_HEIGHT_FORK`, `WuSTORingGeometry`, `GEOM_WU_STO_RING`, `CrossLinkedPolystyrene`, `CLPS`.
- R5 crystal fields carry a docstring block: PLANNING-ASSUMPTION (= `provenance.CRYSTAL`, Breeze 2017) + **cross-build-transfer flag** enumerating the five Wu-side ~4 mm bore-filling indicators (verification table above) + "ask in Oxborrow email queue; placement (axial offset band, centring tol) stays Q9-open". `SENTINEL_Q9.description`'s "Crystal DIMENSIONS are already resolved" sentence is **re-worded** (dimensions resolved *for the Booth-context Breeze import*; for the Wu build they are planning-assumption with the transfer flag — Q9 itself stays placement-only and UNRESOLVED, no SentinelResolution, no solve-gate change).

### R2 — geometry engine: `DielectricShape.RING` + spacer + piston step (minimal diff)

`forward_model/geometry.py`:
- Enum gains `RING = "ring"`. `CavityGeometry` gains optional fields: `dielectric_inner_radius_m` (RING-required; `dielectric_radius_m` = OUTER radius; `dielectric_height_m` reused as ring height), `ring_bottom_z_m` (RING-required — deck clearance; `dielectric_centre_z_m` property becomes shape-aware: RING → `ring_bottom + h/2`, else `box_height/2` as now — zero edits at any consumer, all route through the property), `spacer: SpacerSpec | None` (RING-only), `piston_radius_m: float | None` + `piston_gap_depth_m: float | None` (RING-only, jointly required or jointly None).
- `__post_init__` RING branch: requires height + inner radius + ring_bottom; forbids minor radius; `0 < inner < outer < box_radius`; `ring_bottom + height < box_height` **strict — this check is what makes the p_tune travel floor physical**; PUCK/TORUS branches forbid all new fields (their gate-validated state space is untouched — **the torus path is not modified**).
- **`SpacerSpec`** (in geometry.py — layout, not provenance): base (inner/outer/height) + lip (inner/outer/height), `mask()` = union of the two rectangles, validation: positivity, inner < outer per part, **`base_height == ring_bottom_z_m` (the ring seats on the BASE)**, `lip_inner_radius ≥ dielectric_radius_m` (the lip wraps *outside* the ring — no domain overlap with the STO; corrected from the design-pass sketch, which had the ring seated on the step: the Fig. 6 digitization shows the lip beside the ring, z 3.0→4.5 at r 6.1→8.1). `CavityGeometry.spacer_mask()` returns all-False when absent.
- **Piston step (R1 ratified: the 1 mm annular gap is modelled):** when the piston fields are set, the cavity outline is not a plain rectangle — main region r∈[0, box_radius], z∈[0, box_height] **plus** an annular recess r∈[piston_radius, box_radius], z∈[box_height, box_height + piston_gap_depth]. `piston_gap_depth_m` is **unprinted** — no default; it rides Q2 (the tuning-mechanism geometry ask, email sent 2026-07-18) as an optional resolution-payload key. Zero-licence consequence: the *capability* lands with validation + mask/build support; no solve consumes it yet (Q2 gates all real solves anyway). `dielectric_mask` unchanged by the piston; `_walls_selection` in build.py gains the recess edges when present.

`forward_model/build.py` (the only COMSOL contact — all Q2-gated, so exercised only by contract tests this pass):
- RING primitive: `geometry.create("Rectangle", name="dielectric ring")`, `pos=[inner, ring_bottom]`, `size=[outer−inner, height]`, `selresult=True`, assigned to the same `dielectric` handle — downstream selection/material/mesh logic untouched (the `{geom_tag}_{prim_tag}_dom` mechanism at :283–284 inherits free).
- Spacer: two Rectangles (base, lip), each `selresult=True`; selection union (Union node over the two named `_dom` selections; fallback = two Box selections per the `_walls_selection` precedent); third material node from `MaterialSpec.spacer` (new field `spacer: CrossLinkedPolystyrene | None = None` in materials.py); `validate_spacer_consistency(geom, materials)` beside `validate_wall_bc_consistency`; mesh: optional `MeshConfig.spacer_max_h_m` (None ⇒ inherits the air tier — ladder revalidation is a named licence-session follow-on, not smuggled in); `BuiltModel` gains `spacer_selection_tag`, `size_spacer`.
- **One flag, one owner:** `include_spacer: bool = True` on `draw_solve_spec` populates (or not) `geom.spacer`; build.py builds whatever the geometry declares. Default ON (ratified — Wu's own COMSOL includes it, Fig. 6).
- Mask/export integrity: `dielectric_mask`/p_e stay **STO-only** (spacer must NOT enter p_e); the ε-map fed to `FieldSample` (solve.py:377–381, backend.py:233–235) gains a spacer branch (else the exported `eps_r_complex` lies about the solved model); `FieldSample` gains optional `spacer_mask` (extraction/fields.py), written by export/writer.py as an optional array, `"spacer_mask"` added to schema.py `OPTIONAL_ARRAY_KEYS` + bool-dtype check. `solve_fingerprint` (persistence.py) gains the new geometry/material fields → **`SCHEMA_VERSION` bump to 2** (pinned historical hashes are import-only records, never recomputed — unaffected).

### R3 + R4 + R6 — DOF table re-parameterisation, Q13 fork, p_tune semantics (sweep/)

`sweep/dofs.py`:
- **`ForkTrace(TodoTrace)`** subclass (frozen-inherits-frozen; `DofSpec.nominal: float | TodoTrace` admits it unchanged): adds `candidates`, `evidence_favoured` (defaulted for dataclass inheritance, validated non-empty; favoured ∈ candidates).
- **`SENTINEL_Q13 = ForkTrace(question_id="Q13", …, candidates=GEOM_WU_STO_RING.sto_height_m.candidates, evidence_favoured=…)`** — machine-reads the provenance fork; description carries the {8.5, 8.6} print fork + evidence weighting; `routes_to` = "Oxborrow written reply or caliper measurement".
- Registrations (all four): `SOLVE_GATE_QUESTIONS` — **Q13 in BOTH modes** (D8: Q2,Q9,Q11,Q13; D7: Q9,Q11,Q13 — unlike p_tune, the height is a noise dim no mode can build without); `_SENTINELS_BY_QUESTION`; `_REQUIRED_PAYLOAD_KEYS["Q13"] = ("sto_height_m", "selection_evidence")` (+ optional `sto_height_band_m`, the RESOLUTION_Q11 extra-key precedent); `mock_resolutions()` gains an explicitly-labelled mock Q13 entry selecting the evidence-favoured branch (`mock=True`, PLANNING_ASSUMPTION — the machine-readable branch consumed *only* here and in the mock reference θ, never silently).
- **`LAYER_A_DOFS` rows 1–4 → `{box_radius_m, sto_outer_radius_m, sto_inner_radius_m, sto_height_m}`**: rows 1–3 nominal from `GEOM_WU_STO_RING` (`box_inner_radius_m`, `sto_outer_radius_m`, `sto_inner_radius_m`), `_machining_band` ±25 µm carried over (band_rung PLANNING_ASSUMPTION as now; box_radius provenance string carries the 28-mm-nominal-fitting caveat); row 4 = Q13 fork row (`nominal=SENTINEL_Q13`, `band=SENTINEL_Q13`, `UNDEFINED_TODO_TRACE`, both rungs TODO_TRACE). Pre-resolution **no ±25 µm band exists** for the height; post-resolution `materialise_dims` gains an `elif name == "sto_height_m":` branch (Q9-branch mirror): band = payload override or `nominal ± TOL.machining_tol_m`.
- **`box_height_m` row DELETED, not renamed** — the quantity became the control (p_tune); recorded in the module docstring exactly as the bore-radius invalidation is (invalidate-don't-rename discipline).
- **`SENTINEL_Q2` description update (R4 — description only, NO resolution):** mechanism now IDENTIFIED — p_tune *is* the box internal height (piston position), metres; supervisor-written 2026-07-17 + in print (Wu 2020 screw-ceiling; PRL SM piston-on-brass-screw); as-operated nominal 15e-3 recorded at `GEOM_WU_STO_RING.box_internal_height_asoperated_m`; **travel band `[p_min, p_max]` STILL OPEN — Oxborrow asked by email 2026-07-18; sentinel stays unresolved**; `piston_gap_depth_m` rides the same ask as an optional payload key. `_REQUIRED_PAYLOAD_KEYS["Q2"]` unchanged.
- `design.py:215` blocker filter `("Q2","Q9")` → `("Q2","Q9","Q13")` (else an unresolved fork dies as a TypeError in sampling instead of a named refusal).

`sweep/backend.py`:
- `draw_solve_spec` builds **RING**: outer/inner/height from θ (`sto_*`), `ring_bottom_z_m = GEOM_WU_STO_RING.deck_clearance_m`, `spacer` from the GEOM fields when `include_spacer=True` (new kwarg, default True), `MaterialSpec.spacer = CLPS` correspondingly. **Box height sourcing:** `theta["p_tune"]` when present (identity map — p_tune IS the internal height); else new explicit kwarg `box_height_fallback_m` (driver passes `GEOM_WU_STO_RING.box_internal_height_asoperated_m` explicitly); else `ValueError` naming Q2 — no silent module default.
- **`_PHASE1B_THETA_KEYS`: p_tune LEAVES** → `("crystal_axial_offset_m",)` — the engine now represents the tuning DOF; the Q2 licence-gate (`assert_solveable`) is a separate mechanism and still refuses every real solve. `ComsolBackend.solve` refusal text drops the plate clause.
- **Fresh, explicitly-labelled mock levers** (mocks never carry over): new key set `{sto_outer_radius_m, sto_inner_radius_m, sto_height_m, box_radius_m, epsilon_r, tan_delta?, crystal_axial_offset_m, p_tune}`; `p_tune` lever re-dimensioned to Hz per metre of internal height; reference θ anchored at `GEOM_WU_STO_RING` nominals with `sto_height_m` = the fork's evidence-favoured branch (labelled mock-tier read, comment naming Q13) and `p_tune` = the as-operated 15e-3. **Lever values are fresh labelled mocks chosen at implementation** — plausible-ordering only, nothing downstream may quote them (existing doctrine at backend.py:152–157); no numeric lever values are pre-committed in this plan.
- `sweep/centre_check.py`: dated docstring note only — the pinned centre record (823e6…) is a **Booth-build** record; the Wu-build centre record does not exist yet (licence-session follow-on); no logic change.

### R7 + R8 — targets, gap #3 closure, tan_delta_max re-derivation

- **`PublishedTarget` gains `stated_coupling_k: float | None = None`** (last field, keyword-compatible — five existing entries construct unchanged) + `__post_init__` (stated coupling only on `measured_loaded`, > 0) + property **`deload_k`** → the STATED print when present, else the assumed `DELOAD_K` (raises on `modelled`). Rejected: a new `kind` value — `PublishedTarget.kind` has **zero code consumers** (verified), so a third kind buys nothing.
- **NEW entry `wu_ring` + `wu_measured` frozen-and-annotated** (this follows R7's ratified "new TARGETS entry" literally AND the invalidate-don't-rename discipline — the anchor's *semantics* change from assumed-de-load to stated-coupling, which is exactly the retire-and-replace trigger; the `NominalGeometry` supersession pattern is the in-repo precedent):
  - `ValidationTargets` gains a sixth field `wu_ring: PublishedTarget`; `TARGETS` constructor adds `wu_ring=PublishedTarget(source="Wu 2020 §III.C + PRL 127 SM (2021) — same build; coupling k = 1 STATED in print; gap #3 CLOSED 2026-07-18", epsilon_r_real=312.0, q_factor=3_600.0, f_hz=1.4495e9, v_mode_m3=0.32e-6, kind="measured_loaded", stated_coupling_k=1.0)`. Its `deload_k` property yields 1.0 ⇒ Q_0 = 2·Q_L = 7200 with no new formula (the existing `(1+k)` convention).
  - `wu_measured` **fields untouched, byte-identical** — gains only a dated supersession note in the `ValidationTargets` docstring + source-context comment: *"superseded for anchor duty by `wu_ring` (2026-07-18); retained as the printed record of the assumed-k era; its f_hz = 1.4493e9 is the record-time B15-lineage reading (provenance table, f_XZ row) — documented here, prints stay as printed."* This **dissolves surfaced discrepancy #1** — no branch pick needed: the old entry keeps its documented lineage reading, the new anchor carries the ratified print 1.4495e9.
- **`TOL.tan_delta_max`: 2.3e-4 → `1.4e-4`**, with the full arithmetic traced in a docstring on the field/class: Q_0 = Q_L(1+k) = 3600·2 = **7200** (k = 1 stated; PRL SM corroborates "Q_0 ≈ 2Q_L = 7200") ⇒ upper-bound effective tanδ = 1/Q_0 = 1/7200 = **1.3889e-4** → 2 s.f. **1.4e-4** (identical rounding convention as the superseded 1/4320 = 2.3148e-4 → 2.3e-4; still attributes ALL loss to the dielectric — the conservative-ceiling reading is unchanged in kind, only de-assumption'd). **Old value preserved as a dated superseded record** (the DELOAD_K comment block :281–285 becomes a dated two-era record: pre-2026-07-18 derivation kept verbatim + the closure note; Breeze/npj continue to take k = 0.2 — *theirs is stated in their papers*, consistent with the docstrings as verified).
- **Every consumer of `TOL.tan_delta_max` (grepped) and what changes:**
  | Consumer | What it does | Change |
  |---|---|---|
  | `src/cavity/surrogate/cv_gate.py:258–259` | `span = max − min`; `tan_delta_p95 = min + 0.95·span` (planning-P5 worst case) | No code change; the computed P5 value moves (span 1.3e-4 → 0.4e-4). Any regression-pinned numbers in `tests/test_surrogate_cv_gate.py:25,182,226` re-fitted by **independent calculation** (house rule) |
  | `src/cavity/sweep/dofs.py:343` | row-8 band `(tan_delta_min, tan_delta_max)` | Band narrows automatically; row provenance string :349 re-written ("Wu Q0≈4.3k" → the k=1 re-derivation) |
  | `tests/test_sweep_dofs.py:99–100` | pins band literals `(1.0e-4, 2.3e-4)` | Literal → `(1.0e-4, 1.4e-4)` (independently recomputed) |
  | `tests/test_surrogate_cv_gate.py:25,182,226` | draws/linspaces over the band | Follow TOL automatically; any hard-coded expected values re-fitted |
  | `src/cavity/provenance/constants.py:220` | definition | The change itself |
  - Additional stale-text mends (no logic): `ValidationTargets` docstring :254–257; `export/writer.py:324–332` de-load note ("Wu 2020 coupling unstated – SPEC §11 item 3" → dated closure text); SPEC §6 (see R11).
  - **NOT touched** (k = 0.2 compositions for *our/Booth* build, per the resolved Q12 ruling): `DELOAD_K` itself, `compose.kappa_c_hz`, `thermal/detuning.py`, `report_margin/turnover`, `centre_check.PINNED_CENTRE.q_l`, `validation/report_5a.py`, `figures/f5`.
- `wu_ring.v_mode_m3 = 0.32e-6` is **recorded on the entry but HELD OUT of every gate** — no `GateRowSpec` binds any measured anchor today (verified: GATE_ROWS reference only `booth`/`breeze` + the scalar bounds); the acceptance windows for the new anchor are **W2, a NEW named ratification item** (W-style; W1 = the Phase 1b window precedent), queued — **no gate row lands this changeset**, and V_mode's integration convention must be checked against the Booth convention (the 225/360 lesson) before W2 can ratify any V window. Single-sourcing note for W2's text: `wu_ring` and `wu_measured` describe the same physical device — `wu_ring` is the anchor of record from 2026-07-18; `wu_measured` is the frozen assumed-k-era print record.

### R9 — KAPPA_S annotation (docstring only)

`SpinResonanceLinewidth` docstring gains a dated SAME-BUILD block: the modelled build now has published points — κs = 1.1 MHz and κc = 2.5 MHz, **both ANGULAR** (provenance-table unit trap 1; cyclic κs/2π ≈ 0.175 MHz, κc/2π ≈ 0.398 MHz — cross-check: f/Q_L = 1.4495e9/3600 = 402.6 kHz ✓), 0.1% crystal vs 0.7 MHz FID at ~0.01% with W20's own concentration-effect attribution. Feeds the linewidth-branch question (which κs the margin law should carry for the Wu build) — **explicitly not resolved here**; values/band unchanged.

### R10 — archives (cowley_semple LFS + MANIFEST.sha256 convention)

- **(a) `calibration/data/raw/oxborrow_geometry_2026-07-17/`** — `.eml` (authoritative) + `.md` transcript (subject-H1 + bold From/To/CC/Date header + verbatim body) + `images/` if any + `MANIFEST.sha256` (GNU format, CRLF, `#` comments). **Blocked on Gmail re-auth** (token expired this session) or a user-side .eml export — see STOP S6.
- **(b) `calibration/data/raw/wu_build_papers_2026-07-18/`** — the three PDFs byte-copied from Zotero storage, input hashes pinned NOW (implementation must match):
  - `wu2020_pra_14_064017.pdf` ← `8ZL66UT2` — `fb39bc6c9e1f285185dcdc231de96f43bb1c89f140cf4c3097208efde018d055`
  - `wu2021_prl_127_053604.pdf` ← `73WWZCKU` — `d4409c97192299efedf8a91e3778f66eb7f0dd034d5dcccfa95d7a27be09283e`
  - `wu2021_prl_sm_proof.pdf` ← `EWVFZX3N` — `de6d7de4771f62bf5c304419c195666518ee32a0de4e7fb52988ddcb2dcf9455`
  Manifest `#` comment block records: Zotero item/attachment keys, "SM copy is the PROOF version", "PRA is a verified real PDF (%PDF-1.4, 10 pp) — the floating PhysRevApplied_14_064017.pdf ZIP-of-extracts is NOT this file and must never be archived".
- `.gitattributes` +1 line: `calibration/data/raw/**/*.pdf filter=lfs diff=lfs merge=lfs -text` (the blanket `calibration/data/** -text` already covers EOL).
- CI registration: `tests/test_calibration_integrity.py` gains two tests verifying the new archives via the existing generic `verify_manifest(archive_dir)` (`DEFAULT_ARCHIVE_DIR` + its `== 12` assertion untouched). **Noted, deliberately not fixed:** `oxborrow_tuning_2026-07-16/` remains CI-unverified and its `stotuningmech_assets/` path defect stays as-is (known, left by choice).
- **(c) dated annotations** beside the three thermal-paste records — `constants.py` `Crystal` docstring (:90 block), `SPEC.md:63` (2026-07-16 meeting item 2), `SPEC.md:248` (§7.T5 parenthetical): *"SUPERSEDED 2026-07-17 (Oxborrow, WRITTEN): 'generally just placed the STO ring on a plastic spacer and not bothered with paste' — the STO–copper thermal-paste half of the 2026-07-16 verbal stack is withdrawn at the written rung; the Vaseline crystal–STO half is untouched."* Annotate beside, never delete; verbal text preserved verbatim (verbal-record hygiene). `thermal/cylinder.py` records only the Vaseline half — untouched.

### R11 — SPEC.md changeset

- **Dated revision block** `**2026-07-18 update — geometry re-base: the Wu ring becomes the modelled build (Oxborrow-WRITTEN, 2026-07-17).**` appended at the bottom of the revision-note run (house style: bold-lead paragraph, newest last, above the closing `---`). Numbered outcomes, each at its rung: (1) re-base decision (written); (2) gap #3 CLOSED — k = 1 in print, Q_0 = 7200, tan_delta_max re-derived 2.3e-4 → 1.4e-4 (old value dated-superseded); (3) height fork Q13 opened (8.6 evidence-favoured); (4) Q2 re-scoped (mechanism identified/written+print; travel band open, asked 2026-07-18); (5) Q9 context change (real crystal-in-bore; dims planning-assumption + transfer flag; still unresolved); (6) κs/κc same-build annotation; (7) thermal-paste supersession (written beats verbal); (8) archives landed; (9) W2 queued (acceptance windows; V_mode 0.32 held out pending convention check).
- **§2**: Wu build becomes the modelled geometry (ring dims incl. fork, enclosure 14 mm radius w/ 28-mm-nominal caveat, internal height = the Q2 control at 15 mm as-operated, deck 3 mm, 26-mm piston with the 1 mm gap modelled, spacer sub-domain default ON at ε_r 2.53 datasheet-class, crystal-in-bore planning dims + transfer flag). `dielectric_shape ∈ {puck, torus}` → `{puck, torus, ring}`. **Booth stays, stated as the §5a solver-correctness anchor** (bullet re-worded, nothing deleted).
- **§5b**: crystal sentence gains the cross-build-transfer flag.
- **§6**: de-loading bullet → "k = 0.2 (Breeze 2017; npj) — Wu's k = 1 now STATED (gap #3 closed 2026-07-18)"; tanδ bullet's measured-device span "1.0–2.3×10⁻⁴ (Breeze Q₀ ≈ 10,700 ↔ Wu Q₀ ≈ 4,320)" → "1.0–1.4×10⁻⁴ (… ↔ Wu Q₀ = 7,200)" with a dated correction preserving the old figures in place (re-grade discipline: the stale quote comes into scope with the pass that touches it).
- **§11**: item 3 → CLOSED (dated, with the R8 consequence spelled out); new Q13 open item; Q2 item re-scoped (+ piston-gap-depth rider); W2 queued.
- **`SPEC_phase2_expanded.md:46`**: noise-DOF prose row mechanically re-worded (ring outer/inner radius + height; box height → control), dated inline note.
- **`docs/plans/layer_a_sweep_design.md`**: dated addendum block (the DOF-table design doc of record) recording the row re-parameterisation + Q13; the ticklish-possum implementation record stays untouched (dated record).
- New **`refs/wu_fig6_spacer_digitization.md`** + committed extraction script: the vector-path extraction, cyan-calibration method, both fork branches, vertex table, ±0.3 mm grade — so the spacer numbers are computed and re-fittable, never eyeballed.

---

## File-by-file diff summary

| # | File | Nature | Est. size |
|---|---|---|---|
| 1 | `src/cavity/provenance/constants.py` | +`ForkedConstant`, +`STO_HEIGHT_FORK`, +`WuSTORingGeometry`/`GEOM_WU_STO_RING`, +`CrossLinkedPolystyrene`/`CLPS`; `PublishedTarget` +`stated_coupling_k`+`deload_k`; `ValidationTargets` +`wu_ring` field, new `TARGETS.wu_ring` entry, `wu_measured` frozen + dated supersession note; `TolRanges.tan_delta_max` re-derivation + dated superseded record; DELOAD_K comment two-era record; `Crystal`+`KAPPA_S` docstring updates | ~+245 / −15 |
| 2 | `src/cavity/provenance/__init__.py` | 6 new exports | ~+10 |
| 3 | `src/cavity/forward_model/geometry.py` | RING enum+fields+validation+mask, `SpacerSpec`, piston step, shape-aware centre | ~+160 |
| 4 | `src/cavity/forward_model/materials.py` | `MaterialSpec.spacer` | ~+10 |
| 5 | `src/cavity/forward_model/build.py` | RING primitive branch; spacer primitives/selection/material/mesh; piston-step outline; `validate_spacer_consistency`; `BuiltModel` fields | ~+95 |
| 6 | `src/cavity/forward_model/solve.py` | ε-map spacer branch; `spacer_mask` into `FieldSample` | ~+15 |
| 7 | `src/cavity/forward_model/persistence.py` | fingerprint fields; `SCHEMA_VERSION` → 2 | ~+12 |
| 8 | `src/cavity/extraction/fields.py` | `FieldSample.spacer_mask` optional | ~+6 |
| 9 | `src/cavity/export/writer.py` | optional `spacer_mask` write; de-load note text | ~+12 |
| 10 | `src/cavity/export/schema.py` | `OPTIONAL_ARRAY_KEYS` + dtype check | ~+6 |
| 11 | `src/cavity/sweep/dofs.py` | `ForkTrace`, `SENTINEL_Q13`, 4 registrations, rows 1–4 re-parameterised, `box_height_m` row invalidation record, `SENTINEL_Q2` re-description, `_NOISE_DIM_NAMES` | ~+130 / −60 |
| 12 | `src/cavity/sweep/design.py` | Q13 blocker filter; `sto_height_m` materialise branch | ~+28 |
| 13 | `src/cavity/sweep/backend.py` | RING `draw_solve_spec` + `box_height_fallback_m` + `include_spacer`; `_PHASE1B_THETA_KEYS`; fresh mock levers/reference; refusal text | ~+70 / −45 |
| 14 | `src/cavity/sweep/driver.py` | explicit fallback arg at call site | ~+6 |
| 15 | `src/cavity/sweep/centre_check.py` | dated docstring note (Booth-record pins; Wu record pending) — no logic | ~+10 |
| 16 | `SPEC.md` | revision block; §2, §5b, §6, §11; R10c ×2 | ~+130 / −20 |
| 17 | `SPEC_phase2_expanded.md` | :46 prose rename, dated | ~+4 |
| 18 | `docs/plans/layer_a_sweep_design.md` | dated addendum | ~+18 |
| 19 | `refs/wu_fig6_spacer_digitization.md` (+ script under `refs/` or `scripts/`) | NEW — digitization record | ~+90 + script |
| 20 | `calibration/data/raw/oxborrow_geometry_2026-07-17/` | NEW archive (eml+md+manifest) — Gmail-gated | 3–4 files (LFS) |
| 21 | `calibration/data/raw/wu_build_papers_2026-07-18/` | NEW archive (3 PDFs + manifest, hashes pre-pinned above) | 4 files (LFS) |
| 22 | `.gitattributes` | +1 line (pdf LFS) | +1 |
| 23–31 | tests (below) | | ~+600 total |

Untouched by design (Booth anchor + archived records): `validation/providers.py`, `validation/gate.py`, `validation/report_5a.py`, `provenance/gate_targets.py`, `refs/gate_runs/**`, `thermal/**`, `calibration/**` code, `compose.py`, all figures except none.

---

## Test delta (committed verbatim)

**Before: 797 collected** (`pytest --collect-only -q tests`, run this session on the current tree at 94cf775). **After: 842 collected. Delta: +45** (49 new test functions/cases, 2 parametrize cases retired inside edited tests, 0 test functions deleted, 3 renamed, ~14 edited in place).

New files:
- `tests/test_provenance_wu_geometry.py` (**+14**): `test_literature_pins[…]` (parametrized ×6: sto_outer 6.0e-3, sto_inner 2.025e-3, box_inner_radius 14.0e-3, deck 3.0e-3, piston 13.0e-3, box_internal_height_asoperated 15e-3), `test_fork_candidates_are_8p5_and_8p6_mm`, `test_wu_height_fork_evidence_favoured_is_8p6`, `test_forked_constant_refuses_float_coercion`, `test_forked_constant_validates_candidates_and_sources`, `test_spacer_fields_match_fig6_digitization`, `test_clps_epsilon_r_pin_2p53`, `test_crystal_planning_fields_equal_breeze_import`, `test_tan_delta_max_rederivation_arithmetic` (independent: `round_2sf(1/(3600*(1+1))) == TOL.tan_delta_max == 1.4e-4`).
- `tests/test_provenance_targets.py` (**+7**): `test_wu_ring_records_stated_coupling_k1_and_print_f_1p4495`, `test_wu_ring_deload_yields_q0_7200`, `test_wu_measured_frozen_byte_identical_assumed_k_era`, `test_stated_coupling_forbidden_on_modelled_kind`, `test_deload_k_falls_back_to_assumed_constant`, `test_deload_k_refused_on_modelled_targets`, `test_no_gate_row_binds_wu_ring_until_w2`.

Edited files:
- `tests/test_geometry.py` (**+12**): `TestRingValidation` ×6 (`test_requires_height_inner_and_bottom`, `test_rejects_inner_not_below_outer`, `test_rejects_ring_crossing_axis`, `test_rejects_ring_punching_wall`, `test_rejects_ring_exceeding_box_height`, `test_rejects_minor_radius_with_ring`), `test_ring_mask`, `test_ring_centre_is_bottom_plus_half_height`, `TestSpacer` ×3 (`test_spacer_requires_ring`, `test_spacer_mask_empty_when_absent`, `test_spacer_base_must_meet_ring_bottom_and_lip_wraps_outside`… split as 2 + `test_piston_step_fields_jointly_required`) — 6+2+3+1 = 12. All existing PUCK/TORUS tests unchanged and passing.
- `tests/test_sweep_dofs.py` (**net +2**): edits to `test_table_has_nine_rows_in_design_doc_order`, `test_tan_delta_band_is_tol_span` (literal → 1.4e-4), `test_p_tune_row_is_q2_control` (+ new description asserts), `test_sentinel_question_ids`, `test_solve_gate_partition_matches_design_doc`, `test_empty_context_refuses_both_modes_naming_question_ids`, `test_mock_context_resolves_all_three_questions_for_shape` → `…_all_four_…`; `test_committed_nominals_import_from_provenance` params 6 → 5 (−1); `test_geometry_bands_are_nominal_plus_minus_machining_tol` params 4 → 3 (−1); new ×4: `test_sto_height_row_is_q13_fork_trace`, `test_fork_trace_requires_two_candidates_and_favoured_membership`, `test_fork_trace_is_not_arithmetic`, `test_fork_candidates_import_from_provenance_fork`.
- `tests/test_sweep_backend.py` (**+4**): renames `test_draw_solve_spec_builds_torus_geometry_and_sampled_materials` → `…_builds_ring_geometry_…`, `test_mock_f_responds_to_the_minor_radius_lever` → `test_mock_f_responds_to_the_sto_outer_radius_lever`; rewrite `test_draw_solve_spec_captures_phase1b_keys` (crystal-only); new ×4: `test_box_height_sourced_from_p_tune`, `test_box_height_fallback_required_without_p_tune`, `test_spacer_included_by_default_and_droppable`, `test_p_tune_specs_not_phase1b_but_q2_gate_still_refuses`.
- `tests/test_sweep_design.py` (**+1**): edit `test_geometry_uniform_variant_switches_rows_1_to_4_and_axial_offset`, `test_materialise_refuses_on_unresolved_rows_naming_questions` (+Q13); new `test_materialise_sto_height_band_from_q13_resolution`.
- `tests/test_sweep_resolutions.py` (**+0**): edit `test_solve_ready_exits_still_refuse_naming_q2_q9` → also names Q13.
- `tests/test_sweep_driver.py` (**+0**): edits (`test_rows_carry_exactly_the_raw_contract` θ-key set, `test_cli_mock_dry_run_end_to_end`).
- `tests/test_persistence.py` (**+2**): `test_fingerprint_carries_ring_and_spacer_fields`, `test_schema_version_is_2`.
- `tests/test_export_schema.py` (**+1**): `test_optional_spacer_mask_roundtrip`.
- `tests/test_calibration_integrity.py` (**+2**): `test_wu_build_papers_archive_intact`, `test_oxborrow_geometry_archive_intact` (the second lands only with the email archive — if Gmail stays blocked at implementation time, it defers and the committed AFTER becomes **841** with the deferral stated in the commit message; no silent drop).
- `tests/test_surrogate_cv_gate.py` (**+0**): pins re-fitted by independent calculation where hard-coded (lines 25/182/226 region) — count unchanged.

Sum: 14+7+12+2+4+1+0+0+2+1+2 = **+45** ⇒ **842**.

---

## Ordered implementation sequence (with STOP points)

0. **Pre-flight:** `git switch -c` a working branch. Gmail re-auth (user action: re-authorize the claude.ai Gmail connector, or export the 2026-07-17 email as .eml manually). Re-grep `Q13` repo-wide (must be absent).
   - **STOP S3** if `Q13` is already used anywhere.
   - **STOP S6** if the 2026-07-17 email's content contradicts this prompt's summary of it (different geometry recommendation, different numbers, or additional constraints not in R1–R11) — report, do not reconcile silently.
1. **Archive pass (R10a/b + tests 23):** copy PDFs from Zotero storage; **STOP S7** if any SHA-256 differs from the three pinned above (the storage files changed since verification). Write manifests, .gitattributes line, integrity tests. Commit (i): `archive: Wu build primary sources + Oxborrow geometry email 2026-07-17`.
2. **Provenance pass (R1/R5/R7/R8/R9/R10c):** constants.py + `__init__.py` + new provenance test files. Re-grep `tan_delta_max` and `wu_measured` consumers first — **STOP S1** if any consumer exists beyond the table in this plan. `wu_measured` fields stay byte-identical (supersession note only); the new `wu_ring` entry carries the ratified print values.
3. **Geometry-engine pass (R2):** geometry.py → materials.py → persistence.py → build.py → solve.py → fields.py → writer.py → schema.py + test_geometry/persistence/export_schema additions. Run the untouched PUCK/TORUS test subset before and after — **STOP S2** if any previously-green geometry/extraction test changes outcome.
4. **Sweep pass (R3/R4/R6):** dofs.py → design.py → backend.py → driver.py → centre_check.py docstring + their tests.
5. **SPEC/docs pass (R11):** SPEC.md, SPEC_phase2_expanded.md:46, layer_a_sweep_design.md addendum, refs digitization note + script.
6. **Full suite:** `pytest --collect-only -q` must report **842** (or 841 with the stated email-archive deferral) — **STOP S4** on any other number; then full run green (COMSOL-gated tests skip as they do today; no xfail changes — the wall-loss xfail regime is §5a's and untouched).
7. Commits (ii) `provenance+engine+sweep: Wu STO ring re-base — R1–R9 of the 2026-07-18 checkpoint` and (iii) `SPEC: geometry re-base changeset — s2 Wu build, s11 gap #3 closed, Q13/W2 opened`. No AI attribution trailers (house rule).

Standing STOP (S0, already discharged this session): any paper number disagreeing with the prompt → none found; the only flags raised are the two **surfaced in-repo/archive-copy discrepancies** (wu_measured.f_hz lineage; SM proof copy), both carried as flagged decisions, not silent picks.

---

## Out of scope (restated) and queued follow-ons (list only — licence-session / later)

Not planned, not touched: thermal BCs / S-ladder / 7.T6 (spacer's thermal identity recorded only), calibration/ code (except R10c annotation), surrogate/CV beyond the mechanical band fallout, any COMSOL solve, the d6ef37c `stotuningmech_assets/` path defect (known, left by choice), opportunistic refactors, Zotero duplicate-item cleanup.

Queued follow-ons (recorded in SPEC §11/W2 as appropriate; NOT this changeset):
1. With/without-spacer delta solve (licence session) — quantifies the sub-domain's f/Q effect; also validates the ε-map/mask plumbing live.
2. Wu-anchor validation solves once **W2** acceptance windows ratify (f at 1.4495 GHz; Q_0 = 7200 via the stated k = 1).
3. V_mode-convention check (0.32 cm³ vs the Booth 225/360 lesson) — precondition for any W2 V-window.
4. Mesh-ladder revalidation with the spacer sub-domain present.
5. Piston-gap sensitivity once gap depth / travel band land (Q2 reply).
6. Wu-build sweep-centre gate record → `centre_check` re-base.
7. Q13 resolution (Oxborrow written reply or caliper) → height band materialisation.
8. Wu-side crystal-dimension resolution (the ~4 mm question; Q9 context) and placement bands.
9. Published-SM pull to supersede the proof copy in the archive (optional, honesty upgrade).
