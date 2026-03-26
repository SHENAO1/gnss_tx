"""多星叠加信号合成模块单元测试。

本模块用于验证：
- build_multi_sat_replay_samples 生成的缓冲区长度与单星相同
- 单 PRN 列表模式下功率等效单星
- 32 颗星叠加后最大幅度在合理范围内（功率归一化有效）
- TxBlockConfig 新增的 all_prns / prn_ids 字段向后兼容
"""

import unittest

import numpy as np

from gnss_tx.gr.top_block import TxBlockConfig, build_replay_samples
from gnss_tx.signal.multi_sat_combiner import build_multi_sat_replay_samples


class TestBuildMultiSatReplaySamples(unittest.TestCase):
    """验证 build_multi_sat_replay_samples 的输出行为。"""

    def test_buffer_length_matches_single_sat(self) -> None:
        """叠加缓冲区长度应与单星 replay buffer 相同。"""
        single = build_replay_samples(prn_id=1, samples_per_chip=4, amplitude=1.0)
        multi = build_multi_sat_replay_samples(
            prn_ids=[1], samples_per_chip=4, normalize=False
        )
        self.assertEqual(len(multi), len(single))

    def test_output_dtype_is_complex64(self) -> None:
        """输出必须是 complex64 类型。"""
        buf = build_multi_sat_replay_samples(prn_ids=[1, 2], samples_per_chip=1)
        self.assertEqual(buf.dtype, np.complex64)

    def test_single_prn_list_amplitude_matches_single_sat(self) -> None:
        """单颗星列表（无归一化）与 build_replay_samples 幅度完全一致。"""
        single = build_replay_samples(
            prn_id=3, samples_per_chip=2, amplitude=1.0, nav_pattern=[1, -1]
        )
        multi = build_multi_sat_replay_samples(
            prn_ids=[3], samples_per_chip=2, nav_pattern=[1, -1], normalize=False
        )
        np.testing.assert_array_almost_equal(np.abs(multi), np.abs(single), decimal=6)

    def test_32prn_combined_max_amplitude_within_expected_range(self) -> None:
        """32 颗星叠加后 sqrt(32) 归一化，最大幅度应在理论上限内。

        功率归一化使用 sqrt(N)，平均功率等效于单星。
        峰值幅度理论上限为 sqrt(N)（全部 32 颗码片同相时），约 5.657。
        C/A 码接近正交但并不完全正交，允许少量偏差，故上限设为 sqrt(32) + 0.01。
        """
        buf = build_multi_sat_replay_samples(samples_per_chip=1)
        max_amp = float(np.max(np.abs(buf)))
        upper_bound = np.sqrt(32) + 0.01
        self.assertLessEqual(
            max_amp, upper_bound,
            msg=f"32星叠加最大幅度 {max_amp:.4f} 超出理论上限 {upper_bound:.4f}"
        )

    def test_32prn_combined_mean_power_close_to_single_sat(self) -> None:
        """32 颗星叠加功率归一化后，平均功率应接近单星（误差 < 10%）。"""
        single = build_replay_samples(prn_id=1, samples_per_chip=1, amplitude=1.0)
        multi32 = build_multi_sat_replay_samples(samples_per_chip=1)

        single_power = float(np.mean(np.abs(single) ** 2))
        multi_power = float(np.mean(np.abs(multi32) ** 2))

        self.assertAlmostEqual(
            multi_power, single_power, delta=single_power * 0.1,
            msg=f"32星叠加平均功率 {multi_power:.4f} 与单星 {single_power:.4f} 相差超过 10%"
        )

    def test_none_prn_ids_uses_all_32(self) -> None:
        """prn_ids=None 时默认使用全部 32 颗 PRN，缓冲区长度应与 prn_ids=list(1..32) 相同。"""
        buf_none = build_multi_sat_replay_samples(prn_ids=None, samples_per_chip=1)
        buf_explicit = build_multi_sat_replay_samples(
            prn_ids=list(range(1, 33)), samples_per_chip=1
        )
        np.testing.assert_array_equal(buf_none, buf_explicit)

    def test_normalize_false_produces_larger_amplitude(self) -> None:
        """normalize=False 时叠加幅度应大于 normalize=True（不做功率归一化）。"""
        buf_norm = build_multi_sat_replay_samples(
            prn_ids=list(range(1, 5)), samples_per_chip=1, normalize=True
        )
        buf_raw = build_multi_sat_replay_samples(
            prn_ids=list(range(1, 5)), samples_per_chip=1, normalize=False
        )
        self.assertGreater(
            float(np.max(np.abs(buf_raw))),
            float(np.max(np.abs(buf_norm))),
        )


class TestTxBlockConfigAllPrns(unittest.TestCase):
    """验证 TxBlockConfig 新字段的向后兼容性。"""

    def test_default_config_has_all_prns_false(self) -> None:
        """默认 TxBlockConfig 的 all_prns 应为 False，保持向后兼容。"""
        config = TxBlockConfig()
        self.assertFalse(config.all_prns)

    def test_default_config_has_prn_ids_none(self) -> None:
        """默认 TxBlockConfig 的 prn_ids 应为 None，保持向后兼容。"""
        config = TxBlockConfig()
        self.assertIsNone(config.prn_ids)

    def test_all_prns_true_config_instantiates(self) -> None:
        """all_prns=True 的配置应能正常实例化。"""
        config = TxBlockConfig(all_prns=True)
        self.assertTrue(config.all_prns)
        self.assertIsNone(config.prn_ids)

    def test_prn_ids_subset_config_instantiates(self) -> None:
        """prn_ids 指定子集时应能正常实例化。"""
        config = TxBlockConfig(prn_ids=[1, 3, 7, 15])
        self.assertFalse(config.all_prns)
        self.assertEqual(config.prn_ids, [1, 3, 7, 15])


if __name__ == "__main__":
    unittest.main()
