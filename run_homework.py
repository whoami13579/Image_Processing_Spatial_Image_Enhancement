"""PyInstaller entry point; also runnable with uv run python run_homework.py."""

from spatial_image_enhancement.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
