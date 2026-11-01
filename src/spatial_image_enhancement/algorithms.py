"""Manual enhancement equations. NumPy only stores arrays; it does not enhance them."""

import math

import numpy as np


def _check_image(image: np.ndarray) -> None:
    if not isinstance(image, np.ndarray) or image.ndim != 2 or image.dtype != np.uint8:
        raise ValueError("Expected a 2-D uint8 grayscale image")


def _apply_table(image: np.ndarray, table: list[int]) -> np.ndarray:
    result = np.empty(image.shape, dtype=np.uint8)
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            result[y, x] = table[int(image[y, x])]
    return result


def gamma_transform(image: np.ndarray, gamma: float) -> np.ndarray:
    """Apply round-half-up(255 * (r/255)**gamma) through an explicit LUT."""
    _check_image(image)
    if not math.isfinite(gamma) or gamma <= 0:
        raise ValueError("gamma must be finite and greater than zero")
    table = []
    for r in range(256):
        value = math.floor(255.0 * (r / 255.0) ** gamma + 0.5)
        table.append(min(255, max(0, value)))
    return _apply_table(image, table)


def histogram_counts(image: np.ndarray) -> list[int]:
    _check_image(image)
    counts = [0] * 256
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            counts[int(image[y, x])] += 1
    return counts


def histogram_model(image: np.ndarray) -> tuple[list[int], list[float], list[float]]:
    """Return counts, PMF and inclusive CDF for intensities 0..255."""
    counts = histogram_counts(image)
    total = image.size
    if total == 0:
        raise ValueError("image must contain pixels")
    pmf = [count / total for count in counts]
    cdf = []
    running = 0.0
    for probability in pmf:
        running += probability
        cdf.append(running)
    return counts, pmf, cdf


def histogram_equalize(image: np.ndarray) -> np.ndarray:
    """CDF-min mapping; a single-level image retains its original tone."""
    _check_image(image)
    counts, _, cdf = histogram_model(image)
    first = next(i for i, count in enumerate(counts) if count)
    if counts[first] == image.size:
        return image.copy()
    cdf_min = cdf[first]
    table = []
    for r in range(256):
        mapped = 255.0 * (cdf[r] - cdf_min) / (1.0 - cdf_min)
        table.append(min(255, max(0, math.floor(mapped + 0.5))))
    return _apply_table(image, table)


def _percentile_level(counts: list[int], total: int, percentile: float) -> int:
    target = max(1, math.ceil(total * percentile / 100.0))
    cumulative = 0
    for level, count in enumerate(counts):
        cumulative += count
        if cumulative >= target:
            return level
    return 255


def contrast_stretch(
    image: np.ndarray, low_percentile: float = 1.0, high_percentile: float = 99.5,
    output_max: int = 255,
) -> np.ndarray:
    """Clip percentile endpoints, then linearly map [low, high] to [0, output_max]."""
    _check_image(image)
    if not (0 <= low_percentile < high_percentile <= 100):
        raise ValueError("Require 0 <= low_percentile < high_percentile <= 100")
    if not isinstance(output_max, int) or not 1 <= output_max <= 255:
        raise ValueError("output_max must be an integer in 1..255")
    counts = histogram_counts(image)
    low = _percentile_level(counts, image.size, low_percentile)
    high = _percentile_level(counts, image.size, high_percentile)
    if high <= low:
        return image.copy()
    table = []
    for r in range(256):
        value = math.floor(output_max * (r - low) / (high - low) + 0.5)
        table.append(min(output_max, max(0, value)))
    return _apply_table(image, table)


def combined_enhancement(
    image: np.ndarray, gamma: float, low_percentile: float = 1.0,
    high_percentile: float = 99.5, output_max: int = 255,
) -> np.ndarray:
    """Power-law transformation followed by percentile contrast stretching."""
    return contrast_stretch(gamma_transform(image, gamma), low_percentile, high_percentile, output_max)


def stretch_endpoints(
    image: np.ndarray, low_percentile: float, high_percentile: float
) -> tuple[int, int]:
    """Expose selected endpoints for reproducible experimental reporting."""
    counts = histogram_counts(image)
    return (
        _percentile_level(counts, image.size, low_percentile),
        _percentile_level(counts, image.size, high_percentile),
    )
