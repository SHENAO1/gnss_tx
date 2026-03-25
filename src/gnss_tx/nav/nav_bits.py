from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

# GPS L1 C/A 导航电文速率为 50 bps。
NAV_BIT_RATE_BPS = 50
# 每个导航 bit 覆盖 20 个 C/A 码周期，即 20 ms。
CA_EPOCHS_PER_NAV_BIT = 20
# 默认导航 bit 循环模式
DEFAULT_NAV_PATTERN = (1, -1, 1, 1, -1, -1, 1, -1)


def _normalize_one_bit(token: str | int) -> int:
    """将单个导航 bit 标记归一化为 +/-1。

    支持输入：
    - 数值：1 -> +1；0/-1 -> -1
    - 字符串："1"、"+1"、"+" -> +1；"0"、"-1"、"-" -> -1

    说明：
    - 将 0 映射为 -1，便于后续扩频链路使用双极性乘法表示。
    - 遇到不支持的 token 会显式报错，避免静默吞错。
    """
    if isinstance(token, (int, np.integer)):
        if token == 1:
            return 1
        if token in (0, -1):
            return -1
        raise ValueError(f"Unsupported navigation bit value: {token}")

    text = str(token).strip()
    if text in {"1", "+1", "+"}:
        return 1
    if text in {"0", "-1", "-"}:
        return -1
    raise ValueError(f"Unsupported navigation bit token: {token!r}")


def normalize_nav_bits(nav_pattern: Sequence[str | int] | str | None = None) -> np.ndarray:
    """
    Normalize nav bits to a 1-D int8 array in +/-1 representation.

    物理意义：
    - 导航层输入可能写成 1/0、+1/-1 或字符串。
    - 在扩频链路中统一转成 +/-1 之后，才能与 PRN chip 相乘，
      形成最终的 spread chip。
    - s[k]=d[k]⋅c[k]，其中 d[k] 是导航 bit，c[k] 是 PRN chip，s[k] 是发射的 spread chip。
    - 如果数据还在 0/1 域，b∈{0,1}， c∈{−1,+1}，b⋅c∈{0,−1,+1}，当 b=0 ，时输出全变 0，相当于把信号“关掉”，不是“相位翻转”，这不符合 BPSK/DS-SS 的建模。
    - 接收端再乘一次同一 PRN，r[k]⋅c[k]≈d[k]⋅c[k]⋅c[k]=d[k]，因为 c[k]⋅c[k]=1，所以能正确恢复 d[k]。


        输入行为：
        - nav_pattern is None：使用 DEFAULT_NAV_PATTERN。
        - nav_pattern 为字符串：优先按逗号/空白分词；若分词为空则按字符拆分。
        - nav_pattern 为序列：逐元素归一化。

        输出约束：
        - 返回 np.int8 的一维数组，元素仅为 {-1, +1}。
        - 若输入为空，抛出 ValueError。
    """
    if nav_pattern is None:
        tokens: Iterable[str | int] = DEFAULT_NAV_PATTERN
    elif isinstance(nav_pattern, str):
        compact = nav_pattern.replace(",", " ").split()
        tokens = compact if compact else list(nav_pattern)
    else:
        tokens = nav_pattern

    # 统一映射到双极性 bit，便于后续与 PRN chip 直接相乘。
    bits = np.array([_normalize_one_bit(token) for token in tokens], dtype=np.int8)
    if bits.size == 0:
        raise ValueError("nav_pattern must contain at least one bit.")
    return bits


@dataclass(frozen=True)
class CyclicNavBitSource:
    """循环导航 bit 源。

    用途：
    - 将有限长度的导航 bit 模式视为循环序列，支持长时间连续发射。
    - 通过 bit_at(index) 访问任意时刻对应的导航 bit。
    """
    bits: np.ndarray

    @classmethod
    def from_pattern(cls, nav_pattern: Sequence[str | int] | str | None = None) -> "CyclicNavBitSource":
        """从配置模式构造循环 bit 源。"""
        return cls(bits=normalize_nav_bits(nav_pattern))

    def __post_init__(self) -> None:
        # 防御式校验：确保内部状态始终是合法的 1-D 双极性 bit 数组。
        bit_array = np.asarray(self.bits, dtype=np.int8)
        if bit_array.ndim != 1 or bit_array.size == 0:
            raise ValueError("bits must be a non-empty 1-D sequence.")
        if not np.all(np.isin(bit_array, (-1, 1))):
            raise ValueError("bits must contain only +/-1.")
        object.__setattr__(self, "bits", bit_array)

    def bit_at(self, index: int) -> int:
        # 当前工程使用循环导航 bit 源，便于长时间回放时保持模式重复。
        # 取模实现周期访问：index 可持续增长而无需手动重置。
        return int(self.bits[index % self.bits.size])

    def as_array(self) -> np.ndarray:
        # 返回副本，避免外部误修改内部状态。
        return self.bits.copy()


__all__ = [
    "CA_EPOCHS_PER_NAV_BIT",
    "CyclicNavBitSource",
    "DEFAULT_NAV_PATTERN",
    "NAV_BIT_RATE_BPS",
    "normalize_nav_bits",
]
