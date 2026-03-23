from __future__ import annotations

import numpy as np

# GPS L1 C/A 码每个周期固定为 1023 个 chip，对应 1 ms 码周期。
CA_CODE_LENGTH = 1023

_PRN_G2_TAPS: dict[int, tuple[int, int]] = {
    1: (2, 6),
}


def generate_ca_code(prn_id: int) -> np.ndarray:
    """
    Generate one GPS L1 C/A epoch as int8 chips in +/-1 representation.

    Only PRN1 is implemented in v1, but the interface keeps ``prn_id``
    configurable for future expansion.

    物理意义：
    - 输出的是一个卫星 PRN 的 1 ms 扩频码序列。
    - 每个元素代表一个 chip，取值为 +/-1，后续会与导航 bit 相乘，
      再被重复采样为 baseband sample。
    """
    if prn_id not in _PRN_G2_TAPS:
        raise NotImplementedError(f"Only PRN1 is implemented in v1, got PRN {prn_id}.")

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


__all__ = ["CA_CODE_LENGTH", "generate_ca_code"]
