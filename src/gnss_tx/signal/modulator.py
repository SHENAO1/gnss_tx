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
    # 统一输入类型，确保后续计算和输出类型可控。
    chip_array = np.asarray(chips, dtype=np.int8)
    # 调制链路期望一维码片流，二维/更高维输入在此提前拦截。
    if chip_array.ndim != 1:
        raise ValueError("chips must be a 1-D sequence.")

    # 将整数码片映射到浮点幅度电平（例如 +1/-1 -> +A/-A）。
    scaled = chip_array.astype(np.float32) * np.float32(amplitude)
    # 转为 complex64 以匹配 GNU Radio/UHD 复基带接口，虚部默认 0。
    return scaled.astype(np.complex64)


__all__ = ["chips_to_complex_baseband"]
