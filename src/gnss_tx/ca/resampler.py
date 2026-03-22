from __future__ import annotations

import numpy as np


def repeat_chips(chips: np.ndarray, samples_per_chip: int) -> np.ndarray:
    """Repeat each +/-1 chip ``samples_per_chip`` times."""
    if samples_per_chip <= 0:
        raise ValueError("samples_per_chip must be a positive integer.")

    chip_array = np.asarray(chips, dtype=np.int8)
    if chip_array.ndim != 1:
        raise ValueError("chips must be a 1-D sequence.")

    if chip_array.size == 0:
        return np.empty(0, dtype=np.int8)

    return np.repeat(chip_array, samples_per_chip).astype(np.int8, copy=False)


__all__ = ["repeat_chips"]
