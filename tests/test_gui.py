"""Integration checks for the viewer and its read-only regeneration workflow."""

import hashlib
from pathlib import Path
import time
import tkinter as tk
from types import SimpleNamespace

import numpy as np
from PIL import Image
import pytest

from spatial_image_enhancement import gui, launcher


@pytest.fixture(scope="module")
def desktop():
    root = tk.Tk()
    root.withdraw()
    yield root
    root.destroy()


@pytest.fixture
def viewer(desktop):
    # Keep a single Tcl interpreter, as a normal desktop application does.
    root = tk.Toplevel(desktop)
    app = gui.EnhancementViewer(root, gui.data_directory("outputs"), gui.data_directory("HW1_test_image"))
    root.update()
    yield app
    app.close()


def test_all_six_saved_images_histograms_and_navigation(viewer):
    for index, name in enumerate(gui.NAMES):
        viewer.selector.current(index)
        viewer.selector.event_generate("<<ComboboxSelected>>")
        viewer.root.update()
        assert viewer.index == index
        assert viewer.selection.get() == name
        for pane, (_, folder) in zip(viewer.panes, gui.PANELS):
            with Image.open(viewer.output / folder / name) as expected:
                assert np.array_equal(np.asarray(pane.source), np.asarray(expected))
            assert pane.photo.width() > 100
        with Image.open(viewer.output / "histograms" / f"{Path(name).stem}_histograms.png") as expected:
            assert np.array_equal(np.asarray(viewer.histogram.source), np.asarray(expected))
        assert viewer.histogram.photo.height() > 100
    viewer.move(1)
    assert viewer.index == 0
    viewer.move(-1)
    assert viewer.index == 5
    viewer.root.geometry("960x660")
    viewer.root.update()
    time.sleep(0.1)
    viewer.root.update()
    assert all(p.canvas.winfo_width() > 150 for p in viewer.panes)


def test_paths_ignore_working_directory(monkeypatch, tmp_path):
    expected = gui.data_directory("outputs")
    monkeypatch.chdir(tmp_path)
    assert gui.data_directory("outputs") == expected


def test_frozen_resource_fallback_and_external_override(monkeypatch, tmp_path):
    bundled = tmp_path / "bundle"
    (bundled / "outputs").mkdir(parents=True)
    monkeypatch.setattr(gui, "sys", SimpleNamespace(
        frozen=True, _MEIPASS=str(bundled), executable=str(tmp_path / "SpatialEnhancement.exe")))
    assert gui.data_directory("outputs") == bundled / "outputs"
    (tmp_path / "outputs").mkdir()
    assert gui.data_directory("outputs") == tmp_path / "outputs"


def test_missing_images_clear_previous_display(viewer, tmp_path):
    viewer.output = tmp_path
    viewer.show(1)
    assert "Cannot load 1-2.png" in viewer.status.get()
    assert all(p.source is None for p in [*viewer.panes, viewer.histogram])


def test_regeneration_preserves_all_saved_files_and_matches_18_pixels(viewer):
    saved = viewer.output
    before = {p: hashlib.sha256(p.read_bytes()).digest() for p in saved.rglob("*") if p.is_file()}
    viewer.regenerate_button.invoke()
    deadline = time.monotonic() + 120
    events = 0
    while viewer.temporary is None and time.monotonic() < deadline:
        viewer.root.update()
        events += 1
        time.sleep(0.02)
    assert viewer.temporary is not None
    assert events > 10  # The Tk event loop kept running during processing.
    for folder in ("gamma", "equalized", "combined"):
        for name in gui.NAMES:
            with Image.open(saved / folder / name) as expected, Image.open(viewer.output / folder / name) as actual:
                assert np.array_equal(np.asarray(expected), np.asarray(actual))
    assert (saved / "results.json").read_bytes() == (viewer.output / "results.json").read_bytes()
    assert all(hashlib.sha256(p.read_bytes()).digest() == digest for p, digest in before.items())


def test_entry_point_keeps_cli_and_launches_gui(monkeypatch):
    from spatial_image_enhancement import cli
    monkeypatch.setattr(cli, "main", lambda args: ("cli", args))
    monkeypatch.setattr(gui, "main", lambda args: ("gui", args))
    assert launcher.main([]) == ("gui", [])
    assert launcher.main(["--cli"]) == ("cli", [])
    assert launcher.main(["--output", "elsewhere"]) == ("cli", ["--output", "elsewhere"])
    assert launcher.main(["--gui", "--output", "elsewhere"]) == ("gui", ["--output", "elsewhere"])
