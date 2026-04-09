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
    """将导航 bit 模式归一化为双极性 int8 一维数组。

    物理意义：扩频链路要求 s[k] = d[k]·c[k]，其中 d[k] 为导航 bit，
    c[k] 为 PRN chip，均须为 +/-1。若 d[k] 保留 0/1 表示，乘积会出现
    0 值，相当于"关掉"信号，破坏 BPSK 建模。统一转为 +/-1 后，
    接收端相关解扩 r[k]·c[k] ≈ d[k] 才能正确恢复导航数据。

    Args:
        nav_pattern: 导航 bit 输入，支持三种形式：
            - None：使用 DEFAULT_NAV_PATTERN。
            - 字符串：按逗号/空白分词；若分词为空则按字符拆分。
            - 序列（int/str 元素）：逐元素归一化，支持 1/0/-1/"+"/"-" 等格式。

    Returns:
        shape=(N,) 的 np.int8 数组，元素仅为 +1 或 -1。

    Raises:
        ValueError: 输入为空序列，或包含不支持的 token 时抛出。
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
        """返回指定时刻对应的导航 bit（+1 或 -1）。

        取模实现周期访问，index 可持续增长而无需手动重置。

        Args:
            index: 导航 bit 全局索引（非负整数），对应发射序列中的第几个 bit。

        Returns:
            +1 或 -1。
        """
        return int(self.bits[index % self.bits.size])

    def as_array(self) -> np.ndarray:
        """返回内部 bit 模式的副本，避免外部误修改内部状态。

        Returns:
            shape=(N,) 的 np.int8 数组，元素为 +1 或 -1。
        """
        return self.bits.copy()


__all__ = [
    "CA_EPOCHS_PER_NAV_BIT",
    "CyclicNavBitSource",
    "DEFAULT_NAV_PATTERN",
    "NAV_BIT_RATE_BPS",
    "normalize_nav_bits",
]
