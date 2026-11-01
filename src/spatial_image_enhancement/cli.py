"""Command-line experiment runner and reproducible figure generation."""

import argparse
import json
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .algorithms import (
    combined_enhancement, gamma_transform, histogram_counts,
    histogram_equalize, stretch_endpoints,
)

NAMES = [f"1-{number}.png" for number in range(1, 7)]
# Selected after comparing 0.3, 0.5 and 0.7 on the actual input images.
GAMMAS = {
    "1-1.png": 0.5, "1-2.png": 0.3, "1-3.png": 0.5,
    "1-4.png": 0.5, "1-5.png": 0.3, "1-6.png": 0.3,
}
LOW_PERCENTILE = 1.0
HIGH_PERCENTILE = 99.5
COMBINED_OUTPUT_MAX = {name: (220 if name == "1-4.png" else 255) for name in NAMES}


def _save_gray(array: np.ndarray, path: Path) -> None:
    Image.fromarray(array, mode="L").save(path)


def _histogram_figure(original: np.ndarray, equalized: np.ndarray, path: Path) -> None:
    before = histogram_counts(original)
    after = histogram_counts(equalized)
    ymax = max(max(before), max(after)) * 1.04
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), layout="constrained")
    for ax, counts, title in zip(axes, (before, after), ("Original", "Equalized")):
        ax.bar(range(256), counts, width=1.0, color="#354b6e")
        ax.set(xlim=(-0.5, 255.5), ylim=(0, ymax), ylabel="Pixel count", title=title)
        ax.set_xticks(range(0, 256, 32))
    axes[-1].set_xlabel("Intensity (0–255)")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _comparison_figure(
    original: np.ndarray, gamma: np.ndarray, equalized: np.ndarray,
    combined: np.ndarray, gamma_value: float, path: Path
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 7.5), layout="constrained")
    labels = ("Original", f"Gamma (γ={gamma_value:g})", "Histogram equalization", "Gamma + contrast stretch")
    for ax, array, label in zip(axes.flat, (original, gamma, equalized, combined), labels):
        ax.imshow(array, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
        ax.set_title(label)
        ax.set_xticks([])
        ax.set_yticks([])
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _metrics(array: np.ndarray) -> dict[str, float | int]:
    counts = histogram_counts(array)
    n = array.size
    mean = sum(level * count for level, count in enumerate(counts)) / n
    variance = sum((level - mean) ** 2 * count for level, count in enumerate(counts)) / n
    return {
        "minimum": next(i for i, count in enumerate(counts) if count),
        "maximum": next(i for i in range(255, -1, -1) if counts[i]),
        "mean": round(mean, 3), "std_dev": round(variance ** 0.5, 3),
        "at_zero_percent": round(100 * counts[0] / n, 3),
        "at_255_percent": round(100 * counts[255] / n, 3),
    }


def run(input_dir: Path, output_dir: Path, gammas: dict[str, float]) -> None:
    missing = [name for name in NAMES if not (input_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required input image(s) in {input_dir}: {', '.join(missing)}")
    for name in NAMES:
        with Image.open(input_dir / name) as source:
            if source.mode != "L" or source.size != (600, 400):
                raise ValueError(f"{name}: expected 600 x 400, 8-bit grayscale (L); got {source.size}, {source.mode}")
    for folder in ("original", "gamma", "equalized", "combined", "histograms", "comparisons", "gamma_trials"):
        (output_dir / folder).mkdir(parents=True, exist_ok=True)
    summary = {"method": "CDF-min equalization; gamma then percentile contrast stretch", "images": {}}
    for name in NAMES:
        with Image.open(input_dir / name) as source:
            image = np.asarray(source, dtype=np.uint8).copy()
        gamma_value = gammas[name]
        trial_metrics = {}
        for trial in (0.3, 0.5, 0.7):
            trial_image = gamma_transform(image, trial)
            _save_gray(trial_image, output_dir / "gamma_trials" / f"{Path(name).stem}_gamma_{trial:g}.png")
            trial_metrics[str(trial)] = _metrics(trial_image)
        gamma_image = gamma_transform(image, gamma_value)
        equalized = histogram_equalize(image)
        combined = combined_enhancement(
            image, gamma_value, LOW_PERCENTILE, HIGH_PERCENTILE, COMBINED_OUTPUT_MAX[name]
        )
        shutil.copy2(input_dir / name, output_dir / "original" / name)
        for folder, array in (("gamma", gamma_image), ("equalized", equalized), ("combined", combined)):
            _save_gray(array, output_dir / folder / name)
        stem = Path(name).stem
        _histogram_figure(image, equalized, output_dir / "histograms" / f"{stem}_histograms.png")
        _comparison_figure(image, gamma_image, equalized, combined, gamma_value,
                           output_dir / "comparisons" / f"{stem}_comparison.png")
        endpoints = stretch_endpoints(gamma_image, LOW_PERCENTILE, HIGH_PERCENTILE)
        summary["images"][name] = {
            "gamma": gamma_value, "gamma_trials": trial_metrics,
            "stretch_percentiles": [LOW_PERCENTILE, HIGH_PERCENTILE],
            "stretch_intensities_after_gamma": list(endpoints),
            "combined_output_max": COMBINED_OUTPUT_MAX[name],
            "original": _metrics(image), "gamma_result": _metrics(gamma_image),
            "equalized": _metrics(equalized), "combined": _metrics(combined),
        }
        print(f"Processed {name} (gamma={gamma_value:g}, stretch={endpoints[0]}..{endpoints[1]})")
    (output_dir / "results.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
    parser = argparse.ArgumentParser(description="Enhance six 8-bit grayscale homework images")
    parser.add_argument("--input", type=Path, default=base / "HW1_test_image", help="Directory with 1-1.png through 1-6.png")
    parser.add_argument("--output", type=Path, default=base / "outputs", help="Output directory")
    parser.add_argument("--gamma-config", type=Path, help="JSON object mapping every image filename to gamma")
    args = parser.parse_args(argv)
    try:
        gammas = GAMMAS.copy()
        if args.gamma_config:
            overrides = json.loads(args.gamma_config.read_text(encoding="utf-8"))
            if set(overrides) != set(NAMES):
                raise ValueError("gamma config must contain exactly 1-1.png through 1-6.png")
            gammas = {name: float(overrides[name]) for name in NAMES}
        run(args.input, args.output, gammas)
    except (FileNotFoundError, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0
