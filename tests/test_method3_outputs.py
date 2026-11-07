"""Regression checks against the saved, pre-change image and file hashes."""

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from spatial_image_enhancement.algorithms import (
    bilateral_filter, combined_enhancement, contrast_stretch, gamma_transform,
    histogram_equalize, stretch_endpoints,
)
from spatial_image_enhancement.cli import (
    BILATERAL_PARAMETERS, COMBINED_OUTPUT_MAX, GAMMAS, HIGH_PERCENTILE,
    LOW_PERCENTILE, NAMES, _preserve_previous_method3,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "outputs/baseline_method3"


def read_gray(path):
    with Image.open(path) as source:
        assert source.mode == "L"
        assert source.size == (600, 400)
        return np.asarray(source).copy()


@pytest.mark.parametrize("name", NAMES)
def test_methods_1_and_2_are_pixel_identical_to_previous_versions(name):
    manifest = json.loads((BASELINE / "verification_manifest.json").read_text(encoding="utf-8"))
    original = read_gray(ROOT / "HW1_test_image" / name)
    for folder, result in (("gamma", gamma_transform(original, GAMMAS[name])),
                           ("equalized", histogram_equalize(original))):
        relative = f"outputs/{folder}/{name}"
        previous_hash = manifest["pixels"][relative]
        assert hashlib.sha256(result.tobytes()).hexdigest() == previous_hash
        assert hashlib.sha256(read_gray(ROOT / relative).tobytes()).hexdigest() == previous_hash


@pytest.mark.parametrize("name", NAMES)
def test_all_six_method3_results_baselines_and_native_resolution_comparisons(name):
    original = read_gray(ROOT / "HW1_test_image" / name)
    previous = read_gray(BASELINE / "combined" / name)
    assert np.array_equal(previous, contrast_stretch(gamma_transform(original, GAMMAS[name]),
                                                   LOW_PERCENTILE, HIGH_PERCENTILE, COMBINED_OUTPUT_MAX[name]))
    updated = read_gray(ROOT / "outputs/combined" / name)
    assert np.array_equal(updated, combined_enhancement(original, GAMMAS[name], LOW_PERCENTILE,
                                                       HIGH_PERCENTILE, COMBINED_OUTPUT_MAX[name],
                                                       **BILATERAL_PARAMETERS))
    assert not np.array_equal(updated, previous)
    path = ROOT / "outputs/method3_comparisons" / f"{Path(name).stem}_original_old_new.png"
    with Image.open(path) as comparison:
        assert comparison.size == (1800, 476)
        for column, expected in enumerate((original, previous, updated)):
            panel = comparison.crop((column * 600, 76, (column + 1) * 600, 476)).convert("L")
            assert np.array_equal(np.asarray(panel), expected)


def test_inputs_methods_1_and_2_and_previous_results_preserved_byte_for_byte():
    manifest = json.loads((BASELINE / "verification_manifest.json").read_text(encoding="utf-8"))
    protected = ("HW1_test_image/", "outputs/original/", "outputs/gamma/",
                 "outputs/equalized/", "outputs/gamma_trials/", "outputs/baseline_method3/")
    for relative, expected in manifest["files"].items():
        if relative.startswith(protected):
            assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative


@pytest.mark.parametrize("name", NAMES)
def test_method3_matches_user_approved_pixels_and_parameters(name):
    approved = json.loads((ROOT / "outputs/method3_approved_manifest.json").read_text(encoding="utf-8"))
    actual = read_gray(ROOT / "outputs/combined" / name)
    assert hashlib.sha256(actual.tobytes()).hexdigest() == approved["pixel_sha256"][name]
    assert BILATERAL_PARAMETERS == approved["bilateral"]
    assert GAMMAS == approved["gammas"]
    assert [LOW_PERCENTILE, HIGH_PERCENTILE] == approved["stretch_percentiles"]
    assert COMBINED_OUTPUT_MAX == approved["output_max"]


def test_metadata_records_actual_post_bilateral_gamma_stretch_endpoints():
    summary = json.loads((ROOT / "outputs/results.json").read_text(encoding="utf-8"))
    assert summary["method3_pipeline"] == ["original", "bilateral", "gamma", "contrast_stretch"]
    assert summary["bilateral"]["selection"] == "approved by user after visual review"
    for key, value in BILATERAL_PARAMETERS.items():
        assert summary["bilateral"][key] == value
    for name in NAMES:
        original = read_gray(ROOT / "HW1_test_image" / name)
        gamma = gamma_transform(bilateral_filter(original, **BILATERAL_PARAMETERS), GAMMAS[name])
        assert summary["images"][name]["stretch_intensities_after_gamma"] == list(
            stretch_endpoints(gamma, LOW_PERCENTILE, HIGH_PERCENTILE))


def test_existing_results_snapshotted_once_before_replacement(tmp_path):
    (tmp_path / "combined").mkdir()
    (tmp_path / "comparisons").mkdir()
    result = tmp_path / "combined/1-1.png"
    result.write_bytes(b"old image")
    (tmp_path / "comparisons/1-1_comparison.png").write_bytes(b"old comparison")
    metadata = tmp_path / "results.json"
    metadata.write_text('{"method": "gamma then percentile contrast stretch"}', encoding="utf-8")
    _preserve_previous_method3(tmp_path)
    baseline = tmp_path / "baseline_method3"
    assert (baseline / "combined/1-1.png").read_bytes() == b"old image"
    assert (baseline / "comparisons/1-1_comparison.png").read_bytes() == b"old comparison"
    assert (baseline / "results.json").read_bytes() == metadata.read_bytes()
    result.write_bytes(b"new image")
    # Even before updated metadata is written, an existing baseline is immutable.
    _preserve_previous_method3(tmp_path)
    assert (baseline / "combined/1-1.png").read_bytes() == b"old image"
    metadata.write_text('{"method": "bilateral then gamma then percentile contrast stretch"}', encoding="utf-8")
    _preserve_previous_method3(tmp_path)
    assert (baseline / "combined/1-1.png").read_bytes() == b"old image"
