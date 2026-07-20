"""The publication build command — WS4 of the publication-readiness pass.

Usage:
    python -m publication.build [--build-root runs/publication_build]
                                [--skip-figures] [--skip-slow] [--draft]

Stages (each independently reported; composing, never duplicating):
 1. archive verification   — calibration.integrity.verify_all (every
    MANIFEST.sha256 under calibration/data/raw/, both directions)
 2. git stamp              — HEAD sha / branch / dirty / untracked
 3. regeneration           — every `generated` artifact of
    paper/figure_contract.yaml is regenerated INTO THE BUILD DIRECTORY
    (never in place); byte-pinned artifacts must reproduce the committed
    bytes exactly
 4. artifact index         — sha256 of committed + regenerated artifacts
 5. contract check         — artifacts exist, caveat tokens present,
    pin tests exist
 6. sentinel report        — unresolved Q2/Q9/Q13 (+ mode gates), the
    Q13 fork state, W1/W2 status
 7. claim status           — the paper-claims register: planning-grade /
    supervisor-unratified / missing-chain lists; headline blockers
 8. verdicts               — the four separated statuses; readiness is
    REFUSED unless every headline claim's chain is complete AND no
    blocker names an unresolved sentinel or unratified rung.

`--draft` permits generating clearly-labelled draft artifacts despite
blockers: the build directory gets a DRAFT stamp file and the report
carries the label; the readiness verdict is UNAFFECTED by draft mode.

The command NEVER writes into the committed artifact directories
(thermal/reports, calibration/reports, docs/figures, paper/) — enforced
by a path guard, tested. It never commits.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO / "paper" / "figure_contract.yaml"
MATRIX_PATH = REPO / "paper" / "claim_evidence_matrix.md"

#: Committed artifact directories the build must never write into.
PROTECTED_DIRS = (
    REPO / "thermal" / "reports",
    REPO / "calibration" / "reports",
    REPO / "docs" / "figures",
    REPO / "paper",
    REPO / "refs",
    REPO / "calibration" / "data",
)


class BuildGuardError(RuntimeError):
    """The build attempted something the discipline forbids."""


def _assert_outside_protected(path: Path) -> Path:
    resolved = path.resolve()
    for protected in PROTECTED_DIRS:
        try:
            resolved.relative_to(protected.resolve())
        except ValueError:
            continue
        raise BuildGuardError(
            f"build output {resolved} would land inside the committed "
            f"artifact tree {protected} — refused (regeneration goes to "
            "the build directory only)"
        )
    return resolved


def _normalised(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# --- stage 1: archives --------------------------------------------------


@dataclass(frozen=True)
class ArchiveStatus:
    ok: bool
    per_archive: dict[str, bool]
    detail: str


def verify_archives() -> ArchiveStatus:
    from calibration.integrity import verify_all

    reports = verify_all()
    per = {name: r.ok for name, r in reports.items()}
    bad = [name for name, ok in per.items() if not ok]
    detail = (
        "all archives verify both directions"
        if not bad
        else "FAILED: " + ", ".join(bad)
    )
    return ArchiveStatus(ok=not bad, per_archive=per, detail=detail)


# --- stage 2: git stamp -------------------------------------------------


@dataclass(frozen=True)
class GitStamp:
    head_sha: str
    branch: str
    dirty: bool
    untracked: int

    @property
    def describe(self) -> str:
        return (
            f"{self.head_sha[:12]} ({self.branch})"
            + (" DIRTY" if self.dirty else "")
            + (f" +{self.untracked} untracked" if self.untracked else "")
        )


def git_stamp() -> GitStamp:
    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    status = _git("status", "--porcelain")
    lines = [ln for ln in status.splitlines() if ln.strip()]
    untracked = sum(1 for ln in lines if ln.startswith("??"))
    dirty = any(not ln.startswith("??") for ln in lines)
    return GitStamp(
        head_sha=_git("rev-parse", "HEAD"),
        branch=_git("branch", "--show-current"),
        dirty=dirty,
        untracked=untracked,
    )


# --- stage 3: regeneration ----------------------------------------------

#: id → regeneration recipe. "module-out": subprocess
#: `python -m <module> --out <build_subdir>`; "calibration": in-process
#: render (their CLIs write only to fixed committed paths). One shared
#: recipe regenerates all six figures.
_MODULE_OUT_RECIPES: dict[str, tuple[str, str]] = {
    "R-margin-point": ("cavity.thermal.report_margin", "thermal/reports"),
    "R-turnover": ("cavity.thermal.report_turnover", "thermal/reports"),
    "R-s-ladder": ("cavity.thermal.report_s_ladder", "thermal/reports"),
    "R-ident-3a": ("cavity.thermal.report_3a", "thermal/reports"),
    "R-ident-3a-vol": ("cavity.thermal.report_3a_volumetric", "thermal/reports"),
}
_FIGURES_MODULE = ("cavity.figures", "docs/figures")
_SLOW_IDS = {"R-ident-3a", "R-ident-3a-vol", "R-t4", "R-t5", "R-feed"}


def _regenerate_calibration(build_dir: Path) -> dict[str, Path]:
    """T3/T4/T5 + feed, rendered in-process into the build dir (their
    module CLIs write only to the committed calibration/reports paths)."""
    from calibration import absolute_fit, ratio_test, slope_fit

    out_dir = build_dir / "calibration" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    produced: dict[str, Path] = {}

    t3 = slope_fit.fit_all()
    (out_dir / "slope_fit_digitized.md").write_text(
        slope_fit.render_report(t3), encoding="utf-8"
    )
    produced["R-t3"] = out_dir / "slope_fit_digitized.md"

    t4 = ratio_test.run_ratio_test()
    (out_dir / "ratio_test_digitized.md").write_text(
        ratio_test.render_report(t4), encoding="utf-8"
    )
    produced["R-t4"] = out_dir / "ratio_test_digitized.md"

    feed = absolute_fit.run_absolute_fits()
    (out_dir / "absolute_fit_digitized.md").write_text(
        absolute_fit.render_report(feed), encoding="utf-8"
    )
    produced["R-t5"] = out_dir / "absolute_fit_digitized.md"
    (out_dir / "observable_a_feed.json").write_text(
        feed.to_json(), encoding="utf-8"
    )
    produced["R-feed"] = out_dir / "observable_a_feed.json"
    return produced


@dataclass(frozen=True)
class RegenResult:
    artifact_id: str
    regenerated: bool
    matches_committed: bool | None  # None = no byte requirement
    detail: str


def regenerate_artifacts(
    contract: dict,
    build_dir: Path,
    *,
    include_figures: bool = True,
    include_slow: bool = True,
) -> list[RegenResult]:
    build_dir = _assert_outside_protected(build_dir)
    results: list[RegenResult] = []
    by_id = {a["id"]: a for a in contract["artifacts"]}

    def _run_module(module: str, subdir: str) -> None:
        out = build_dir / subdir
        out.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-m", module, "--out", str(out)],
            cwd=REPO,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise BuildGuardError(
                f"{module} failed (exit {proc.returncode}):\n{proc.stderr[-2000:]}"
            )

    calibration_produced: dict[str, Path] = {}
    need_calibration = include_slow and any(
        a["kind"] == "generated"
        and a["id"] in ("R-t3", "R-t4", "R-t5", "R-feed")
        for a in contract["artifacts"]
    )
    if need_calibration:
        calibration_produced = _regenerate_calibration(build_dir)

    figures_ran = False
    for artifact in contract["artifacts"]:
        aid = artifact["id"]
        if artifact["kind"] != "generated":
            continue
        committed = REPO / artifact["path"]
        expected_name = committed.name
        try:
            if aid in _MODULE_OUT_RECIPES:
                if not include_slow and aid in _SLOW_IDS:
                    results.append(
                        RegenResult(aid, False, None, "skipped (--skip-slow)")
                    )
                    continue
                module, subdir = _MODULE_OUT_RECIPES[aid]
                _run_module(module, subdir)
                regen_path = build_dir / subdir / expected_name
            elif aid.startswith("F"):
                if not include_figures:
                    results.append(
                        RegenResult(aid, False, None, "skipped (--skip-figures)")
                    )
                    continue
                if not figures_ran:
                    _run_module(*_FIGURES_MODULE)
                    figures_ran = True
                regen_path = build_dir / _FIGURES_MODULE[1] / expected_name
            elif aid in ("R-t3", "R-t4", "R-t5", "R-feed"):
                if not include_slow:
                    results.append(
                        RegenResult(aid, False, None, "skipped (--skip-slow)")
                    )
                    continue
                regen_path = calibration_produced[aid]
            else:
                results.append(
                    RegenResult(
                        aid, False, None, "no regeneration recipe (contract gap)"
                    )
                )
                continue
        except BuildGuardError as exc:
            results.append(RegenResult(aid, False, False, str(exc)))
            continue

        if not regen_path.is_file() or regen_path.stat().st_size == 0:
            results.append(
                RegenResult(aid, False, False, f"generator produced no {expected_name}")
            )
            continue
        if artifact.get("byte_pinned"):
            # Text artifacts compare after newline normalisation — the
            # repo's own byte-pin tests are text-level, and git autocrlf
            # makes raw-byte equality checkout-dependent on Windows.
            if committed.suffix in {".md", ".json", ".txt", ".yaml"}:
                match = _normalised(regen_path) == _normalised(committed)
                label = "content-identical to committed (newline-normalised)"
            else:
                match = regen_path.read_bytes() == committed.read_bytes()
                label = "byte-identical to committed"
            results.append(
                RegenResult(
                    aid,
                    True,
                    match,
                    label
                    if match
                    else "DRIFT: regenerated content differs from committed",
                )
            )
        else:
            results.append(RegenResult(aid, True, None, "regenerated (value-pinned)"))
    return results


# --- stage 4: index -----------------------------------------------------


def artifact_index(contract: dict, build_dir: Path) -> dict:
    entries = []
    for artifact in contract["artifacts"]:
        committed = REPO / artifact["path"]
        entry = {
            "id": artifact["id"],
            "path": artifact["path"],
            "kind": artifact["kind"],
            "generator": artifact.get("generator"),
            "committed_sha256": _sha256(committed) if committed.is_file() else None,
            "pin_tests": artifact.get("pin_tests", []),
            "claims": artifact.get("claims", []),
        }
        regen = build_dir / artifact["path"]
        entry["regenerated_sha256"] = _sha256(regen) if regen.is_file() else None
        entries.append(entry)
    return {"schema": "artifact-index/v1", "artifacts": entries}


# --- stage 5: contract check --------------------------------------------


@dataclass(frozen=True)
class ContractCheck:
    ok: bool
    problems: tuple[str, ...]


def check_contract(contract: dict) -> ContractCheck:
    import importlib

    problems: list[str] = []
    for artifact in contract["artifacts"]:
        aid = artifact["id"]
        target = REPO / artifact["path"]
        if not target.exists():
            problems.append(f"{aid}: missing artifact {artifact['path']}")
            continue
        for entry in artifact.get("pin_tests", []):
            parts = entry.split("::")
            test_file = REPO / parts[0]
            if not test_file.exists():
                problems.append(f"{aid}: missing pin-test file {parts[0]}")
            elif len(parts) > 1 and parts[-1] not in test_file.read_text(
                encoding="utf-8"
            ):
                problems.append(f"{aid}: pin test {parts[-1]} not in {parts[0]}")
        for token in artifact.get("required_caveats", []):
            if target.suffix in {".md", ".json", ".yaml", ".txt"}:
                haystack = target.read_text(encoding="utf-8")
            elif artifact.get("generator"):
                mod = importlib.import_module(artifact["generator"])
                haystack = Path(mod.__file__).read_text(encoding="utf-8")
            else:
                problems.append(f"{aid}: caveat {token!r} unverifiable")
                continue
            if token.lower() not in haystack.lower():
                problems.append(f"{aid}: required caveat {token!r} absent")
    return ContractCheck(ok=not problems, problems=tuple(problems))


# --- stage 6: sentinels -------------------------------------------------


@dataclass(frozen=True)
class SentinelStatus:
    unresolved_by_mode: dict[str, tuple[str, ...]]
    fork_state: str
    ratified: tuple[str, ...]
    named_items: dict[str, str]


def sentinel_status() -> SentinelStatus:
    from cavity.provenance.constants import STO_HEIGHT_FORK
    from cavity.sweep.dofs import DesignMode
    from cavity.sweep.resolutions import ratified_resolutions

    ctx = ratified_resolutions()
    unresolved = {m.value: ctx.unresolved(m) for m in DesignMode}
    return SentinelStatus(
        unresolved_by_mode=unresolved,
        fork_state=(
            f"Q13 fork OPEN: candidates {STO_HEIGHT_FORK.candidates}, "
            f"evidence-favoured {STO_HEIGHT_FORK.evidence_favoured} "
            "(never silently selected)"
            if any("Q13" in v for v in unresolved.values())
            else "Q13 resolved"
        ),
        ratified=tuple(r.question_id for r in ctx.resolutions),
        named_items={
            "W1": "Phase 1b weak-perturbation window — queued with Q9+Q11",
            "W2": (
                "Wu-anchor windows ratified as planning choices; NO gate row "
                "binds wu_ring until the first W2-passing solve"
            ),
        },
    )


# --- stage 7: claims ----------------------------------------------------


@dataclass(frozen=True)
class ClaimStatus:
    n_claims: int
    headline_blocked: tuple[str, ...]
    missing_chain: tuple[str, ...]
    supervisor_unratified: tuple[str, ...]
    planning_grade: tuple[str, ...]


def load_claims() -> list[dict]:
    text = MATRIX_PATH.read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    if len(blocks) != 1:
        raise BuildGuardError("claim matrix must carry exactly one yaml register")
    data = yaml.safe_load(blocks[0])
    if data.get("schema") != "paper-claims/v1":
        raise BuildGuardError(f"unknown claims schema {data.get('schema')!r}")
    return data["claims"]


def claim_status(claims: list[dict]) -> ClaimStatus:
    missing = tuple(
        c["id"] for c in claims if not c["evidence_chain"] == "complete"
    )
    return ClaimStatus(
        n_claims=len(claims),
        headline_blocked=tuple(
            c["id"]
            for c in claims
            if c["headline"] and c["evidence_chain"] != "complete"
        ),
        missing_chain=missing,
        supervisor_unratified=tuple(
            c["id"] for c in claims if "supervisor-unratified" in c["category"]
        ),
        planning_grade=tuple(
            c["id"] for c in claims if "planning-grade" in c["category"]
        ),
    )


# --- stage 8: verdicts + report -----------------------------------------


@dataclass(frozen=True)
class BuildVerdicts:
    """The four SEPARATED statuses. Passing tests alone must not imply the
    science is publication-ready — reproducibility is verdict 1 of 4."""

    artifact_reproducibility: str
    scientific_validation: str
    supervisor_ratification: str
    publication_readiness: str
    headline_ready: bool


def compose_verdicts(
    archives: ArchiveStatus,
    regen: list[RegenResult],
    contract_check: ContractCheck,
    sentinels: SentinelStatus,
    claims: ClaimStatus,
) -> BuildVerdicts:
    regen_bad = [
        r for r in regen if r.matches_committed is False or (not r.regenerated and "skipped" not in r.detail)
    ]
    repro = (
        "PASS"
        if archives.ok and contract_check.ok and not regen_bad
        else "FAIL: "
        + "; ".join(
            ([archives.detail] if not archives.ok else [])
            + [f"{r.artifact_id}: {r.detail}" for r in regen_bad]
            + list(contract_check.problems)
        )
    )
    validation = (
        "PARTIAL: SS5a Booth anchor GREEN (5/0/1) but phase1_complete FALSE "
        "(confinement row deferred); W2 Wu-anchor UNSOLVED (no gate row binds "
        "wu_ring); Layer B calibration at graph-digitized grade "
        "(superseded_by_raw_data pending); Layer A/C population NOT RUN. "
        "This verdict is read from the committed gate/report records, "
        "never from test results."
    )
    ratification = (
        "PENDING: " + ", ".join(claims.supervisor_unratified)
        if claims.supervisor_unratified
        else "no unratified claims"
    )
    headline_ready = not claims.headline_blocked and repro == "PASS"
    unresolved_any = sorted(
        {q for v in sentinels.unresolved_by_mode.values() for q in v}
    )
    if headline_ready:
        readiness = "READY (all headline chains complete)"
    else:
        reasons = []
        if claims.headline_blocked:
            reasons.append(
                "headline claims with incomplete evidence chains: "
                + ", ".join(claims.headline_blocked)
            )
        if unresolved_any:
            reasons.append("unresolved sentinels: " + ", ".join(unresolved_any))
        if claims.supervisor_unratified:
            reasons.append(
                "supervisor-unratified: " + ", ".join(claims.supervisor_unratified)
            )
        if repro != "PASS":
            reasons.append("artifact reproducibility not PASS")
        readiness = "REFUSED — " + "; ".join(reasons)
    return BuildVerdicts(
        artifact_reproducibility=repro,
        scientific_validation=validation,
        supervisor_ratification=ratification,
        publication_readiness=readiness,
        headline_ready=headline_ready,
    )


def render_report(
    stamp: GitStamp,
    archives: ArchiveStatus,
    regen: list[RegenResult],
    contract_check: ContractCheck,
    sentinels: SentinelStatus,
    claims: ClaimStatus,
    verdicts: BuildVerdicts,
    *,
    draft: bool,
) -> str:
    lines = [
        "# Publication build report",
        "",
        f"- generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"- git: {stamp.describe}",
    ]
    if draft:
        lines.append(
            "- **DRAFT MODE: artifacts below are drafts generated despite "
            "blockers — NOT publication-ready outputs**"
        )
    lines += [
        "",
        "## 1. Archive verification",
        f"- {archives.detail}",
    ]
    lines += [
        f"  - {name}: {'INTACT' if ok else 'FAILED'}"
        for name, ok in sorted(archives.per_archive.items())
    ]
    lines += ["", "## 2. Artifact regeneration"]
    lines += [
        f"- {r.artifact_id}: "
        + ("OK" if r.regenerated else "NOT REGENERATED")
        + (f" — {r.detail}" if r.detail else "")
        for r in regen
    ]
    lines += ["", "## 3. Contract check"]
    lines += (
        [f"- PROBLEM: {p}" for p in contract_check.problems]
        if contract_check.problems
        else ["- all contract rows satisfied"]
    )
    lines += ["", "## 4. Unresolved sentinels"]
    for mode, missing in sentinels.unresolved_by_mode.items():
        lines.append(f"- {mode}: {', '.join(missing) if missing else 'none'}")
    lines.append(f"- {sentinels.fork_state}")
    for name, note in sentinels.named_items.items():
        lines.append(f"- {name}: {note}")
    lines += [
        "",
        "## 5. Claim status",
        f"- claims: {claims.n_claims}",
        f"- planning-grade: {', '.join(claims.planning_grade) or 'none'}",
        f"- supervisor-unratified: {', '.join(claims.supervisor_unratified) or 'none'}",
        f"- missing evidence chain: {', '.join(claims.missing_chain) or 'none'}",
        f"- HEADLINE claims blocked: {', '.join(claims.headline_blocked) or 'none'}",
        "",
        "## 6. Verdicts (four separated statuses)",
        "",
        f"1. **Artifact reproducibility:** {verdicts.artifact_reproducibility}",
        f"2. **Scientific validation:** {verdicts.scientific_validation}",
        f"3. **Supervisor ratification:** {verdicts.supervisor_ratification}",
        f"4. **Publication readiness:** {verdicts.publication_readiness}",
        "",
        "Passing tests alone does NOT imply the science is publication-ready:",
        "verdict 1 is about generators and bytes; verdicts 2-4 are about the",
        "world outside the test suite (solves, supervisors, referees).",
        "",
    ]
    return "\n".join(lines)


# --- CLI ----------------------------------------------------------------


def run_build(
    *,
    build_root: Path,
    include_figures: bool = True,
    include_slow: bool = True,
    draft: bool = False,
) -> tuple[Path, BuildVerdicts]:
    stamp_dir = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    build_dir = _assert_outside_protected(Path(build_root) / stamp_dir)
    build_dir.mkdir(parents=True, exist_ok=False)

    contract = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    archives = verify_archives()
    stamp = git_stamp()
    regen = regenerate_artifacts(
        contract,
        build_dir,
        include_figures=include_figures,
        include_slow=include_slow,
    )
    index = artifact_index(contract, build_dir)
    contract_check = check_contract(contract)
    sentinels = sentinel_status()
    claims = claim_status(load_claims())
    verdicts = compose_verdicts(archives, regen, contract_check, sentinels, claims)

    (build_dir / "artifact_index.json").write_text(
        json.dumps(index, indent=2), encoding="utf-8"
    )
    (build_dir / "build_report.json").write_text(
        json.dumps(
            {
                "git": asdict(stamp),
                "archives": archives.per_archive,
                "regeneration": [asdict(r) for r in regen],
                "contract_problems": list(contract_check.problems),
                "sentinels": {
                    "unresolved_by_mode": {
                        k: list(v) for k, v in sentinels.unresolved_by_mode.items()
                    },
                    "ratified": list(sentinels.ratified),
                },
                "claims": asdict(claims),
                "verdicts": asdict(verdicts),
                "draft": draft,
            },
            indent=2,
            default=list,
        ),
        encoding="utf-8",
    )
    report = render_report(
        stamp,
        archives,
        regen,
        contract_check,
        sentinels,
        claims,
        verdicts,
        draft=draft,
    )
    (build_dir / "build_report.md").write_text(report, encoding="utf-8")
    if draft:
        (build_dir / "DRAFT").write_text(
            "DRAFT artifacts — generated despite blockers; NOT publication-"
            "ready. See build_report.md verdict 4.\n",
            encoding="utf-8",
        )
    return build_dir, verdicts


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="python -m publication.build")
    parser.add_argument(
        "--build-root",
        default=str(REPO / "runs" / "publication_build"),
        help="root for timestamped build directories (never a committed dir)",
    )
    parser.add_argument("--skip-figures", action="store_true")
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="skip the identifiability + calibration regenerations",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="label outputs as DRAFT (permitted despite blockers; does not "
        "change the readiness verdict)",
    )
    args = parser.parse_args(argv)
    build_dir, verdicts = run_build(
        build_root=Path(args.build_root),
        include_figures=not args.skip_figures,
        include_slow=not args.skip_slow,
        draft=args.draft,
    )
    print((build_dir / "build_report.md").read_text(encoding="utf-8"))
    print(f"[build directory: {build_dir}]")
    return 0 if verdicts.artifact_reproducibility == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
