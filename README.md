# Spatial Image Enhancement

Image Processing Homework 1. The project manually implements gamma correction, CDF-min histogram equalization, and gamma correction followed by percentile contrast stretching for six 600 × 400 grayscale PNGs.

## Requirements

- Windows 11
- [uv](https://docs.astral.sh/uv/) with Python 3.12 managed through uv
- VS Code is recommended for editing; select the project `.venv` interpreter after `uv sync`

The included `SpatialEnhancement.exe` in the submission folder (or `dist/SpatialEnhancement.exe` in the development project) runs without a separate Python installation. The source workflow uses uv exclusively.

## Setup and run

Open a PowerShell terminal in this folder:

```powershell
uv sync --python 3.12
uv run python -m pytest -q
uv run python -m spatial_image_enhancement --input HW1_test_image --output outputs
```

On this Windows machine, the `pytest.exe` launcher was blocked by Application Control; `uv run python -m pytest -q` worked and ran all 11 tests. The program checks all six files before processing and reports missing or incorrectly formatted inputs.

Use the Windows executable from any current directory:

```powershell
& .\SpatialEnhancement.exe --input .\HW1_test_image --output .\outputs
```

When executing from another directory, use absolute `--input` and `--output` paths. If neither is supplied, the executable looks for `HW1_test_image` beside itself and writes `outputs` beside itself. Source execution defaults to the current directory. To override the per-image selected gamma values, create a JSON object with exactly the six filename keys and supply `--gamma-config path\to\config.json`. Example:

```json
{
  "1-1.png": 0.5,
  "1-2.png": 0.3,
  "1-3.png": 0.5,
  "1-4.png": 0.5,
  "1-5.png": 0.3,
  "1-6.png": 0.3
}
```

## Output layout

`outputs/original/` contains untouched copies of the input images. `gamma/`, `equalized/`, and `combined/` contain the three results for each filename. `gamma_trials/` contains 0.3, 0.5, and 0.7 experiments. `histograms/` contains original/equalized histogram pairs. `comparisons/` contains four-panel figures. `results.json` records parameters and numerical measurements.

All enhanced PNGs are 600 × 400, 8-bit grayscale. The report source is `report/report.md`; its PDF is `report/Spatial_Image_Enhancement_Report.pdf`. Edit the Markdown and regenerate the PDF with:

```powershell
uv run python report/build_report.py
```

The six originals are preserved in `HW1_test_image` and are never edited by the program.

## Rebuild the Windows executable

```powershell
uv run pyinstaller --onefile --name SpatialEnhancement --noconfirm --clean run_homework.py
```

The output is `dist/SpatialEnhancement.exe`. PyInstaller's `build/` directory and `.spec` file are intermediate development artifacts and are excluded from the submission package.

## Algorithm notes

- Gamma mapping: `round(255 × (r/255)^gamma)` for each 8-bit intensity.
- Equalization: manual frequency counts, PMF, inclusive CDF, and CDF-min-adjusted lookup mapping. Constant images retain their original intensity.
- Combined method: selected gamma, then a manual linear stretch between the 1st and 99.5th percentile intensity of the gamma output. The output ceiling is 220 for 1-4 and 255 for the other five images.

`src/spatial_image_enhancement/algorithms.py` contains the explicit calculations and nested pixel loops. NumPy stores arrays, Pillow reads and writes PNGs, and Matplotlib draws figures. No ready-made image enhancement API is used. The report documents equations, selection rationale, measurements, and the specific external library calls.

## Verification and limitations

On November 1, 2026, `uv run python -m pytest -q` reported 11 passed. The PyInstaller executable ran from a temporary directory outside the source tree, produced all six comparison and histogram figures, and its 18 enhanced PNGs were pixel identical to the source run. All 18 verified outputs were 600 × 400 mode L. The executable returned a descriptive missing-file message and exit code 1. It was not tested on a separate Python-free Windows installation.

Before final submission, replace the name, student ID, and submission-date placeholders in `report/report.md`, regenerate the PDF, and, if needed, rename the outer submission folder to the required student ID.
