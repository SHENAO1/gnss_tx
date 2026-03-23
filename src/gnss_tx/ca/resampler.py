from __future__ import annotations

import numpy as np


def repeat_chips(chips: np.ndarray, samples_per_chip: int) -> np.ndarray:
    """
    将离散 chip 序列重复展开为 sample 序列。

    物理意义：
    - ``chips`` 是扩频码片层的数据，码率通常对应 GPS C/A 的 1.023 Mcps。
    - ``samples_per_chip`` 指每个 chip 在数字基带中占多少个采样点。
    - 返回值仍是 +/-1 序列，但已经从 chip 粒度扩展到了 sample 粒度。
    """
    if samples_per_chip <= 0:
        raise ValueError("samples_per_chip must be a positive integer.")

    chip_array = np.asarray(chips, dtype=np.int8)
    if chip_array.ndim != 1:
        raise ValueError("chips must be a 1-D sequence.")

    if chip_array.size == 0:
        return np.empty(0, dtype=np.int8)

    return np.repeat(chip_array, samples_per_chip).astype(np.int8, copy=False)


__all__ = ["repeat_chips"]
