"""Read-only Tkinter presentation of the saved homework results."""

import argparse
from pathlib import Path
import queue
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

NAMES = tuple(f"1-{i}.png" for i in range(1, 7))
PANELS = (
    ("Original", "original"),
    ("Gamma Correction", "gamma"),
    ("Histogram Equalization", "equalized"),
    ("Gamma Correction +\nContrast Stretching", "combined"),
)


def data_directory(folder: str) -> Path:
    """Resolve resources independently of the caller's working directory."""
    if getattr(sys, "frozen", False):
        executable_dir = Path(sys.executable).resolve().parent
        candidates = [executable_dir / folder]
        # A development build lives in dist/; a copied EXE uses bundled data.
        if executable_dir.name == "dist":
            candidates.append(executable_dir.parent / folder)
        candidates.append(Path(sys._MEIPASS) / folder)
    else:
        candidates = [Path(__file__).resolve().parents[2] / folder]
    return next((p for p in candidates if p.is_dir()), candidates[-1])


def load_views(output: Path, name: str) -> list[Image.Image]:
    paths = [output / folder / name for _, folder in PANELS]
    paths.append(output / "histograms" / f"{Path(name).stem}_histograms.png")
    images = []
    for path in paths:
        with Image.open(path) as source:
            images.append(source.copy())
    return images


class ImagePane(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, background="#edf0f4", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.source = None
        self.photo = None
        self.pending = None
        self.canvas.bind("<Configure>", self.schedule_draw)

    def set_image(self, source):
        self.source = source
        self.draw()

    def schedule_draw(self, event=None):
        if self.pending:
            self.after_cancel(self.pending)
        self.pending = self.after(50, self.draw)

    def draw(self):
        self.pending = None
        self.canvas.delete("all")
        if self.source is None:
            return
        image = self.source.copy()
        image.thumbnail((max(1, self.canvas.winfo_width() - 12),
                         max(1, self.canvas.winfo_height() - 12)), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image, master=self.canvas)
        self.canvas.create_image(self.canvas.winfo_width() // 2,
                                 self.canvas.winfo_height() // 2, image=self.photo)


class EnhancementViewer:
    def __init__(self, root: tk.Tk, output: Path, inputs: Path):
        self.root, self.output, self.inputs = root, output, inputs
        self.index = 0
        self.messages = queue.Queue()
        self.worker = None
        self.temporary = None
        self.closed = False
        root.title("Spatial Image Enhancement | Homework 1")
        root.geometry("1280x860")
        root.minsize(960, 660)
        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 11))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("Title.TLabel", font=("Segoe UI", 19, "bold"))
        style.configure("Panel.TLabel", font=("Segoe UI", 11, "bold"))
        body = ttk.Frame(root, padding=16)
        body.pack(fill="both", expand=True)
        ttk.Label(body, text="Spatial Image Enhancement", style="Title.TLabel").pack(anchor="w")
        navigation = ttk.Frame(body)
        navigation.pack(fill="x", pady=(12, 12))
        ttk.Button(navigation, text="Previous", command=lambda: self.move(-1)).pack(side="left")
        self.selection = tk.StringVar(value=NAMES[0])
        self.selector = ttk.Combobox(navigation, textvariable=self.selection, values=NAMES,
                                     state="readonly", width=12, font=("Segoe UI", 11))
        self.selector.pack(side="left", padx=10)
        self.selector.bind("<<ComboboxSelected>>", lambda e: self.show(NAMES.index(self.selection.get())))
        ttk.Button(navigation, text="Next", command=lambda: self.move(1)).pack(side="left")
        self.counter = ttk.Label(navigation)
        self.counter.pack(side="left", padx=16)
        self.regenerate_button = ttk.Button(navigation, text="Regenerate preview", command=self.regenerate)
        self.regenerate_button.pack(side="right")
        self.progress = ttk.Progressbar(navigation, mode="indeterminate", length=100)
        self.progress.pack(side="right", padx=12)
        comparison = ttk.Frame(body, height=240)
        comparison.pack(fill="both", expand=True)
        comparison.grid_propagate(False)
        comparison.rowconfigure(1, weight=1)
        self.panes = []
        for column, (title, _) in enumerate(PANELS):
            comparison.columnconfigure(column, weight=1, uniform="images")
            ttk.Label(comparison, text=title, style="Panel.TLabel", anchor="center",
                      justify="center").grid(row=0, column=column, sticky="ew", padx=4, pady=6)
            pane = ImagePane(comparison)
            pane.grid(row=1, column=column, sticky="nsew", padx=4)
            self.panes.append(pane)
        ttk.Label(body, text="Intensity histograms | Original and Histogram Equalization",
                  style="Panel.TLabel").pack(anchor="w", pady=(14, 4))
        self.histogram = ImagePane(body)
        self.histogram.configure(height=360)
        self.histogram.pack_propagate(False)
        self.histogram.pack(fill="both", expand=True)
        self.status = tk.StringVar()
        ttk.Label(body, textvariable=self.status, wraplength=1100).pack(anchor="w", pady=(8, 0))
        root.bind("<Left>", lambda e: self.move(-1))
        root.bind("<Right>", lambda e: self.move(1))
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.show(0)
        root.after(100, self.poll)

    def move(self, delta):
        self.show((self.index + delta) % len(NAMES))

    def show(self, index):
        self.index = index
        name = NAMES[index]
        self.selection.set(name)
        self.counter.configure(text=f"Image {index + 1} of {len(NAMES)}  |  Left / Right keys")
        try:
            images = load_views(self.output, name)
        except (OSError, ValueError) as error:
            for pane in [*self.panes, self.histogram]:
                pane.set_image(None)
            self.status.set(f"Cannot load {name}: {error}. Use Regenerate preview to create temporary results.")
            return
        for pane, image in zip([*self.panes, self.histogram], images):
            pane.set_image(image)
        self.status.set(f"{name}  |  Saved results: {self.output}")

    def regenerate(self):
        if self.worker and self.worker.is_alive():
            return
        self.regenerate_button.state(["disabled"])
        self.progress.start()
        self.status.set("Generating all six previews with the existing pipeline; saved outputs are preserved.")
        self.worker = threading.Thread(target=self.generate_worker, daemon=True)
        self.worker.start()

    def generate_worker(self):
        temporary = tempfile.TemporaryDirectory(prefix="spatial-enhancement-preview-")
        try:
            from .cli import GAMMAS, run
            run(self.inputs, Path(temporary.name), GAMMAS.copy())
            if self.closed:
                temporary.cleanup()
            else:
                self.messages.put((temporary, None))
        except Exception as error:
            temporary.cleanup()
            self.messages.put((None, str(error)))

    def poll(self):
        try:
            temporary, error = self.messages.get_nowait()
        except queue.Empty:
            pass
        else:
            self.progress.stop()
            self.regenerate_button.state(["!disabled"])
            if error:
                self.status.set(f"Regeneration failed: {error}")
                messagebox.showerror("Regeneration failed", error, parent=self.root)
            else:
                if self.temporary:
                    self.temporary.cleanup()
                self.temporary = temporary
                self.output = Path(temporary.name)
                self.show(self.index)
        self.root.after(100, self.poll)

    def close(self):
        self.closed = True
        if self.temporary:
            self.temporary.cleanup()
        self.root.destroy()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="View saved spatial enhancement results")
    parser.add_argument("--input", type=Path, default=data_directory("HW1_test_image"))
    parser.add_argument("--output", type=Path, default=data_directory("outputs"))
    args = parser.parse_args(argv)
    root = tk.Tk()
    EnhancementViewer(root, args.output.resolve(), args.input.resolve())
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
