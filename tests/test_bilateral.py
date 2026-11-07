"""Independent scalar reference checks for the manual bilateral filter."""

import math

import numpy as np
import pytest

from spatial_image_enhancement.algorithms import (
    bilateral_filter, combined_enhancement, contrast_stretch, gamma_transform,
)


def scalar_reference(image, window_size, sigma_spatial, sigma_range):
    """Deliberately simple per-pixel implementation with clipped neighborhoods."""
    result = np.empty_like(image)
    radius = window_size // 2
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            total, normalization = 0.0, 0.0
            for ny in range(max(0, y - radius), min(image.shape[0], y + radius + 1)):
                for nx in range(max(0, x - radius), min(image.shape[1], x + radius + 1)):
                    spatial = math.exp(-((ny - y)**2 + (nx - x)**2) / (2 * sigma_spatial**2))
                    difference = int(image[ny, nx]) - int(image[y, x])
                    intensity = math.exp(-difference**2 / (2 * sigma_range**2))
                    weight = spatial * intensity
                    total += weight * int(image[ny, nx])
                    normalization += weight
            result[y, x] = min(255, max(0, math.floor(total / normalization + 0.5)))
    return result


@pytest.mark.parametrize("level", [0, 1, 85, 128, 254, 255])
@pytest.mark.parametrize("shape", [(1, 1), (1, 7), (7, 1), (2, 3), (9, 11)])
def test_constants_preserve_every_pixel_including_boundaries(level, shape):
    image = np.full(shape, level, dtype=np.uint8)
    actual = bilateral_filter(image)
    assert np.array_equal(actual, image)
    assert actual.dtype == np.uint8
    assert not np.shares_memory(actual, image)


@pytest.mark.parametrize("parameters", [(3, 1.0, 3.0), (3, 1.0, 10.0), (5, 2.0, 20.0), (7, 2.0, 30.0)])
@pytest.mark.parametrize("shape", [(1, 6), (6, 1), (2, 3), (8, 9)])
def test_matches_scalar_reference_at_corners_edges_and_interior(parameters, shape):
    image = np.random.default_rng(35).integers(0, 256, shape, dtype=np.uint8)
    before = image.copy()
    actual = bilateral_filter(image, *parameters)
    assert np.array_equal(actual, scalar_reference(image, *parameters))
    assert np.array_equal(image, before)
    assert actual.shape == image.shape
    assert actual.dtype == np.uint8
    assert 0 <= int(actual.min()) <= int(actual.max()) <= 255


def test_two_pixel_boundary_has_only_valid_neighbors_and_no_uint8_wraparound():
    image = np.array([[0, 20]], dtype=np.uint8)
    weight = math.exp(-1 / 8) * math.exp(-400 / 800)
    left = math.floor(20 * weight / (1 + weight) + 0.5)
    assert bilateral_filter(image, 5, 2, 20).tolist() == [[left, 20 - left]]
    # A large intensity jump gets negligible range weight in both directions.
    assert bilateral_filter(np.array([[0, 255]], dtype=np.uint8)).tolist() == [[0, 255]]


def test_noise_reduction_preserves_high_contrast_edge_and_thin_line():
    rng = np.random.default_rng(19)
    clean = np.full((30, 40), 40.0)
    clean[:, 20:] = 200
    noisy = np.clip(np.floor(clean + rng.normal(0, 5, clean.shape) + 0.5), 0, 255).astype(np.uint8)
    filtered = bilateral_filter(noisy)
    assert np.mean((filtered.astype(float) - clean)**2) < np.mean((noisy.astype(float) - clean)**2)
    assert np.all(filtered[:, 19] < 65)
    assert np.all(filtered[:, 20] > 175)
    line = np.full((9, 9), 20, dtype=np.uint8)
    line[:, 4] = 230
    assert np.array_equal(bilateral_filter(line), line)


def test_identity_window_and_pipeline_order():
    image = np.array([[10, 15, 21], [14, 22, 31]], dtype=np.uint8)
    assert np.array_equal(bilateral_filter(image, 1), image)
    expected = contrast_stretch(gamma_transform(bilateral_filter(image), 0.5), 0, 100, 220)
    actual = combined_enhancement(image, 0.5, 0, 100, 220)
    assert np.array_equal(actual, expected)
    old = contrast_stretch(gamma_transform(image, 0.5), 0, 100, 220)
    assert not np.array_equal(actual, old)


@pytest.mark.parametrize("parameters", [
    {"window_size": 0}, {"window_size": 2}, {"window_size": -3},
    {"window_size": 3.0}, {"window_size": True},
    {"sigma_spatial": 0}, {"sigma_spatial": -1}, {"sigma_spatial": float("inf")},
    {"sigma_spatial": float("nan")}, {"sigma_range": 0}, {"sigma_range": -1},
    {"sigma_range": float("inf")}, {"sigma_range": float("nan")},
])
def test_invalid_parameters(parameters):
    with pytest.raises(ValueError):
        bilateral_filter(np.zeros((3, 3), dtype=np.uint8), **parameters)


@pytest.mark.parametrize("image", [
    [[0]], np.zeros((0, 3), dtype=np.uint8), np.zeros((3, 0), dtype=np.uint8),
    np.zeros((2, 2, 3), dtype=np.uint8), np.zeros((2, 2), dtype=float),
])
def test_invalid_images(image):
    with pytest.raises(ValueError):
        bilateral_filter(image)
