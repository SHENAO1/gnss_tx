from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from gnss_tx import __version__, PROJECT_NAME


def check_gnuradio_uhd():
    try:
        from gnuradio import uhd as gr_uhd
    except Exception as exc:
        return False, repr(exc), None
    return True, None, getattr(gr_uhd, "__file__", "<builtin>")


def main() -> int:
    project_root = PROJECT_ROOT

    print("=" * 60)
    print("Quick Check: GNSS TX Project")
    print("=" * 60)
    print(f"Project name   : {PROJECT_NAME}")
    print(f"Version        : {__version__}")
    print(f"Python exec    : {sys.executable}")
    print(f"Python version : {sys.version.split()[0]}")
    print(f"Project root   : {project_root}")
    print(f"Numpy version  : {np.__version__}")
    print()

    required_paths = [
        project_root / "src" / "gnss_tx",
        project_root / "configs",
        project_root / "scripts",
        project_root / "flowgraphs",
    ]

    print("Path check:")
    path_ok = True
    for p in required_paths:
        ok = p.exists()
        print(f"  [{'OK' if ok else 'NO'}] {p}")
        path_ok = path_ok and ok

    print()
    gnuradio_ok, gnuradio_error, gnuradio_path = check_gnuradio_uhd()
    print("GNU Radio / UHD check:")
    if gnuradio_ok:
        print(f"  [OK] gnuradio.uhd : {gnuradio_path}")
    else:
        print(f"  [NO] gnuradio.uhd : {gnuradio_error}")
        print("  [HINT] Recreate .venv with `python3 -m venv --system-site-packages .venv`")
        print("  [HINT] after installing `gnuradio python3-gnuradio uhd-host` via apt.")

    print()
    x = np.linspace(0, 1, 8, endpoint=False)
    tone = np.cos(2 * np.pi * x)

    print("Numpy test tone:")
    print(tone)

    print()
    if path_ok and gnuradio_ok:
        print("[SUCCESS] Project structure, Python environment, and GNU Radio/UHD bindings look good.")
        return 0

    print("[WARNING] Setup is incomplete. Fix the warnings above before running TX.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
