# Spatial Image Enhancement

Image Processing Homework 1. The project manually implements gamma correction, CDF-min histogram equalization, and gamma correction followed by percentile contrast stretching for six 600 × 400 grayscale PNGs.

## Requirements

- Windows 11
- [uv](https://docs.astral.sh/uv/) with Python 3.12 managed through uv
- VS Code is recommended for editing; select the project `.venv` interpreter after `uv sync`

The rebuilt `dist/SpatialEnhancement.exe` opens a Tkinter viewer when double-clicked and bundles the saved outputs and inputs, so it requires no separate Python installation. The source workflow uses uv exclusively. Previously generated submission packages are not automatically updated by rebuilding.

## Setup and run

Open a PowerShell terminal in this folder:

```powershell
uv sync --python 3.12
uv run python -m pytest -q
uv run python -m spatial_image_enhancement --input HW1_test_image --output outputs
```

On this Windows machine, the `pytest.exe` launcher was blocked by Application Control; `uv run python -m pytest -q` worked and ran all 11 tests. The program checks all six files before processing and reports missing or incorrectly formatted inputs.

### Desktop viewer

Double-click `dist/SpatialEnhancement.exe`, or run the viewer from source:

```powershell
uv run python run_homework.py
```

The viewer shows Original, Gamma Correction, Histogram Equalization, and Gamma Correction + Contrast Stretching side by side, with the saved original/equalized histogram figure below. Select any of the six filenames, use Previous/Next, or press Left/Right. Images resize with the window while preserving aspect ratio; resizing affects only the preview.

`Regenerate preview` runs the unchanged processing pipeline in a background thread and displays temporary results. It never overwrites `outputs/`, numerical results, or the report. Temporary previews are discarded on exit. Missing or unreadable images are reported in the status line.

Resource lookup is independent of the working directory: the GUI uses directories beside the executable, then the project directories for a development build in `dist/`, then bundled resources. A copied executable can run standalone. Source GUI execution uses the project directories. To select other directories explicitly:

```powershell
uv run python run_homework.py --gui --input C:\data\HW1_test_image --output C:\data\outputs
```

### Command line

The module command and installed `spatial-image-enhancement` command retain their existing behavior. Existing executable processing arguments also select CLI mode; use `--cli` to process with defaults:

```powershell
& .\SpatialEnhancement.exe --input .\HW1_test_image --output .\outputs
```

When executing the CLI from another directory, use absolute `--input` and `--output` paths. `SpatialEnhancement.exe --cli` looks for `HW1_test_image` beside itself and writes `outputs` beside itself. Module CLI execution defaults to the current directory. The windowed executable attaches to an invoking console when available; for reliable console output and redirection, use `uv run python -m spatial_image_enhancement`. To override the per-image selected gamma values, create a JSON object with exactly the six filename keys and supply `--gamma-config path\to\config.json`. Example:

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
uv run pyinstaller --noconfirm --clean SpatialEnhancement.spec
```

The output is `dist/SpatialEnhancement.exe`. The tracked spec bundles inputs/outputs and selects `console=False`. Use the spec when rebuilding to preserve this configuration. PyInstaller's `build/` directory is an intermediate development artifact. To refresh the existing submission folder and ZIP after reviewing the local changes, run `uv run python scripts/build_submission.py`.

## Algorithm notes

- Gamma mapping: `round(255 × (r/255)^gamma)` for each 8-bit intensity.
- Equalization: manual frequency counts, PMF, inclusive CDF, and CDF-min-adjusted lookup mapping. Constant images retain their original intensity.
- Combined method: selected gamma, then a manual linear stretch between the 1st and 99.5th percentile intensity of the gamma output. The output ceiling is 220 for 1-4 and 255 for the other five images.

`src/spatial_image_enhancement/algorithms.py` contains the explicit calculations and nested pixel loops. NumPy stores arrays, Pillow reads and writes PNGs, and Matplotlib draws figures. No ready-made image enhancement API is used. The report documents equations, selection rationale, measurements, and the specific external library calls.

## Verification and limitations

GUI update verification (November 5, 2026): `uv run python -m pytest -q` reports 17 passed, including all 11 original tests. Tkinter integration tests exercise all six images and their paired histogram figures, navigation, resizing, missing-file handling, resource paths, and background regeneration. All 18 regenerated enhanced images are pixel-identical to saved outputs; regenerated `results.json` is byte-identical. All 66 protected baseline files (inputs, outputs, report, algorithm and CLI source) remain byte-identical.

PyInstaller successfully rebuilt the executable with PE subsystem 2 (Windows GUI, no console). Runtime verification of a standalone EXE copied to an external temporary directory was blocked by Windows Application Control (WinError 4551). Automated desktop visual inspection was also denied by the computer-use permission system. Executable runtime and visual inspection therefore remain unverified on this machine; the source GUI integration checks passed. No security settings were changed.

On November 1, 2026, `uv run python -m pytest -q` reported 11 passed. The PyInstaller executable ran from a temporary directory outside the source tree, produced all six comparison and histogram figures, and its 18 enhanced PNGs were pixel identical to the source run. All 18 verified outputs were 600 × 400 mode L. The executable returned a descriptive missing-file message and exit code 1. It was not tested on a separate Python-free Windows installation.

Before final submission, replace the name, student ID, and submission-date placeholders in `report/report.md`, regenerate the PDF, and, if needed, rename the outer submission folder to the required student ID.
