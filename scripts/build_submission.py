"""Build and verify the homework submission folder and ZIP archive.

Run from the project with: uv run python scripts/build_submission.py

The file list reproduces the existing submission layout. The generated folder
and archive are staged first. Matching existing deliverables are left untouched;
outdated deliverables are replaced only after staging succeeds.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUBMISSION_ROOT = PROJECT_ROOT / "submission"
PACKAGE_NAME = PROJECT_ROOT.name
PACKAGE_DIR = SUBMISSION_ROOT / PACKAGE_NAME
PACKAGE_ZIP = SUBMISSION_ROOT / f"{PACKAGE_NAME}.zip"
IMAGE_NAMES = tuple(f"1-{number}.png" for number in range(1, 7))
OUTPUT_FOLDERS = ("original", "gamma", "equalized", "combined")
GAMMA_TRIALS = ("0.3", "0.5", "0.7")


def required_files() -> list[Path]:
    """Return the project paths that belong in the existing submission layout."""
    paths = [
        Path("pyproject.toml"),
        Path("uv.lock"),
        Path("README.md"),
        Path("run_homework.py"),
        Path("outputs/results.json"),
        Path("report/report.md"),
        Path("report/build_report.py"),
        Path("report/Spatial_Image_Enhancement_Report.pdf"),
    ]
    paths.extend(Path("HW1_test_image") / name for name in IMAGE_NAMES)
    for folder in OUTPUT_FOLDERS:
        paths.extend(Path("outputs") / folder / name for name in IMAGE_NAMES)
    paths.extend(
        Path("outputs/comparisons") / f"1-{number}_comparison.png"
        for number in range(1, 7)
    )
    paths.extend(
        Path("outputs/histograms") / f"1-{number}_histograms.png"
        for number in range(1, 7)
    )
    paths.extend(
        Path("outputs/gamma_trials") / f"1-{number}_gamma_{gamma}.png"
        for number in range(1, 7)
        for gamma in GAMMA_TRIALS
    )
    for folder in (Path("src"), Path("tests")):
        paths.extend(path.relative_to(PROJECT_ROOT) for path in (PROJECT_ROOT / folder).rglob("*.py"))
    return sorted(set(paths), key=lambda path: path.as_posix())


def source_for(relative: Path) -> Path:
    if relative == Path("SpatialEnhancement.exe"):
        return PROJECT_ROOT / "dist" / "SpatialEnhancement.exe"
    return PROJECT_ROOT / relative


def manifest() -> dict[Path, Path]:
    result = {relative: source_for(relative) for relative in required_files()}
    result[Path("SpatialEnhancement.exe")] = source_for(Path("SpatialEnhancement.exe"))
    for relative, source in result.items():
        if not source.is_file():
            raise FileNotFoundError(f"Required submission source is missing: {source}")
        if not source.resolve().is_relative_to(PROJECT_ROOT):
            raise ValueError(f"Source path escapes the project: {source}")
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"Unsafe submission path: {relative}")
    return result


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def folder_files(folder: Path) -> set[Path]:
    if not folder.is_dir():
        return set()
    return {path.relative_to(folder) for path in folder.rglob("*") if path.is_file()}


def matching_folder(folder: Path, staged: Path, expected: set[Path]) -> bool:
    return folder_files(folder) == expected and all(
        sha256(folder / relative) == sha256(staged / relative)
        for relative in expected
    )


def write_archive(source_folder: Path, target: Path, expected: set[Path]) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative in sorted(expected, key=lambda path: path.as_posix()):
            entry = zipfile.ZipInfo(
                f"{PACKAGE_NAME}/{relative.as_posix()}",
                date_time=(1980, 1, 1, 0, 0, 0),
            )
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o644 << 16
            with (source_folder / relative).open("rb") as source, archive.open(entry, "w") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def matching_archive(path: Path, staged: Path, expected: set[Path]) -> bool:
    if not path.is_file():
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            names = {name for name in archive.namelist() if not name.endswith("/")}
            wanted = {f"{PACKAGE_NAME}/{relative.as_posix()}" for relative in expected}
            if names != wanted or archive.testzip() is not None:
                return False
            for relative in expected:
                member = f"{PACKAGE_NAME}/{relative.as_posix()}"
                if hashlib.sha256(archive.read(member)).hexdigest() != sha256(staged / relative):
                    return False
    except (OSError, zipfile.BadZipFile):
        return False
    return True


def replace_folder(staged: Path, destination: Path, backup: Path) -> None:
    if destination.exists():
        destination.rename(backup)
    try:
        staged.rename(destination)
    except OSError:
        if backup.exists():
            backup.rename(destination)
        raise


def main() -> None:
    sources = manifest()
    expected = set(sources)
    SUBMISSION_ROOT.mkdir(parents=True, exist_ok=True)
    if PACKAGE_DIR.resolve().parent != SUBMISSION_ROOT.resolve():
        raise ValueError("Submission directory escapes the submission root")
    if PACKAGE_ZIP.resolve().parent != SUBMISSION_ROOT.resolve():
        raise ValueError("Submission archive escapes the submission root")

    with tempfile.TemporaryDirectory(prefix=".submission-build-", dir=SUBMISSION_ROOT) as temporary:
        work = Path(temporary)
        staged_folder = work / PACKAGE_NAME
        for relative, source in sources.items():
            target = staged_folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

        folder_matches = matching_folder(PACKAGE_DIR, staged_folder, expected)
        if not folder_matches:
            replace_folder(staged_folder, PACKAGE_DIR, work / "previous-submission")

        staged_zip = work / f"{PACKAGE_NAME}.zip"
        write_archive(PACKAGE_DIR, staged_zip, expected)
        archive_matches = matching_archive(PACKAGE_ZIP, PACKAGE_DIR, expected)
        if not archive_matches:
            os.replace(staged_zip, PACKAGE_ZIP)

        if not matching_folder(PACKAGE_DIR, PACKAGE_DIR, expected):
            raise RuntimeError("Generated submission folder failed verification")
        if not matching_archive(PACKAGE_ZIP, PACKAGE_DIR, expected):
            raise RuntimeError("Generated ZIP failed verification")
        if any(sha256(PACKAGE_DIR / relative) != sha256(source) for relative, source in sources.items()):
            raise RuntimeError("Generated files differ from their project sources")

    print(f"Submission folder: {PACKAGE_DIR}")
    print(f"Submission archive: {PACKAGE_ZIP}")
    print(f"Verified {len(expected)} files against project sources and ZIP contents.")
    print(f"Existing folder matched: {folder_matches}; existing ZIP matched: {archive_matches}")


if __name__ == "__main__":
    main()
