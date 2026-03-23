"""导航比特归一化与循环访问相关单元测试。

本模块用于验证：
- 导航比特输入能否统一映射到 `+1/-1`
- 默认导航模式是否满足最小可用要求
- 循环导航源是否能按索引回绕
"""

import unittest

import numpy as np

from gnss_tx.nav.nav_bits import CyclicNavBitSource, normalize_nav_bits


class TestNavBits(unittest.TestCase):
    """验证导航比特归一化和循环访问逻辑的测试集合。"""

    def test_normalize_nav_bits_maps_zero_to_minus_one(self) -> None:
        """验证导航比特归一化时 `0` 会被映射为 `-1`。

        功能说明：
        - 验证多种输入形式的导航比特会被统一转换为 `+1/-1`。
        - 确保测试模式中的 `0`、`-1` 和字符串形式都能正确归一化。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的整型与字符串混合导航模式。

        输出说明：
        - 无返回值。
        - 期望行为是输出数组与预期 `+1/-1` 序列完全一致。
        """
        # 验证多种导航比特表示法的统一归一化结果。
        bits = normalize_nav_bits([1, 0, -1, "1", "0", "-"])
        expected = np.array([1, -1, -1, 1, -1, -1], dtype=np.int8)
        np.testing.assert_array_equal(bits, expected)

    def test_default_pattern_is_non_empty_and_binary(self) -> None:
        """验证默认导航模式非空且仅包含二值符号。

        功能说明：
        - 检查默认导航模式能否作为最小测试输入直接使用。
        - 验证归一化结果是否仅包含 `+1/-1`。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `normalize_nav_bits()` 的默认返回值。

        输出说明：
        - 无返回值。
        - 期望行为是输出非空，且所有元素都在 `+1/-1` 集合内。
        """
        # 使用默认导航模式，检查最小可用性。
        bits = normalize_nav_bits()
        self.assertGreater(bits.size, 0)
        self.assertTrue(np.all(np.isin(bits, (-1, 1))))

    def test_cyclic_source_wraps_indices(self) -> None:
        """验证循环导航源在越界索引时会自动回绕。

        功能说明：
        - 构造一个短导航模式并访问超出长度的索引。
        - 验证循环源是否按照模长回绕。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的导航模式 `[1, -1, 1]`。

        输出说明：
        - 无返回值。
        - 期望行为是越界索引返回与周期回绕一致的导航比特。
        """
        # 验证导航比特循环源的周期访问行为。
        source = CyclicNavBitSource.from_pattern([1, -1, 1])
        self.assertEqual(source.bit_at(0), 1)
        self.assertEqual(source.bit_at(1), -1)
        self.assertEqual(source.bit_at(3), 1)
        self.assertEqual(source.bit_at(4), -1)


if __name__ == "__main__":
    unittest.main()
