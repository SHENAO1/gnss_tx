from __future__ import annotations

import numpy as np


def chips_to_complex_baseband(chips: np.ndarray, amplitude: float = 0.8) -> np.ndarray:
    """
    将 +/-1 chip 序列映射为复基带样本。

    物理意义：
    - 输入 ``chips`` 已经是扩频后的码片层数据。
    - 输出为 complex64，是为了匹配 GNU Radio / UHD 常用的复数基带接口。
    - 当前仅使用 I 支路承载 BPSK，Q 支路恒为 0。

    这一步描述的是：
    chip 符号 -> 基带幅度电平
    """
    chip_array = np.asarray(chips, dtype=np.int8)
    if chip_array.ndim != 1:
        raise ValueError("chips must be a 1-D sequence.")

    scaled = chip_array.astype(np.float32) * np.float32(amplitude)
    return scaled.astype(np.complex64)


__all__ = ["chips_to_complex_baseband"]
