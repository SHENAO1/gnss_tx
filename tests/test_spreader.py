"""扩频状态机与基带样本生成相关单元测试。

本模块用于验证：
- 导航比特与 PRN 码的扩频关系是否正确
- 分段输出与一次性输出是否一致
- chip 到 sample 的展开是否遵守边界
- 相关性符号与内部状态推进是否符合 GNSS 扩频链预期
"""

import unittest

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, generate_ca_code
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator


class TestGpsL1CaBpskGenerator(unittest.TestCase):
    """验证单星 PRN 扩频状态机与样本输出行为的测试集合。"""

    def test_first_nav_bit_covers_20_code_epochs(self) -> None:
        """验证首个导航比特持续 20 个 C/A 码周期。

        功能说明：
        - 验证导航比特在 GNSS L1 C/A 中的时长为 `20 ms`。
        - 检查第一个导航比特和第二个导航比特是否分别对应正负两个扩频周期块。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 PRN1 本地码和内部构造的导航模式 `[1, -1]`。

        输出说明：
        - 无返回值。
        - 期望行为是第一个 20 ms 为正码重复，第二个 20 ms 为负码重复。
        """
        # 生成参考 PRN1 本地码，作为扩频结果比较基准。
        code = generate_ca_code(1)
        generator = GpsL1CaBpskGenerator(
            prn_id=1,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1, -1],
        )

        # 生成两个导航比特时长的基带样本，并转换为实部符号序列。
        first_bit = generator.generate_samples(CA_CODE_LENGTH * CA_EPOCHS_PER_NAV_BIT).real.astype(np.int8)
        second_bit = generator.generate_samples(CA_CODE_LENGTH * CA_EPOCHS_PER_NAV_BIT).real.astype(np.int8)

        # 验证导航比特翻转会导致整段扩频结果翻相。
        np.testing.assert_array_equal(first_bit, np.tile(code, CA_EPOCHS_PER_NAV_BIT))
        np.testing.assert_array_equal(second_bit, -np.tile(code, CA_EPOCHS_PER_NAV_BIT))

    def test_split_generation_matches_single_shot(self) -> None:
        """验证分段生成与一次性生成得到相同结果。

        功能说明：
        - 以相同配置分别做单次长序列生成和多次分段生成。
        - 验证扩频状态机在跨调用时的内部状态保持正确。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的两个同参数生成器和固定样本数 `3000`。

        输出说明：
        - 无返回值。
        - 期望行为是分段拼接结果与一次性生成结果逐样本一致。
        """
        sample_count = 3000
        # 单次生成作为参考真值，分段生成用于验证状态连续性。
        single = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=3, amplitude=0.5, nav_pattern=[1, 0, 1])
        split = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=3, amplitude=0.5, nav_pattern=[1, 0, 1])

        expected = single.generate_samples(sample_count)
        # 模拟实际流式输出的分块调用场景。
        actual = np.concatenate(
            [
                split.generate_samples(7),
                split.generate_samples(1001),
                split.generate_samples(2),
                split.generate_samples(sample_count - 1010),
            ]
        )

        # 验证跨多次调用后仍能保持样本连续性。
        np.testing.assert_array_equal(actual, expected)

    def test_non_prn1_generation_matches_reference_code(self) -> None:
        code = generate_ca_code(7)
        generator = GpsL1CaBpskGenerator(
            prn_id=7,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1],
        )

        epoch = generator.generate_samples(CA_CODE_LENGTH).real.astype(np.int8)
        np.testing.assert_array_equal(epoch, code)

    def test_sample_repetition_respects_chip_boundaries(self) -> None:
        """验证 chip 到 sample 的展开不会跨越码片边界。

        功能说明：
        - 当 `samples_per_chip=4` 时，同一个 chip 应重复输出 4 个 sample。
        - 相邻 chip 的 sample 段不应互相混叠。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 PRN1 本地码和内部构造的扩频生成器。

        输出说明：
        - 无返回值。
        - 期望行为是前 8 个 sample 恰好由前 2 个 chip 各重复 4 次组成。
        """
        # 生成参考 PRN1 码，验证 chip 级别到 sample 级别的展开关系。
        code = generate_ca_code(1)
        generator = GpsL1CaBpskGenerator(
            prn_id=1,
            samples_per_chip=4,
            amplitude=1.0,
            nav_pattern=[1],
        )

        # 取前 8 个 sample，覆盖前两个 chip。
        first_eight = generator.generate_samples(8).real.astype(np.int8)
        # 校验每个 chip 被准确重复为 4 个采样点。
        np.testing.assert_array_equal(first_eight[:4], np.full(4, code[0], dtype=np.int8))
        np.testing.assert_array_equal(first_eight[4:], np.full(4, code[1], dtype=np.int8))

    def test_one_epoch_correlation_has_expected_sign(self) -> None:
        """验证一个码周期上的相关结果符号与导航比特一致。

        功能说明：
        - 构造正导航比特和负导航比特两种扩频结果。
        - 与本地 PRN 码做点积相关，验证相关主峰符号。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 PRN1 本地码以及内部构造的两组导航模式。

        输出说明：
        - 无返回值。
        - 期望行为是正导航比特相关值为正峰，负导航比特相关值为负峰。
        """
        # 生成本地 PRN 码，作为相关器参考码。
        code = generate_ca_code(1).astype(np.float32)
        positive = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=1, amplitude=1.0, nav_pattern=[1])
        negative = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=1, amplitude=1.0, nav_pattern=[0])

        # 生成单个 C/A 周期的扩频样本，做相关符号验证。
        pos_epoch = positive.generate_samples(CA_CODE_LENGTH).real.astype(np.float32)
        neg_epoch = negative.generate_samples(CA_CODE_LENGTH).real.astype(np.float32)

        # 点积相关模拟简单捕获器，验证导航比特翻相效果。
        self.assertEqual(int(np.dot(pos_epoch, code)), CA_CODE_LENGTH)
        self.assertEqual(int(np.dot(neg_epoch, code)), -CA_CODE_LENGTH)

    def test_state_advances_after_partial_chip_chunk(self) -> None:
        """验证部分 chip 输出后内部状态推进是否正确。

        功能说明：
        - 先输出不足一个 chip 的样本数，再继续输出剩余样本。
        - 验证 `sample_phase_in_chip` 与 `code_phase` 的状态推进逻辑。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的扩频生成器和固定样本块长度。

        输出说明：
        - 无返回值。
        - 期望行为是 chip 未完成时仅推进 sample 相位，补齐后再推进码相位。
        """
        generator = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=4, amplitude=1.0, nav_pattern=[1, -1])

        # 先生成不足一个 chip 的样本，验证 sample 相位推进。
        generator.generate_samples(3)
        self.assertEqual(generator.state.code_phase, 0)
        self.assertEqual(generator.state.sample_phase_in_chip, 3)

        # 再补齐当前 chip，验证码相位推进到下一个 chip。
        generator.generate_samples(1)
        self.assertEqual(generator.state.code_phase, 1)
        self.assertEqual(generator.state.sample_phase_in_chip, 0)


if __name__ == "__main__":
    unittest.main()
