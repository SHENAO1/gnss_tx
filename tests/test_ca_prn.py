"""PRN 码生成相关单元测试。

本模块用于验证 GPS L1 C/A PRN 码生成器的基础正确性，包括：
- 码长、数据类型与符号集合是否合法
- PRN 码是否满足近似平衡特性
- 周期自相关峰值是否出现在零移位
- PRN 取值范围与不同 PRN 之间的区分是否合理
"""

import unittest

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, SUPPORTED_PRN_IDS, generate_ca_code


class TestCaPrnGenerator(unittest.TestCase):
    """验证 PRN 码生成器输出行为的测试集合。"""

    def test_prn1_has_expected_length_and_symbols(self) -> None:
        """验证 PRN1 输出码长、类型与符号取值范围。

        功能说明：
        - 验证 PRN1 生成结果是否符合 GPS L1 C/A 单周期长度定义。
        - 验证输出是否为 `int8` 类型且仅包含 `+1/-1` 符号。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `generate_ca_code(1)` 的直接输出。

        输出说明：
        - 无返回值。
        - 期望行为是生成长度为 `CA_CODE_LENGTH` 的一维 PRN 码数组。
        """
        # 生成 PRN1 的单周期 C/A 码。
        code = generate_ca_code(1)
        # 校验 GNSS PRN 码长度、存储类型和符号集合。
        self.assertEqual(code.shape, (CA_CODE_LENGTH,))
        self.assertEqual(code.dtype, np.int8)
        self.assertTrue(np.all(np.isin(code, (-1, 1))))

    def test_prn1_is_balanced(self) -> None:
        """验证 PRN1 在一个周期内满足近似平衡特性。

        功能说明：
        - 验证 PRN1 周期内 `+1/-1` 码片数量接近平衡。
        - 对 GPS L1 C/A 码而言，单周期求和绝对值应为 `1`。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `generate_ca_code(1)` 的直接输出。

        输出说明：
        - 无返回值。
        - 期望行为是周期码和的绝对值为 `1`。
        """
        # 生成待分析的 PRN1 码序列。
        code = generate_ca_code(1)
        # 校验周期内正负码片数量满足平衡性要求。
        self.assertEqual(abs(int(code.sum())), 1)

    def test_prn1_periodic_autocorrelation_peaks_at_zero_shift(self) -> None:
        """验证 PRN1 周期自相关在零移位处取得主峰。

        功能说明：
        - 计算 PRN1 单周期与其循环移位版本之间的周期自相关。
        - 验证零移位处主峰为 `CA_CODE_LENGTH`，其余移位旁瓣受控。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `generate_ca_code(1)` 生成的 PRN1 码。

        输出说明：
        - 无返回值。
        - 期望行为是零移位相关峰值最大，非零移位旁瓣不超过阈值。
        """
        # 生成 PRN1 码并提升到整型，便于做相关计算。
        code = generate_ca_code(1).astype(np.int32)
        # 通过循环移位计算周期自相关，验证 PRN 码相关特性。
        correlations = np.array(
            [int(np.dot(code, np.roll(code, shift))) for shift in range(CA_CODE_LENGTH)],
            dtype=np.int32,
        )
        # 校验主峰与旁瓣范围是否符合预期。
        self.assertEqual(int(correlations[0]), CA_CODE_LENGTH)
        self.assertLessEqual(int(np.max(np.abs(correlations[1:]))), 65)

    def test_supported_prns_share_common_shape_rules(self) -> None:
        for prn_id in (1, 2, 7, 32):
            code = generate_ca_code(prn_id)
            self.assertEqual(code.shape, (CA_CODE_LENGTH,))
            self.assertEqual(code.dtype, np.int8)
            self.assertTrue(np.all(np.isin(code, (-1, 1))))
            self.assertEqual(abs(int(code.sum())), 1)

    def test_different_prns_produce_distinct_codes_with_bounded_cross_correlation(self) -> None:
        code_1 = generate_ca_code(1).astype(np.int32)
        code_7 = generate_ca_code(7).astype(np.int32)

        self.assertFalse(np.array_equal(code_1, code_7))
        periodic_cross = np.array(
            [int(np.dot(code_1, np.roll(code_7, shift))) for shift in range(CA_CODE_LENGTH)],
            dtype=np.int32,
        )
        self.assertLessEqual(int(np.max(np.abs(periodic_cross))), 65)

    def test_prn_range_rejects_values_outside_supported_table(self) -> None:
        self.assertEqual(SUPPORTED_PRN_IDS[0], 1)
        self.assertEqual(SUPPORTED_PRN_IDS[-1], 32)
        with self.assertRaises(ValueError):
            generate_ca_code(0)
        with self.assertRaises(ValueError):
            generate_ca_code(33)


if __name__ == "__main__":
    unittest.main()
