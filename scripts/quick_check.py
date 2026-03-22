from pathlib import Path
import sys
import numpy as np

from gnss_tx import __version__, PROJECT_NAME


def main():
    project_root = Path(__file__).resolve().parents[1]

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
        project_root / "results",
        project_root / "flowgraphs",
    ]

    print("Path check:")
    all_ok = True
    for p in required_paths:
        ok = p.exists()
        print(f"  [{'OK' if ok else 'NO'}] {p}")
        all_ok = all_ok and ok

    print()
    x = np.linspace(0, 1, 8, endpoint=False)
    tone = np.cos(2 * np.pi * x)

    print("Numpy test tone:")
    print(tone)

    print()
    if all_ok:
        print("[SUCCESS] Project structure and Python environment look good.")
    else:
        print("[WARNING] Some required paths are missing.")


if __name__ == "__main__":
    main()
