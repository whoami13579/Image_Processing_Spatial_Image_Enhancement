# Spatial Image Enhancement

Image Processing Homework 1. The project manually implements gamma correction, CDF-min histogram equalization, and bilateral filtering followed by gamma correction and percentile contrast stretching for six 600 × 400 grayscale PNGs. Method 3 has been approved after visual review of all six images, and the homework report and PDF describe the approved implementation and results.

## Requirements

- Windows 11
- [uv](https://docs.astral.sh/uv/) with Python 3.12 managed through uv
- VS Code is recommended for editing; select the project `.venv` interpreter after `uv sync`

The locally rebuilt `dist/SpatialEnhancement.exe` opens a Tkinter viewer when double-clicked and bundles the saved outputs and inputs, so it requires no separate Python installation. Executables and build intermediates are ignored by Git; build from the tracked spec after cloning. The standard source workflow uses uv. Previously generated submission packages are not automatically updated by rebuilding.

## Setup and run

Open a PowerShell terminal in this folder:

```powershell
uv sync --python 3.12
uv run python -m pytest -q
uv run python -m spatial_image_enhancement --input HW1_test_image --output outputs
```

The program checks all six files before processing and reports missing or incorrectly formatted inputs. If Application Control blocks the virtual-environment Python launcher, use the installed-interpreter fallback below. The finalized test suite contains 105 passing tests.

### Desktop viewer

Double-click `dist/SpatialEnhancement.exe`, or run the viewer from source:

```powershell
uv run python run_homework.py
```

If Windows Application Control blocks the project's virtual-environment Python launcher, the installed Python 3.12 interpreter worked on this machine with the existing project packages. From the repository folder:

```powershell
$env:PYTHONPATH = "$PWD\src;$PWD\.venv\Lib\site-packages"
$projectPython = "$env:APPDATA\uv\python\cpython-3.12-windows-x86_64-none\python.exe"
& $projectPython run_homework.py
# The same interpreter can run tests, regenerate outputs, or rebuild:
# & $projectPython -m pytest -q
# & $projectPython -m spatial_image_enhancement --input HW1_test_image --output outputs
# & $projectPython -m PyInstaller --noconfirm --clean SpatialEnhancement.spec
```

The viewer shows Original, Gamma Correction, Histogram Equalization, and Bilateral Filtering + Gamma + Contrast Stretching (Method 3) side by side, with the saved original/equalized histogram figure below. Select any of the six filenames, use Previous/Next, or press Left/Right. Images resize with the window while preserving aspect ratio; resizing affects only the preview.

`Regenerate preview` runs the updated processing pipeline in a background thread and displays temporary results. It never overwrites `outputs/`, numerical results, or the report. Temporary previews are discarded on exit. Missing or unreadable images are reported in the status line.

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

Method 3 comparison and verification artifacts:

- `outputs/baseline_method3/combined/1-1.png` through `1-6.png`: the preserved previous Gamma + Contrast Stretching images. The previous four-panel figures and `results.json` are also preserved in this baseline directory. Existing baselines are never overwritten by regeneration.
- `outputs/method3_comparisons/1-1_original_old_new.png` through `1-6_original_old_new.png`: Original | Previous Method 3 | Updated Method 3, with each 600 × 400 image pasted at native resolution beneath its label. Open at 100% zoom to inspect detail.
- `outputs/method3_parameter_trials/1-1_parameter_comparison.png` through `1-6_parameter_comparison.png`: optional local comparisons of the starting 5×5/2/20 setting and weaker 5×5/1/5, 5×5/1/3, and 3×3/1/3 alternatives. These tuning outputs are ignored by Git; reproduce them with `uv run python scripts/compare_method3_parameters.py`. This command does not change the selected outputs.
- `outputs/baseline_method3/verification_manifest.json`: pre-change file and decoded-pixel SHA-256 hashes used by regression tests.
- `outputs/method3_approved_manifest.json`: frozen approved Method 3 pixel hashes, bilateral parameters, gamma values, and stretch settings used by regression tests.

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
- Method 3: original → manual bilateral filtering → existing selected gamma → existing manual linear stretch between the 1st and 99.5th percentile intensity of the filtered gamma output. The output ceiling remains 220 for 1-4 and 255 for the other five images.
- Bilateral filtering explicitly computes `exp(-(dx²+dy²)/(2σspatial²)) * exp(-(neighbor-center)²/(2σrange²))`, accumulates weighted intensities and weights, and divides by the weight sum. Only valid neighbors are used at boundaries, with local normalization. Float64 arithmetic avoids 8-bit subtraction overflow; round-half-up conversion returns a new uint8 grayscale array.
- Approved settings for all six images: 3×3, spatial sigma 1 pixel, range sigma 3 on the original 0–255 scale. The requested starting 5×5/2/20 setting visibly softened lettering, building windows, and appliance controls in these dark inputs. All six trial sheets were visually inspected before choosing the weaker setting; no numerical score selected it. The image owner reviewed and approved this version. Some grain and shadow quantization remain. Finalization changes documentation and approval metadata without changing the filter, parameters, or approved image pixels.

`src/spatial_image_enhancement/algorithms.py` contains the explicit calculations. The bilateral filter loops over neighborhood offsets and uses NumPy to process overlapping pixel arrays; the existing gamma and stretch functions are reused without changes. Pillow reads/writes PNGs and assembles the native-resolution review panels, and Matplotlib draws the existing figures. No ready-made bilateral or image enhancement API is used. The report includes the manual weight equations, approved parameter selection, actual post-filter stretch endpoints, and updated measurements and figures.

## Verification and limitations

Final Method 3 verification: all 17 pre-change tests passed before implementation; the finalized suite reports **105 passed**, covering constants, clipped boundaries, single-row/column images, scalar-reference agreement, dimensions, uint8 ranges, invalid inputs/parameters, edge preservation, pipeline order, GUI navigation/resizing/background regeneration, baseline preservation, and frozen approved pixel hashes and parameters. All six Method 3 images and native-resolution comparison panels were verified. Methods 1 and 2 match the pre-change decoded-pixel hashes for every input. All nine existing gamma, histogram, and stretch helper function bodies remain unchanged from the pre-bilateral implementation. The six input files, saved Method 1/2 PNGs, gamma trials, and previous Method 3 baseline remain byte-identical. The approved manual filter, enhancement settings, and all approved result/comparison PNGs are unchanged during finalization. The report and PDF have been updated to reflect this version.

The rebuilt `dist/SpatialEnhancement.exe` has Windows GUI subsystem 2 and bundles the saved inputs/outputs. Its CLI ran successfully from an external temporary working directory, generated all six images, and matched the source pixels for gamma, equalization, approved Method 3, previous Method 3, and the three-panel comparisons. The old local executable is retained at `dist/baseline_method3/SpatialEnhancement.exe`. Desktop screenshot access to the Python GUI was denied by the computer-use permission system; the Tkinter integration checks passed. No security settings were changed. Existing ignored submission folders/archives are not refreshed automatically; use the packaging script only when preparing a new submission.

The executable has not been tested on a separate Python-free Windows installation.

Before final submission, replace the name, student ID, and submission-date placeholders in `report/report.md`, regenerate the PDF, and, if needed, rename the outer submission folder to the required student ID.
