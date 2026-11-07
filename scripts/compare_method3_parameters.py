"""Generate visual parameter trials without changing the selected GUI outputs.

Run with: uv run python scripts/compare_method3_parameters.py
Each sheet retains native 600x400 panels; no numerical score selects a winner.
"""

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from spatial_image_enhancement.algorithms import combined_enhancement
from spatial_image_enhancement.cli import COMBINED_OUTPUT_MAX, GAMMAS, HIGH_PERCENTILE, LOW_PERCENTILE, NAMES

ROOT = Path(__file__).resolve().parents[1]
TRIALS = (
    ("5x5_s2_r20", 5, 2.0, 20.0),
    ("5x5_s1_r5", 5, 1.0, 5.0),
    ("5x5_s1_r3", 5, 1.0, 3.0),
    ("3x3_s1_r3", 3, 1.0, 3.0),
)


def main():
    output = ROOT / "outputs/method3_parameter_trials"
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=20)
    for name in NAMES:
        with Image.open(ROOT / "HW1_test_image" / name) as source:
            original = np.asarray(source).copy()
        with Image.open(ROOT / "outputs/baseline_method3/combined" / name) as source:
            previous = np.asarray(source).copy()
        panels = [("Original", original), ("Previous Method 3", previous)]
        for label, size, spatial, intensity in TRIALS:
            result = combined_enhancement(original, GAMMAS[name], LOW_PERCENTILE, HIGH_PERCENTILE,
                                          COMBINED_OUTPUT_MAX[name], window_size=size,
                                          sigma_spatial=spatial, sigma_range=intensity)
            folder = output / label
            folder.mkdir(exist_ok=True)
            Image.fromarray(result).save(folder / name)
            panels.append((f"{size}x{size}, spatial={spatial:g}, range={intensity:g}", result))
        canvas = Image.new("RGB", (1800, 900), "white")
        draw = ImageDraw.Draw(canvas)
        for index, (label, result) in enumerate(panels):
            x, y = (index % 3) * 600, (index // 3) * 450
            draw.text((x + 12, y + 12), label, fill="black", font=font)
            canvas.paste(Image.fromarray(result).convert("RGB"), (x, y + 50))
        canvas.save(output / f"{Path(name).stem}_parameter_comparison.png")
        print(f"Compared {name}")
    (output / "parameters.json").write_text(json.dumps({
        label: {"window_size": size, "sigma_spatial": spatial, "sigma_range": intensity}
        for label, size, spatial, intensity in TRIALS
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
