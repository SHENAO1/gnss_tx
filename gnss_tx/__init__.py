from __future__ import annotations

from pathlib import Path
import pkgutil


__version__ = "0.1.0"
PROJECT_NAME = "gnss_tx"

_SRC_PACKAGE = Path(__file__).resolve().parent.parent / "src" / "gnss_tx"
__path__ = pkgutil.extend_path(__path__, __name__)
if str(_SRC_PACKAGE) not in __path__:
    __path__.append(str(_SRC_PACKAGE))
