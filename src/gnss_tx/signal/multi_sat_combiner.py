from __future__ import annotations

from typing import Sequence

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, SUPPORTED_PRN_IDS
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT, normalize_nav_bits
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator


def build_multi_sat_replay_samples(
    *,
    prn_ids: Sequence[int] | None = None,
    samples_per_chip: int = 4,
    nav_pattern: str | list[int] = "1 0 1 1 0 0 1 0",
    normalize: bool = True,
) -> np.ndarray:
    """
    叠加多颗 GPS L1 C/A 卫星的基带信号，返回可循环回放的 complex64 缓冲区。

    物理原理：
    - 不同 PRN 的 C/A 码设计为近正交，可直接线性叠加。
    - 叠加信号 = sum(nav_bit_i(t) * ca_code_i(t)) for i in prn_ids
    - normalize=True 时除以 sqrt(N) 做功率归一化，使叠加信号的每颗星
      平均功率等效于单星发射，保证 USRP DAC 不过载。

    缓冲区长度与 build_replay_samples 相同，均为完整 nav_pattern 周期，
    可在 GNU Radio vector_source_c(repeat=True) 中无缝循环回放。

    Args:
        prn_ids:        要叠加的 PRN 编号列表；None 表示全部 32 颗（PRN 1~32）。
        samples_per_chip: 每个 chip 展开为多少个 sample，决定采样率。
        nav_pattern:    导航 bit 循环模式（所有卫星共用同一模式）。
        normalize:      是否对叠加结果做功率归一化（推荐保持 True）。

    Returns:
        complex64 numpy 数组，长度 = nav_bits * 20 * 1023 * samples_per_chip。
    """
    if prn_ids is None:
        prn_ids = list(SUPPORTED_PRN_IDS)

    nav_bits = normalize_nav_bits(nav_pattern)
    epochs_per_buffer = CA_EPOCHS_PER_NAV_BIT * len(nav_bits)
    sample_count = epochs_per_buffer * CA_CODE_LENGTH * int(samples_per_chip)

    # 每颗星用单位幅度（amplitude=1.0）独立生成，再叠加后统一归一化。
    # 这样可以避免逐星缩放时的浮点累积误差。
    combined = np.zeros(sample_count, dtype=np.complex64)
    for prn_id in prn_ids:
        gen = GpsL1CaBpskGenerator(
            prn_id=prn_id,
            samples_per_chip=samples_per_chip,
            amplitude=1.0,
            nav_pattern=nav_bits.tolist(),
        )
        combined += gen.generate_samples(sample_count)

    # sqrt(N) 功率归一化：叠加 N 颗星后每颗星的平均功率保持不变。
    if normalize and len(prn_ids) > 1:
        combined /= np.sqrt(len(prn_ids))

    return combined.astype(np.complex64)


__all__ = ["build_multi_sat_replay_samples"]
