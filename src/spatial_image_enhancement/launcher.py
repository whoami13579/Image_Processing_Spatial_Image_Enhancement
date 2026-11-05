"""Desktop executable entry point; the module CLI remains unchanged."""

import sys


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] != "--gui":
        if args[0] == "--cli":
            args.pop(0)
        # Windowed PyInstaller builds have no streams. Attach to the invoking
        # terminal when available; never create a console for a double-click.
        if sys.platform == "win32" and getattr(sys, "frozen", False):
            import ctypes
            if ctypes.windll.kernel32.AttachConsole(-1):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8")
                sys.stderr = open("CONOUT$", "w", encoding="utf-8")
        from .cli import main as cli_main
        return cli_main(args)
    from .gui import main as gui_main
    return gui_main(args[1:] if args else [])
