from __future__ import annotations

import numpy as np


def chips_to_complex_baseband(chips: np.ndarray, amplitude: float = 0.8) -> np.ndarray:
    """Map +/-1 chips to complex64 baseband samples with zero Q branch."""
    chip_array = np.asarray(chips, dtype=np.int8)
    if chip_array.ndim != 1:
        raise ValueError("chips must be a 1-D sequence.")

    scaled = chip_array.astype(np.float32) * np.float32(amplitude)
    return scaled.astype(np.complex64)


__all__ = ["chips_to_complex_baseband"]
