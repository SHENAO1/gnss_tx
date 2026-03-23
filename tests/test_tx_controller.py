"""发送控制层与配置装载相关单元测试。

本模块用于验证：
- YAML 配置装载后的派生参数行为
- 运行时参数覆盖逻辑
- 终端配置摘要、实验摘要与观察清单的输出字段
- spread / tone 两种模式下的参数校验规则
"""

import tempfile
import unittest
from pathlib import Path

from gnss_tx.usrp.tx_controller import (
    GPS_CA_CHIP_RATE,
    TxRuntimeConfig,
    apply_overrides,
    format_config_report,
    format_lab_table_summary,
    format_observation_checklist,
    load_tx_runtime_config,
)


class TestTxController(unittest.TestCase):
    """验证发送控制层配置、摘要和校验逻辑的测试集合。"""

    def test_load_tx_runtime_config_derives_bandwidth(self) -> None:
        """验证配置装载时可自动派生带宽参数。

        功能说明：
        - 构造一个不显式写出 `bandwidth` 的临时 YAML 配置。
        - 验证 `load_tx_runtime_config()` 会根据采样率自动补齐带宽。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为测试内部写入的临时 YAML 文件。

        输出说明：
        - 无返回值。
        - 期望行为是装载后 `bandwidth` 等于 `sample_rate`，并保留原始 `samples_per_chip`。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tx.yaml"
            # 构造最小运行时配置，模拟实验配置文件来源。
            path.write_text(
                "\n".join(
                    [
                        "prn_id: 1",
                        "usrp_addr: \"type=b200\"",
                        "center_freq: 100000000.0",
                        "samples_per_chip: 4",
                        "sample_rate: 4092000.0",
                        "tx_gain: 0.0",
                        "amplitude: 0.25",
                        "antenna: \"TX/RX\"",
                        "nav_pattern: \"1 0 1 1 0 0 1 0\"",
                        "continuous: true",
                    ]
                ),
                encoding="utf-8",
            )

            # 装载配置并验证派生字段是否自动补齐。
            config = load_tx_runtime_config(path)

        self.assertEqual(config.bandwidth, 4092000.0)
        self.assertEqual(config.samples_per_chip, 4)

    def test_apply_overrides_updates_sample_rate_from_samples_per_chip(self) -> None:
        """验证覆盖 `samples_per_chip` 时采样率会同步更新。

        功能说明：
        - 基于默认运行时配置施加 `samples_per_chip=8` 覆盖。
        - 验证 chip 速率到采样率的派生关系仍然成立。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `TxRuntimeConfig()` 默认配置与覆盖参数。

        输出说明：
        - 无返回值。
        - 期望行为是 `sample_rate` 与 `bandwidth` 同步更新为 `1.023e6 * 8`。
        """
        config = TxRuntimeConfig().validate()

        # 通过运行时覆盖模拟用户修改采样展开倍数。
        updated = apply_overrides(config, samples_per_chip=8)

        self.assertEqual(updated.sample_rate, GPS_CA_CHIP_RATE * 8)
        self.assertEqual(updated.bandwidth, GPS_CA_CHIP_RATE * 8)

    def test_report_contains_safety_text(self) -> None:
        """验证配置摘要中包含实验安全提示。

        功能说明：
        - 生成运行时配置摘要字符串。
        - 检查其中是否包含频谱仪输入限制和安全提醒字段。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为默认运行时配置。

        输出说明：
        - 无返回值。
        - 期望行为是报告文本包含安全相关提示。
        """
        report = format_config_report(TxRuntimeConfig().validate())
        self.assertIn("Spectrum analyzer max input", report)
        self.assertIn("Safety reminder", report)

    def test_observation_checklist_mentions_frequency_and_span(self) -> None:
        """验证观察清单中包含核心频率与频谱设置提示。

        功能说明：
        - 生成频谱仪观察清单。
        - 检查清单中是否包含中心频率、Span 和发射端口等关键信息。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为默认运行时配置。

        输出说明：
        - 无返回值。
        - 期望行为是清单文本包含实验观察所需的关键参数提示。
        """
        checklist = format_observation_checklist(TxRuntimeConfig().validate())
        self.assertIn("100.000 MHz", checklist)
        self.assertIn("20 MHz", checklist)
        self.assertIn("TX/RX", checklist)

    def test_lab_table_summary_contains_serial_and_generation_mode(self) -> None:
        """验证实验摘要中包含设备序列号和扩频生成方式。

        功能说明：
        - 构造扩频模式配置并注入 mock 的 UHD 设备信息。
        - 验证实验表格摘要是否输出 serial、生成方式和关键实验字段。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的扩频模式配置和设备信息字符串。

        输出说明：
        - 无返回值。
        - 期望行为是摘要文本包含实验记录所需的关键字段。
        """
        config = TxRuntimeConfig(tx_gain=10.0, amplitude=0.5).validate()
        summary = format_lab_table_summary(
            config,
            "Device Address:\n    serial: 193982\n    type: b200\n",
        )
        self.assertIn("实验表格参数摘要", summary)
        self.assertIn("GNU Radio流图=不输出", summary)
        self.assertIn("serial=193982", summary)
        self.assertIn("生成方式=PRN1 C/A 扩频缓冲回放", summary)
        self.assertIn("幅度=0.5", summary)
        self.assertIn("射频中心频率=100000000.0", summary)
        self.assertIn("信号观测频率=100000000.0", summary)
        self.assertIn("基带偏移频率=0.0", summary)

    def test_lab_table_summary_reports_tone_offset_frequency(self) -> None:
        """验证单音模式摘要会正确报告观测频率与基带频偏。

        功能说明：
        - 构造单音模式发送配置。
        - 检查实验摘要中是否体现 tone 模式的观测频率和基带偏移。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的 tone 模式配置。

        输出说明：
        - 无返回值。
        - 期望行为是摘要文本正确显示 tone 偏移后的 RF 观测频率。
        """
        config = TxRuntimeConfig(
            signal_mode="tone",
            center_freq=100_000_000.0,
            sample_rate=4_092_000.0,
            tone_offset_hz=500_000.0,
            tx_gain=6.0,
            amplitude=0.5,
        ).validate()

        summary = format_lab_table_summary(config)

        # 验证 tone 模式下的偏移频率和观测频率字段。
        self.assertIn("生成方式=单音缓冲回放", summary)
        self.assertIn("基带偏移频率=500000.0", summary)
        self.assertIn("信号观测频率=100500000.0", summary)

    def test_lab_table_summary_marks_qt_preview_when_enabled(self) -> None:
        """验证启用 QT 预览时实验摘要会标记 GUI 输出状态。

        功能说明：
        - 构造启用 QT 预览的运行时配置。
        - 检查实验摘要中 GNU Radio 流图和频谱字段是否标记为预览开启。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `enable_qt_preview=True` 的配置对象。

        输出说明：
        - 无返回值。
        - 期望行为是摘要文本中显示 QT 预览已启用。
        """
        config = TxRuntimeConfig(enable_qt_preview=True).validate()

        summary = format_lab_table_summary(config)

        self.assertIn("GNU Radio流图=QT 预览开启", summary)
        self.assertIn("GNU Radio频谱=QT 频谱预览开启", summary)

    def test_tone_mode_accepts_non_chip_rate_sample_rate(self) -> None:
        """验证单音模式允许非 chip-rate 对齐采样率。

        功能说明：
        - 构造 tone 模式配置，使用不等于 `1.023e6 * samples_per_chip` 的采样率。
        - 验证 tone 模式不会受扩频模式的 chip-rate 约束。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的 tone 模式配置。

        输出说明：
        - 无返回值。
        - 期望行为是配置校验通过，模式保持为 `tone`。
        """
        config = TxRuntimeConfig(
            signal_mode="tone",
            sample_rate=2_000_000.0,
            samples_per_chip=4,
            tone_offset_hz=250_000.0,
        ).validate()
        self.assertEqual(config.signal_mode, "tone")

    def test_spread_mode_still_requires_chip_rate_sample_rate(self) -> None:
        """验证扩频模式仍要求采样率与 chip-rate 对齐。

        功能说明：
        - 构造 spread 模式配置，并故意设置不匹配的采样率。
        - 验证扩频模式下会抛出参数校验异常。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的非法 spread 模式配置。

        输出说明：
        - 无返回值。
        - 期望行为是抛出 `ValueError`。
        """
        # 扩频模式要求 sample_rate 与 PRN chip 速率严格匹配。
        with self.assertRaises(ValueError):
            TxRuntimeConfig(signal_mode="spread", sample_rate=2_000_000.0).validate()


if __name__ == "__main__":
    unittest.main()
