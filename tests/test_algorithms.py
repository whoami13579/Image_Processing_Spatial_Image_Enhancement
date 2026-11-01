import numpy as np
import pytest
from PIL import Image

from spatial_image_enhancement.algorithms import (
    combined_enhancement, contrast_stretch, gamma_transform,
    histogram_counts, histogram_equalize, histogram_model,
)


def test_gamma_known_values_and_identity():
    image = np.array([[0, 64, 128, 255]], dtype=np.uint8)
    assert gamma_transform(image, 1).tolist() == image.tolist()
    assert gamma_transform(image, 0.5).tolist() == [[0, 128, 181, 255]]
    with pytest.raises(ValueError):
        gamma_transform(image, 0)


def test_histogram_pmf_and_cdf():
    image = np.array([[0, 0], [1, 2]], dtype=np.uint8)
    counts, pmf, cdf = histogram_model(image)
    assert counts == histogram_counts(image)
    assert counts[:4] == [2, 1, 1, 0]
    assert sum(counts) == 4
    assert pmf[:3] == [0.5, 0.25, 0.25]
    assert sum(pmf) == pytest.approx(1)
    assert cdf[:3] == [0.5, 0.75, 1.0]
    assert all(left <= right for left, right in zip(cdf, cdf[1:]))
    assert cdf[-1] == pytest.approx(1)


def test_cdf_min_equalization_mapping():
    image = np.array([[0, 0], [1, 2]], dtype=np.uint8)
    assert histogram_equalize(image).tolist() == [[0, 0], [128, 255]]


@pytest.mark.parametrize("level", [0, 85, 255])
def test_constant_images_preserve_tone(level):
    image = np.full((3, 5), level, dtype=np.uint8)
    assert np.array_equal(histogram_equalize(image), image)
    assert np.array_equal(contrast_stretch(image), image)
    assert np.array_equal(combined_enhancement(image, 1), image)


def test_combined_order_and_contrast():
    image = np.array([[0, 32, 64, 96, 128, 255]], dtype=np.uint8)
    gamma = gamma_transform(image, 0.5)
    expected = contrast_stretch(gamma, 0, 100)
    actual = combined_enhancement(image, 0.5, 0, 100)
    assert np.array_equal(actual, expected)
    assert actual[0, 1] > image[0, 1]
    assert np.all(actual[0, :-1] <= actual[0, 1:])
    limited = combined_enhancement(image, 0.5, 0, 100, 220)
    assert int(limited.max()) == 220


@pytest.mark.parametrize("operation", [
    lambda a: gamma_transform(a, 0.3), histogram_equalize,
    lambda a: combined_enhancement(a, 0.7),
])
def test_shape_bounds_and_grayscale_png_round_trip(tmp_path, operation):
    image = np.array([[0, 1, 3], [120, 240, 255]], dtype=np.uint8)
    result = operation(image)
    assert result.shape == image.shape
    assert result.dtype == np.uint8
    assert 0 <= int(result.min()) <= int(result.max()) <= 255
    path = tmp_path / "result.png"
    Image.fromarray(result, mode="L").save(path)
    with Image.open(path) as reopened:
        assert reopened.mode == "L"
        assert reopened.size == (3, 2)
        assert np.array_equal(np.asarray(reopened), result)


def test_invalid_input_and_percentiles():
    with pytest.raises(ValueError):
        histogram_equalize(np.zeros((2, 2, 3), dtype=np.uint8))
    with pytest.raises(ValueError):
        contrast_stretch(np.zeros((2, 2), dtype=np.uint8), 50, 50)
