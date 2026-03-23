from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np

# GPS L1 C/A 导航电文速率为 50 bps。
NAV_BIT_RATE_BPS = 50
# 每个导航 bit 覆盖 20 个 C/A 码周期，即 20 ms。
CA_EPOCHS_PER_NAV_BIT = 20
DEFAULT_NAV_PATTERN = (1, -1, 1, 1, -1, -1, 1, -1)


def _normalize_one_bit(token: str | int) -> int:
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
    """
    if nav_pattern is None:
        tokens: Iterable[str | int] = DEFAULT_NAV_PATTERN
    elif isinstance(nav_pattern, str):
        compact = nav_pattern.replace(",", " ").split()
        tokens = compact if compact else list(nav_pattern)
    else:
        tokens = nav_pattern

    bits = np.array([_normalize_one_bit(token) for token in tokens], dtype=np.int8)
    if bits.size == 0:
        raise ValueError("nav_pattern must contain at least one bit.")
    return bits


@dataclass(frozen=True)
class CyclicNavBitSource:
    bits: np.ndarray

    @classmethod
    def from_pattern(cls, nav_pattern: Sequence[str | int] | str | None = None) -> "CyclicNavBitSource":
        return cls(bits=normalize_nav_bits(nav_pattern))

    def __post_init__(self) -> None:
        bit_array = np.asarray(self.bits, dtype=np.int8)
        if bit_array.ndim != 1 or bit_array.size == 0:
            raise ValueError("bits must be a non-empty 1-D sequence.")
        if not np.all(np.isin(bit_array, (-1, 1))):
            raise ValueError("bits must contain only +/-1.")
        object.__setattr__(self, "bits", bit_array)

    def bit_at(self, index: int) -> int:
        # 当前工程使用循环导航 bit 源，便于长时间回放时保持模式重复。
        return int(self.bits[index % self.bits.size])

    def as_array(self) -> np.ndarray:
        return self.bits.copy()


__all__ = [
    "CA_EPOCHS_PER_NAV_BIT",
    "CyclicNavBitSource",
    "DEFAULT_NAV_PATTERN",
    "NAV_BIT_RATE_BPS",
    "normalize_nav_bits",
]
