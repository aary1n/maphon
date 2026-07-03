"""Proven MPh conventions, pinned against the supervisor reference model.

This is the guarded successor of the interactive probe sessions that
established (SPEC §11 gap #4, resolved 2026-07-02; eval-path mechanism
pinned 2026-07-03):

  - `model.evaluate()` returns float64 arrays only; the complex
    eigenfrequency is assembled in Python from `real(freq)` and
    `imag(freq)` — no `complex=True` kwarg exists;
  - the eigenfrequency must be read from the BARE solver variable
    `freq` (= i*lambda/(2*pi), complex). The interface-scoped
    `<tag>.freq` is realified per solution number in results
    evaluation, so `imag(<tag>.freq)` reads identically 0 on the lossy
    reference — THAT is the retracted probe bug, and it is asserted
    here as an artifact so nobody "simplifies" solve.py back onto the
    broken path;
  - the Q convention is f'/(2 f''), supervisor-confirmed: on the lossy
    reference it reproduces emw.Qfactor mode-by-mode;
  - the interface tag is discovered from the model's physics node,
    never hardcoded (a supervisor model with a non-emw tag has been
    observed).

The Oxborrow sapphire model is method-reference only (weak form,
lossless, no Q) and is deliberately NOT probed for conventions here.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytestmark = pytest.mark.requires_comsol

_REPO_ROOT = Path(__file__).resolve().parent.parent
_LOSSY_MPH = _REPO_ROOT / "refs" / "comsol" / "booth" / "2D Resonator Lossy.mph"


def _physics_tags(model) -> list[str]:
    return [str(node.tag()) for node in (model / "physics")]


def _qfactor_tag(model) -> str:
    """Discover the RF interface tag from the physics node (SPEC: never
    hardcode 'emw' in shared code; 'emw' is only the expected default)."""
    tags = _physics_tags(model)
    for tag in tags:
        try:
            model.evaluate(f"{tag}.Qfactor")
            return tag
        except Exception:
            continue
    pytest.fail(
        f"no physics interface exposes <tag>.Qfactor; tags found: {tags}"
    )


@pytest.fixture(scope="module")
def lossy_model(comsol_client):
    if not _LOSSY_MPH.is_file():
        pytest.skip(f"reference model not present: {_LOSSY_MPH}")
    model = comsol_client.load(str(_LOSSY_MPH))
    # The pristine handover file carries no stored solution and must
    # stay that way (refs/comsol/README.md: never solve & save into
    # it). Solve in memory only; the model is never saved back to disk.
    model.solve()
    yield model
    try:
        comsol_client.remove(model)
    except Exception:
        pass


@pytest.fixture(scope="module")
def spectrum(lossy_model):
    f_re = np.atleast_1d(np.asarray(lossy_model.evaluate("real(freq)")))
    f_im = np.atleast_1d(np.asarray(lossy_model.evaluate("imag(freq)")))
    return f_re, f_im


class TestEvaluateConventions:
    def test_evaluate_returns_float64_not_complex(self, spectrum):
        f_re, f_im = spectrum
        assert not np.iscomplexobj(f_re)
        assert not np.iscomplexobj(f_im)
        assert f_re.dtype == np.float64
        assert f_im.dtype == np.float64

    def test_interface_tag_is_discoverable(self, lossy_model):
        tag = _qfactor_tag(lossy_model)
        assert tag in _physics_tags(lossy_model)
        # The booth reference is supervisor-confirmed to be the packaged
        # RF interface; its default tag is emw.
        assert tag == "emw"


class TestLossyReferenceConvention:
    def test_bare_freq_imag_positive_near_1p45ghz(self, spectrum):
        """The retracted-probe regression, positive direction: the mode
        nearest 1.45 GHz carries strictly positive imag through the
        bare-`freq` eval path solve.py uses."""
        f_re, f_im = spectrum
        idx = int(np.argmin(np.abs(f_re - 1.45e9)))
        assert f_im[idx] > 0.0, (
            "imag(freq) = 0 on the lossy reference — the eigenfrequency "
            "eval path is broken again (SPEC §11 gap #4)."
        )

    def test_interface_scoped_freq_is_realified_artifact(
        self, lossy_model, spectrum
    ):
        """The retracted-probe regression, trap direction: the
        interface-scoped `<tag>.freq` is realified in results
        evaluation (imag reads 0 despite a lossy solve). solve.py must
        NEVER read imag through the interface-scoped variable. If this
        assertion ever fails, COMSOL changed the realification
        behaviour — re-verify conventions before touching solve.py,
        which uses bare `freq` and is correct either way."""
        _, f_im_bare = spectrum
        tag = _qfactor_tag(lossy_model)
        f_im_tag = np.atleast_1d(
            np.asarray(lossy_model.evaluate(f"imag({tag}.freq)"))
        )
        assert np.all(f_im_tag == 0.0)
        assert np.any(f_im_bare > 0.0)

    def test_q_convention_reproduces_qfactor(self, lossy_model, spectrum):
        """Q = f'/(2 f'') from the bare complex `freq` must reproduce
        the interface's own Qfactor mode-by-mode — the supervisor-
        confirmed convention (in person, 2026-07-02), now pinned
        numerically."""
        f_re, f_im = spectrum
        tag = _qfactor_tag(lossy_model)
        q_emw = np.atleast_1d(
            np.asarray(lossy_model.evaluate(f"{tag}.Qfactor"))
        )
        lossy = f_im > 0.0
        assert np.any(lossy)
        q_formula = f_re[lossy] / (2.0 * f_im[lossy])
        assert np.allclose(q_formula, q_emw[lossy], rtol=1e-9)

    def test_q_plausible_near_1p45ghz(self, spectrum):
        f_re, f_im = spectrum
        idx = int(np.argmin(np.abs(f_re - 1.45e9)))
        q = f_re[idx] / (2.0 * f_im[idx])
        # Dielectric-resonator scale, not an inverted/mangled reading.
        assert 1.0e2 < q < 1.0e7

    def test_spectrum_is_dense_near_search(self, spectrum):
        """The premise of the SPEC §2 anti-proximity rule: multiple
        modes cluster near 1.45 GHz (observed: 1.4513 / 1.5224 GHz, 71
        MHz apart), so nearest-eigenvalue picking is unsafe. The
        synthetic trap test in test_mode_id.py asserts the picker's
        behaviour; this pins the physical premise."""
        f_re, _ = spectrum
        near = np.sort(f_re[(f_re > 1.3e9) & (f_re < 1.6e9)])
        if near.size < 2:
            pytest.skip(
                "solved spectrum keeps < 2 modes near 1.45 GHz; "
                "density premise not checkable on this file"
            )
        assert float(np.min(np.diff(near))) < 1.5e8
