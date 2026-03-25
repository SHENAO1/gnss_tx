from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral
from typing import Sequence

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, generate_ca_code
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT, CyclicNavBitSource


@dataclass
class GeneratorState:
    # 当前 C/A 码片相位，范围为 [0, 1023)。
    # 它表示 1 ms PRN 码周期内部，当前走到了第几个 chip。
    code_phase: int = 0
    # 当前导航 bit 内已经走过了多少个 1 ms C/A epoch。
    # GPS L1 C/A 中 1 个导航 bit 跨越 20 个 C/A 码周期。
    nav_epoch_in_bit: int = 0
    # 当前处于第几个导航 bit。
    # 该索引决定当前 20 ms 时间窗内应该对 PRN 码施加哪个符号。
    nav_bit_index: int = 0
    # 当前 chip 内已经输出了多少个 sample。
    # 当 sample_rate = chip_rate * samples_per_chip 时，
    # 它负责把 chip 级状态扩展到 sample 级状态。
    sample_phase_in_chip: int = 0


class GpsL1CaBpskGenerator:
    """
    Stateful GPS L1 C/A PRN generator with 50 bps cyclic navigation bits.

    数据流对应关系：
    - nav bit: 导航数据层符号，持续 20 ms。
    - chip: nav bit 与 PRN C/A 码相乘后的扩频码片，持续约 1 / 1.023e6 s。
    - sample: 数字基带采样点，用于送入 GNU Radio / USRP。

    因此本类的核心职责是：
    1. 维护导航 bit、码相位、sample 相位这三个时间尺度的状态。
    2. 先确定当前 nav bit。
    3. 再取当前 PRN chip。
    4. 两者相乘得到 spread chip。
    5. 将每个 chip 展开为多个 baseband sample。
    """
    # 通俗理解：这个类像“带记忆的信号笔”。
    # 每次调用 generate_* 都会从上次停下的位置继续输出，不会悄悄从头开始。

    def __init__(
        self,
        prn_id: int = 1,
        samples_per_chip: int = 1,
        amplitude: float = 0.8,
        nav_pattern: Sequence[str | int] | str | None = None,
        initial_code_phase: int = 0,
        initial_nav_epoch: int = 0,
        initial_nav_bit_index: int = 0,
    ) -> None:
        # 必须是严格正整数，避免 0.5 这类值被 int() 截断为 0，
        # 进而导致 sample 生成循环无法前进。
        if isinstance(samples_per_chip, bool) or not isinstance(samples_per_chip, Integral):
            raise ValueError("samples_per_chip must be a positive integer.")
        if samples_per_chip <= 0:
            raise ValueError("samples_per_chip must be a positive integer.")

        self.prn_id = prn_id
        self.samples_per_chip = int(samples_per_chip)
        self.amplitude = float(amplitude)
        self.ca_code = generate_ca_code(prn_id)
        self.nav_source = CyclicNavBitSource.from_pattern(nav_pattern)

        if not 0 <= initial_code_phase < CA_CODE_LENGTH:
            raise ValueError(f"initial_code_phase must be in [0, {CA_CODE_LENGTH}).")
        if not 0 <= initial_nav_epoch < CA_EPOCHS_PER_NAV_BIT:
            raise ValueError(f"initial_nav_epoch must be in [0, {CA_EPOCHS_PER_NAV_BIT}).")
        if initial_nav_bit_index < 0:
            raise ValueError("initial_nav_bit_index must be >= 0.")

        # 这里把“时间刻度”初始化到起点：
        # code_phase 控制码片位置，nav_epoch_in_bit 控制 20ms 内第几个 1ms，
        # nav_bit_index 控制当前导航 bit，sample_phase_in_chip 控制 chip 内采样偏移。
        self.state = GeneratorState(
            code_phase=int(initial_code_phase),
            nav_epoch_in_bit=int(initial_nav_epoch),
            nav_bit_index=int(initial_nav_bit_index),
            sample_phase_in_chip=0,
        )

    def _current_nav_bit(self) -> int:
        # 当前 20ms 时间窗内要使用的导航符号（通常为 +1 或 -1）。
        return self.nav_source.bit_at(self.state.nav_bit_index)

    def _current_spread_chip(self) -> np.int8:
        # 物理意义：导航 bit 负责 20 ms 级别的符号翻转，
        # PRN 码负责 1.023 Mcps 级别的扩频。
        # 结果是每个 chip 对应一个符号位（+1/-1）。
        return np.int8(self._current_nav_bit() * self.ca_code[self.state.code_phase])

    def _advance_chip(self) -> None:
        # 推进到下一个 PRN chip。
        # 可把它想成一个“里程表”：
        # 先走 code_phase；code_phase 回卷时推进 nav_epoch_in_bit；
        # nav_epoch_in_bit 再回卷时推进 nav_bit_index。
        self.state.code_phase += 1
        if self.state.code_phase < CA_CODE_LENGTH:
            return

        # 1023 个 chip 走完后，一个 1 ms C/A epoch 结束。
        self.state.code_phase = 0
        self.state.nav_epoch_in_bit += 1
        if self.state.nav_epoch_in_bit < CA_EPOCHS_PER_NAV_BIT:
            return

        # 20 个 C/A epoch 走完后，说明当前 20 ms 导航 bit 结束，
        # 切换到下一个导航 bit。
        self.state.nav_epoch_in_bit = 0
        self.state.nav_bit_index += 1

    def generate_chips(self, num_chips: int) -> np.ndarray:
        if num_chips < 0:
            raise ValueError("num_chips must be >= 0.")
        if self.state.sample_phase_in_chip != 0:
            raise RuntimeError("Generator is not chip-aligned; finish the current chip first.")

        # 该接口输出的是 chip 级序列，常用于离线分析或相关性验证。
        # 这里每次循环只做两件事：取当前 chip，然后把状态推进 1 个 chip。
        chips = np.empty(num_chips, dtype=np.int8)
        for index in range(num_chips):
            chips[index] = self._current_spread_chip()
            self._advance_chip()
        return chips

    def generate_samples(self, num_samples: int) -> np.ndarray:
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0.")
        out = np.empty(num_samples, dtype=np.complex64)
        if num_samples == 0:
            return out

        # 当前实现中 Q 支路恒为 0，因此生成的是实值 BPSK，
        # 再以 complex64 表示，便于直接送入 GNU Radio complex 流。
        pos_level = np.complex64(self.amplitude + 0j)
        neg_level = np.complex64(-self.amplitude + 0j)

        write_index = 0
        while write_index < num_samples:
            spread_chip = self._current_spread_chip()
            # 一个 chip 会被展开成 ``samples_per_chip`` 个 sample。
            # 如果当前调用只消费了部分 chip，就先把当前 chip 的剩余 sample 补齐。
            # 也就是说 run 表示“本轮最多能连续写多少个相同符号的 sample”。
            samples_left_in_chip = self.samples_per_chip - self.state.sample_phase_in_chip
            samples_left_in_request = num_samples - write_index
            run = min(samples_left_in_chip, samples_left_in_request)

            # 对当前 chip 对应的连续 sample 区间做一次性切片写入。
            out[write_index : write_index + run] = pos_level if spread_chip > 0 else neg_level
            write_index += run
            self.state.sample_phase_in_chip += run

            if self.state.sample_phase_in_chip == self.samples_per_chip:
                # 当前 chip 的所有 sample 已输出完，才允许进入下一个 chip。
                # 这样可保证 chip 边界和 sample 边界严格一致，不会跳相位。
                self.state.sample_phase_in_chip = 0
                self._advance_chip()

        return out


__all__ = ["GeneratorState", "GpsL1CaBpskGenerator"]
