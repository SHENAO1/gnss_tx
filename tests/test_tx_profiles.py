"""发射配置文件语义相关单元测试。

本模块用于验证：
- 安全基线配置是否保持保守参数
- 可见谱配置是否与当前工程约定一致
"""

import unittest
from pathlib import Path

from gnss_tx.usrp.tx_controller import load_tx_runtime_config


class TestTxProfiles(unittest.TestCase):
    """验证配置文件语义与工程约定一致性的测试集合。"""

    def test_safe_baseline_profile_is_conservative(self) -> None:
        """验证安全基线配置保持低风险起始参数。

        功能说明：
        - 读取 `configs/tx_b210.yaml`。
        - 检查其是否维持低功率安全基线的工程语义。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为仓库内的安全基线配置文件。

        输出说明：
        - 无返回值。
        - 期望行为是 `tx_gain=0.0` 且 `amplitude=0.25`。
        """
        # 读取默认安全基线配置，验证其保持保守参数。
        config = load_tx_runtime_config(Path("configs/tx_b210.yaml"))
        self.assertEqual(config.tx_gain, 0.0)
        self.assertEqual(config.amplitude, 0.25)

    def test_visible_spectrum_profile_matches_checkpoint(self) -> None:
        """验证当前可见谱配置与工程约定值一致。

        功能说明：
        - 读取 `configs/tx_b210_visible_spectrum.yaml`。
        - 检查其是否符合当前仓库约定的扩频模式参数。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为仓库内的可见谱配置文件。

        输出说明：
        - 无返回值。
        - 期望行为是配置文件处于 `spread` 模式，且关键参数与当前文件内容一致。
        """
        # 读取当前可见谱配置，验证其关键参数与仓库状态同步。
        config = load_tx_runtime_config(Path("configs/tx_b210_visible_spectrum.yaml"))
        self.assertEqual(config.tx_gain, 10.0)
        self.assertEqual(config.amplitude, 1.0)
        self.assertEqual(config.signal_mode, "spread")


if __name__ == "__main__":
    unittest.main()
