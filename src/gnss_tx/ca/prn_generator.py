from __future__ import annotations

import numpy as np

# GPS L1 C/A 码每个周期固定为 1023 个 chip，对应 1 ms 码周期。
CA_CODE_LENGTH = 1023

_PRN_G2_TAPS: dict[int, tuple[int, int]] = {
    1: (2, 6),
    2: (3, 7),
    3: (4, 8),
    4: (5, 9),
    5: (1, 9),
    6: (2, 10),
    7: (1, 8),
    8: (2, 9),
    9: (3, 10),
    10: (2, 3),
    11: (3, 4),
    12: (5, 6),
    13: (6, 7),
    14: (7, 8),
    15: (8, 9),
    16: (9, 10),
    17: (1, 4),
    18: (2, 5),
    19: (3, 6),
    20: (4, 7),
    21: (5, 8),
    22: (6, 9),
    23: (1, 3),
    24: (4, 6),
    25: (5, 7),
    26: (6, 8),
    27: (7, 9),
    28: (8, 10),
    29: (1, 6),
    30: (2, 7),
    31: (3, 8),
    32: (4, 9),
}
SUPPORTED_PRN_IDS = tuple(sorted(_PRN_G2_TAPS))


def generate_ca_code(prn_id: int) -> np.ndarray:
    """
    Generate one GPS L1 C/A epoch as int8 chips in +/-1 representation.

    物理意义：
    - 输出的是一个卫星 PRN 的 1 ms 扩频码序列。
    - 每个元素代表一个 chip，取值为 +/-1，后续会与导航 bit 相乘，
      再被重复采样为 baseband sample。
    """
    if prn_id not in _PRN_G2_TAPS:
        raise ValueError(
            f"prn_id must be one of {SUPPORTED_PRN_IDS[0]}..{SUPPORTED_PRN_IDS[-1]}, got {prn_id}."
        )

    # GPS L1 C/A 码由两个 10 级 LFSR 组合而成。
    # G1、G2 初值全 1；不同 PRN 通过选择 G2 的抽头组合来区分。
    g1 = np.ones(10, dtype=np.uint8)
    g2 = np.ones(10, dtype=np.uint8)
    tap_a, tap_b = _PRN_G2_TAPS[prn_id]

    code = np.empty(CA_CODE_LENGTH, dtype=np.int8)
    for index in range(CA_CODE_LENGTH):
        # 每次循环生成 1 个 chip。
        # g1_out 和 g2_out 的异或结果决定当前 C/A chip 是 +1 还是 -1。
        g1_out = g1[9]
        g2_out = g2[tap_a - 1] ^ g2[tap_b - 1]
        code[index] = 1 if (g1_out ^ g2_out) == 0 else -1

        # 反馈多项式来自 GPS L1 C/A 码定义。
        # 这里推进的是“码寄存器状态”，对应下一个 chip 的生成条件。
        g1_feedback = g1[2] ^ g1[9]
        g2_feedback = g2[1] ^ g2[2] ^ g2[5] ^ g2[7] ^ g2[8] ^ g2[9]

        g1[1:] = g1[:-1]
        g1[0] = g1_feedback

        g2[1:] = g2[:-1]
        g2[0] = g2_feedback

    return code


__all__ = ["CA_CODE_LENGTH", "SUPPORTED_PRN_IDS", "generate_ca_code"]
