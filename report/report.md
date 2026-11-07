# Spatial Image Enhancement

**Image Processing Homework 1**  
Student name: [Placeholder]  
Student ID: [Placeholder]  
Due date: November 11, 2026  
Submission date: [Placeholder]

## Technical Description

### Objectives and input

This homework enhances six dark, 600 × 400, 8-bit grayscale PNG images. It compares gamma correction (Method 1), global histogram equalization (Method 2), and bilateral filtering followed by gamma correction and contrast stretching (Method 3). The final Method 3 was approved after visual review of all six images. Each result remains a 600 × 400 mode-L PNG. The images are 1-1.png through 1-6.png. The code also saves original copies, gamma trials, original/equalized histograms, comparison figures, the previous Method 3 baseline, and a JSON measurement record.

### Mathematical background and algorithms

Let r be an integer input intensity in [0,255], let N = 240,000 pixels, and let round(x) mean floor(x + 0.5) for nonnegative x. Gamma, equalization, and stretch mappings use explicitly calculated lookup tables and pixel loops. The bilateral filter explicitly loops over neighborhood offsets, processing overlapping pixel arrays with NumPy. Outputs are clamped to [0,255].

**Gamma transformation.** For gamma greater than zero, s = round[255 (r/255)^gamma]. A gamma below 1 expands dark intensities. The implementation builds a 256-entry lookup table with the equation and assigns the mapped value to every pixel. Values 0.3, 0.5, and 0.7 were saved for every image before selecting one value per scene.

**Histogram equalization.** The implementation counts h(k) = number of pixels with intensity k, for k = 0,...,255. It calculates p(k) = h(k)/N and C(k) = sum from j=0 to k of p(j). It uses the CDF-min-adjusted mapping s(k) = round[255 (C(k) - C_min)/(1 - C_min)], where C_min is the first nonzero CDF value. The mapping is clamped to [0,255]. If all pixels have one intensity, the output is an unchanged copy, avoiding division by zero. This is global equalization, so distinct input levels can map to the same output level; the resulting histogram is not necessarily flat.

**Manual bilateral filtering.** For a center pixel p and each valid neighbor q within its 3 x 3 window, the spatial weight is ws(p,q) = exp[-((qx-px)^2 + (qy-py)^2)/(2 sigma_spatial^2)] and the range weight is wr(p,q) = exp[-(I(q)-I(p))^2/(2 sigma_range^2)]. The filtered intensity is B(p) = round[sum_q ws(p,q) wr(p,q) I(q) / sum_q ws(p,q) wr(p,q)]. The approved parameters are sigma_spatial = 1 pixel and sigma_range = 3 on the original 0-255 intensity scale. The implementation computes both weights, weighted sums, and normalization manually; it does not call any ready-made bilateral filter. Neighborhoods are clipped at image boundaries and their remaining weights are normalized. Float64 subtraction prevents unsigned 8-bit wraparound. The center always has weight 1, so the denominator is positive. Clipping and round-half-up conversion produce a new uint8 grayscale image without modifying the original.

**Combined enhancement (Method 3).** The approved order is Original -> Bilateral Filtering -> Gamma Correction -> Contrast Stretching. The existing gamma function processes B, followed by the existing percentile stretch function. The lower endpoint L is the first intensity whose cumulative count reaches 1% of pixels in this filtered gamma image; the upper endpoint H reaches 99.5%. The mapping is s = clamp(round[M (r-L)/(H-L)], 0, M). The output ceiling M remains 255 except for image 1-4, where it remains 220 to retain sky gradation. If H <= L, stretching returns its input unchanged. Percentile endpoints limit outlier influence but intentionally clip values outside the selected interval. Methods 1 and 2 process the untouched original independently and are unchanged. No additional enhancement technique is introduced.

### Implementation and execution flow

1. Parse the input directory, output directory, and optional per-image gamma JSON file. Check that all six files exist and are 600 × 400 mode-L images before writing output.
2. Read each image and count intensities with explicit nested pixel loops. Create trial gamma outputs for 0.3, 0.5, and 0.7.
3. Apply selected gamma and CDF-min equalization to the original for Methods 1 and 2. For Method 3, manually bilateral-filter the original, then reuse the existing gamma and percentile-stretch implementations.
4. Preserve previous Gamma + Contrast Stretching results before replacement. Save PNGs, paired histograms, four-panel method comparisons, native-resolution Original / Previous Method 3 / Updated Method 3 comparisons, and measured values in results.json. Existing baselines are never overwritten.
5. Run automated tests and bundle the GUI/CLI with PyInstaller for Windows execution. The GUI's fourth panel displays the approved Method 3; temporary background regeneration preserves saved results.

The histograms use the same x range of 0–255 and the same y maximum within each original/equalized pair. Every comparison panel uses vmin=0 and vmax=255, so display scaling cannot make one method appear brighter by changing the plotting limits.

### External library calls and their limited roles

| Library calls | Role | Why the homework algorithm remains manual |
|---|---|---|
| NumPy `asarray`, `astype`, `zeros`, slicing, `exp`, `clip`, `floor`, `array_equal` | Store arrays; evaluate explicit range Gaussians and weighted sums; round, clamp, and verify results | Neighborhood offsets, spatial weights, range weights, and normalization are written in the project; no bilateral, enhancement, histogram, or CDF API is called. |
| Pillow `Image.open`, `Image.fromarray`, `Image.save`, `ImageDraw`, `ImageFont` | Decode/encode PNGs and assemble labeled native-resolution comparisons | They do not calculate enhancement mappings or filtering. |
| Matplotlib `use`, `subplots`, `bar`, `imshow`, `savefig`, `close` | Draw histograms and fixed-scale comparison figures | Histogram counts are supplied by the manual counting loop. |
| pytest `raises`, `approx`, parameterization | Execute numerical, boundary, pipeline, saved-image regression, and GUI assertions | An independent scalar bilateral reference and frozen image hashes check the implementation. |
| PyInstaller command | Bundle Python, dependencies, inputs, and outputs into a Windows GUI executable | It packages the GUI and CLI without changing the algorithms. |
| reportlab classes and `build` | Render this editable report source as a PDF | It is used only for report layout. |

### Parameter selection

Visual inspection of all 18 gamma trial images guided the choices below. Gamma 0.3 revealed more structure in the very dark bookshelf, laundry, and shelf scenes (1-2, 1-5, 1-6). Gamma 0.5 retained more tonal separation in 1-1, 1-3, and 1-4; 0.3 made some bright surfaces look flat. Gamma 0.7 was generally too dark for these inputs. The combined stretch uses the same percentiles on all images. Its output ceiling changes only for 1-4 because a 255 ceiling made the sky too pale in the visual comparison.

For bilateral filtering, evaluation started with the requested 5 x 5 window, spatial sigma 2, and range sigma 20. This visibly softened book lettering, building windows, and appliance controls because the original images occupy narrow, dark intensity ranges. Weaker alternatives were compared on all six inputs: 5 x 5 / 1 / 5, 5 x 5 / 1 / 3, and 3 x 3 / 1 / 3 (window / spatial sigma / range sigma). The final 3 x 3 / 1 / 3 setting reduces visible grain while retaining more fine detail than the starting setting. The image owner inspected and approved this version. Numerical metrics did not select the filter parameters. Residual noise and shadow quantization remain; stronger smoothing was not assumed to be better.

| Image | Selected gamma | L to H after bilateral + gamma | Combined ceiling M |
|---|---:|---:|---:|
| 1-1 | 0.5 | 0 to 116 | 255 |
| 1-2 | 0.3 | 48 to 161 | 255 |
| 1-3 | 0.5 | 36 to 194 | 255 |
| 1-4 | 0.5 | 28 to 105 | 220 |
| 1-5 | 0.3 | 48 to 152 | 255 |
| 1-6 | 0.3 | 48 to 146 | 255 |

## Experimental Results

The mean and population standard deviation below describe intensity distributions, not perceived quality. They are calculated from manual histogram counts. The Method 3 columns reflect the approved saved outputs in outputs/results.json; the Original, Gamma, and Equalized results are unchanged. The percent at zero or 255 exposes clipping; the figures provide the visual check.

| Image | Original mean / SD | Gamma mean / SD | Equalized mean / SD | Combined mean / SD | Combined at 0 / 255 |
|---|---:|---:|---:|---:|---:|
| 1-1 | 19.36 / 12.96 | 64.41 / 27.97 | 129.13 / 75.00 | 141.97 / 60.46 | 1.170% / 0.502% |
| 1-2 | 20.31 / 14.06 | 111.71 / 29.06 | 129.65 / 73.29 | 144.61 / 62.51 | 2.536% / 0.500% |
| 1-3 | 52.34 / 34.41 | 107.95 / 41.17 | 129.29 / 72.93 | 116.15 / 66.35 | 4.855% / 0.840% |
| 1-4 | 28.48 / 13.02 | 81.93 / 23.09 | 132.04 / 76.00 | 154.27 / 64.94 | 1.862% / 0% |
| 1-5 | 12.69 / 8.80 | 98.06 / 22.94 | 132.10 / 73.07 | 123.59 / 52.00 | 2.583% / 0.550% |
| 1-6 | 18.92 / 10.45 | 111.65 / 23.97 | 130.56 / 73.67 | 166.44 / 59.91 | 1.441% / 0.587% |

### Image 1-1

The plush figure and folded cloth become visible with gamma. Equalization reveals more wall texture but also a grainier background. Bilateral filtering before gamma and stretching reduces wall grain while retaining the figure's outlines and cloth boundaries. The weaker approved setting avoids the larger starting filter's visible softening.

![Four-panel comparison for 1-1](../outputs/comparisons/1-1_comparison.png)

![Original and equalized histograms for 1-1](../outputs/histograms/1-1_histograms.png)

### Image 1-2

Gamma 0.3 lifts dark book spines. Equalization raises grain around the shelf. The approved Method 3 reduces grain while keeping more lettering and wire detail than the 5 x 5 / 2 / 20 trial. It clips 2.536% to black; small lettering remains a useful check against excessive smoothing.

![Four-panel comparison for 1-2](../outputs/comparisons/1-2_comparison.png)

![Original and equalized histograms for 1-2](../outputs/histograms/1-2_histograms.png)

### Image 1-3

The original already has a wider range than the other inputs. Gamma 0.5 keeps the white figure controlled. Equalization brightens the wall and white figure strongly. The approved bilateral setting makes a restrained change rather than forcing heavy smoothing. Method 3 leaves 4.855% at black, so the darkest details can still be lost during stretching.

![Four-panel comparison for 1-3](../outputs/comparisons/1-3_comparison.png)

![Original and equalized histograms for 1-3](../outputs/histograms/1-3_histograms.png)

### Image 1-4

The skyline becomes clearer with all methods. Equalization visibly amplifies sky noise. Bilateral filtering reduces grain before expansion, while the approved small window retains more building windows and roof detail than the starting trial. The unchanged output ceiling of 220 limits sky brightness; shadow clipping remains 1.862%.

![Four-panel comparison for 1-4](../outputs/comparisons/1-4_comparison.png)

![Original and equalized histograms for 1-4](../outputs/histograms/1-4_histograms.png)

### Image 1-5

Gamma 0.3 reveals the washing machines. Equalization raises floor and wall noise substantially. The approved Method 3 reduces grain on these surfaces while retaining more appliance controls and drum detail than the starting trial. Dark-region clipping remains, with 2.583% at zero.

![Four-panel comparison for 1-5](../outputs/comparisons/1-5_comparison.png)

![Original and equalized histograms for 1-5](../outputs/histograms/1-5_histograms.png)

### Image 1-6

Gamma 0.3 makes shelf contents visible while retaining modest contrast. Equalization produces a harsher, noisier appearance. The approved Method 3 reduces grain while retaining shelf edges and small objects more clearly than the starting bilateral setting. Highlights, shadow quantization, and residual noise remain visible limitations.

![Four-panel comparison for 1-6](../outputs/comparisons/1-6_comparison.png)

![Original and equalized histograms for 1-6](../outputs/histograms/1-6_histograms.png)

## Discussions

Gamma correction is monotone and controllable. It lifts dark intensities without forcing the image to use the full 0–255 range, but it may leave a narrow histogram and low contrast. Histogram equalization derives its mapping from the image distribution and usually spreads intensities more widely; in these images it can over-emphasize noise, flatten some surfaces, and change the balance between shadow and highlight detail. A larger mean is not evidence of better quality: 1-4's uncapped combined trial was brighter but visibly lost sky gradation.

Method 3 now reduces noise before the existing gamma and stretching operations expand dark intensity differences. Spatial weights favor nearby pixels, while range weights reduce averaging across intensity edges. This preserves high-contrast edges better than unrestricted spatial averaging, but it cannot guarantee preservation of every low-contrast texture. The 3 x 3 window and small range sigma were approved through visual review of all six scenes. The 1st and 99.5th percentiles still clip intensities: image 1-3 has 4.855% pixels at zero. Image 1-4's ceiling of 220 sacrifices some dynamic range to retain sky gradation. Quantization and residual grain remain, particularly in the darkest regions.

Automated verification covers the original gamma/equalization checks plus bilateral constant images, corners and edges, single-row/column inputs, dimensions, uint8 ranges, invalid parameters, an independent scalar reference, high-contrast edge retention, pipeline order, immutable baselines, and frozen user-approved Method 3 pixel hashes. GUI tests cover all six images, navigation, resizing, missing-file handling, and background regeneration. The finalized suite reports **105 passed**. Methods 1 and 2 match their pre-change pixel hashes, all original input files remain byte-identical, and all six Method 3 outputs match the approved images. The manual filter and its selected parameters are unchanged during finalization.

The one-file Windows GUI executable bundles the same saved inputs/results and supports CLI processing. It was rebuilt from SpatialEnhancement.spec and checked by running the CLI from an external temporary working directory; regenerated outputs match the source pixels. Desktop screenshot access to the Python GUI was denied by the computer-use permission system, so GUI appearance was checked through integration tests and the saved result figures rather than an automated screenshot. A Python-free Windows machine was not available for a separate installation test.

## References and Appendix

1. Course slide deck, `Ch00.pdf`, page 11, "Homeworks" (required report sections).
2. OpenCV documentation, "Histogram Equalization," https://docs.opencv.org/4.x/d5/daf/tutorial_py_histogram_equalization.html (theory only; its enhancement functions are not used).
3. OpenCV documentation, "Intensity Transform," https://docs.opencv.org/4.3.0/dc/dfe/group__intensity__transform.html (power-law terminology only).
4. Astral, "Running commands," https://docs.astral.sh/uv/concepts/projects/run/.
5. PyInstaller, "Using PyInstaller," https://www.pyinstaller.org/en/stable/usage.html.

### Reproduction

From the repository root on Windows 11 with uv and Python 3.12 available: run `uv sync --python 3.12`, then `uv run python -m pytest -q`, then `uv run python -m spatial_image_enhancement --input HW1_test_image --output outputs`. Launch the GUI with `uv run python run_homework.py` or double-click dist/SpatialEnhancement.exe after building. Rebuild with `uv run pyinstaller --noconfirm --clean SpatialEnhancement.spec` to retain bundled data and the windowed entry point. From another directory, use `SpatialEnhancement.exe --input <image-folder> --output <result-folder>` with absolute paths as appropriate. Refresh this PDF with `uv run python report/build_report.py`. README.md also documents the working installed-interpreter fallback when Application Control blocks the virtual-environment launcher.

The project uses Python 3.12, NumPy, Pillow, Matplotlib, pytest, PyInstaller, and reportlab. It does not use a ready-made bilateral, enhancement, or histogram equalization API. outputs/results.json contains the complete measured values. Previous Method 3 images, comparison figures, and metadata are preserved in outputs/baseline_method3/. The six native-resolution Original / Previous Method 3 / Approved Method 3 sheets are outputs/method3_comparisons/1-1_original_old_new.png through 1-6_original_old_new.png. outputs/method3_approved_manifest.json records the approved pixel hashes and parameters. The optional scripts/compare_method3_parameters.py reproduces tuning sheets without changing the selected outputs. The original six PNG files remain byte-for-byte unchanged in HW1_test_image.
