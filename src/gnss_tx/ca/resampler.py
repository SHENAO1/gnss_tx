from __future__ import annotations

import numpy as np


def repeat_chips(chips: np.ndarray, samples_per_chip: int) -> np.ndarray:
    """
    将离散 chip 序列重复展开为 sample 序列。

    物理意义：
    - ``chips`` 是扩频码片层的数据，码率通常对应 GPS C/A 的 1.023 Mcps。
    - ``samples_per_chip`` 指每个 chip 在数字基带中占多少个采样点。
    - 返回值仍是 +/-1 序列，但已经从 chip 粒度扩展到了 sample 粒度。

    补充说明：
    - 这是“按 chip 重复”的上采样方式（零阶保持），不会在 chip 内部做插值。
    - 输出长度关系：``len(out) = len(chips) * samples_per_chip``。
    - 示例：chips=[1, -1, 1], samples_per_chip=3
      输出为 [1, 1, 1, -1, -1, -1, 1, 1, 1]。
    """
    # 参数保护：每个 chip 的采样点数必须为正。
    if samples_per_chip <= 0:
        raise ValueError("samples_per_chip must be a positive integer.")

    # 统一转成 int8，便于保持输出数据类型稳定。
    chip_array = np.asarray(chips, dtype=np.int8)
    # 仅接受一维 chip 序列。
    if chip_array.ndim != 1:
        raise ValueError("chips must be a 1-D sequence.")

    # 空输入直接返回空数组，避免后续处理边界问题。
    if chip_array.size == 0:
        return np.empty(0, dtype=np.int8)

    # 将每个 chip 重复 samples_per_chip 次，得到采样点级序列。
    return np.repeat(chip_array, samples_per_chip).astype(np.int8, copy=False)


__all__ = ["repeat_chips"]
