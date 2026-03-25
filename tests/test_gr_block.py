"""GNU Radio 发送块相关单元测试。

本模块用于验证：
- 自定义 PRN 源块是否输出正确的复基带数据
- GNU Radio 源块与纯 Python 参考状态机是否一致
- replay buffer 是否覆盖完整导航周期并可循环回放
- 顶层流图在启用或关闭 QT 预览时的装配行为
"""

import unittest
import os

import numpy as np
from gnuradio import blocks, gr
from PyQt5 import QtWidgets

from gnss_tx.gr.top_block import (
    GpsL1CaSourceBlock,
    GpsL1CaTxTopBlock,
    TxBlockConfig,
    build_replay_samples,
    make_gps_l1_ca_vector_source,
)
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator


class TestGpsL1CaSourceBlock(unittest.TestCase):
    """验证 GNU Radio PRN 源块与顶层流图行为的测试集合。"""

    @classmethod
    def setUpClass(cls) -> None:
        """初始化 QT 运行环境，确保图形相关测试可在无头环境执行。

        功能说明：
        - 配置 `QT_QPA_PLATFORM=offscreen`，避免测试依赖真实显示设备。
        - 初始化 `QApplication`，供 QT sink 相关测试复用。

        输入参数说明：
        - `cls`：测试类对象，由 `unittest` 框架提供。

        输出说明：
        - 无返回值。
        - 期望行为是后续 QT 预览相关测试具备基础运行环境。
        """
        # 使用离屏模式执行 QT 预览测试，避免依赖桌面环境。
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_block_outputs_complex64_samples(self) -> None:
        """验证 GNU Radio 源块输出类型和复基带格式。

        功能说明：
        - 检查 `GpsL1CaSourceBlock` 是否输出 `complex64` 类型样本。
        - 验证当前 BPSK 基带仅使用 I 支路，Q 支路应为零。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的 `GpsL1CaSourceBlock` 和输出缓冲区。

        输出说明：
        - 无返回值。
        - 期望行为是输出长度正确、类型为 `complex64`、且结果为纯实数复基带。
        """
        # 构造 PRN1 扩频源块，输入测试导航比特模式。
        block = GpsL1CaSourceBlock(prn_id=1, samples_per_chip=2, amplitude=0.25, nav_pattern=[1, -1])
        # 申请 GNU Radio 输出缓冲区，模拟 block.work() 输出。
        output = np.empty(17, dtype=np.complex64)

        # 调用 GNU Radio 同步块工作函数生成复基带样本。
        produced = block.work([], [output])

        # 校验输出样本数量、数据类型及 I/Q 形式。
        self.assertEqual(produced, 17)
        self.assertEqual(output.dtype, np.complex64)
        self.assertTrue(np.all(np.isreal(output)))

    def test_block_uses_same_state_machine_as_reference_generator(self) -> None:
        """验证 GNU Radio 源块与纯 Python 参考状态机一致。

        功能说明：
        - 使用同一组 PRN、导航比特和采样参数构造参考生成器与 GNU Radio 源块。
        - 比较分段输出与单次输出是否完全一致。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的 `GpsL1CaBpskGenerator` 与 `GpsL1CaSourceBlock`。

        输出说明：
        - 无返回值。
        - 期望行为是两条路径产生完全相同的样本序列。
        """
        # 纯 Python 生成器作为参考真值，验证 GNU Radio block 的状态机一致性。
        reference = GpsL1CaBpskGenerator(
            prn_id=1,
            samples_per_chip=2,
            amplitude=0.75,
            nav_pattern=[1, 0, 1],
        )
        block = GpsL1CaSourceBlock(
            prn_id=1,
            samples_per_chip=2,
            amplitude=0.75,
            nav_pattern=[1, 0, 1],
        )

        # 单次生成整段参考样本。
        expected = reference.generate_samples(64)
        out_a = np.empty(7, dtype=np.complex64)
        out_b = np.empty(57, dtype=np.complex64)

        # 分两次驱动 block.work()，验证跨调用状态连续性。
        block.work([], [out_a])
        block.work([], [out_b])
        actual = np.concatenate([out_a, out_b])

        # 校验 GNU Radio block 输出与参考状态机完全一致。
        np.testing.assert_array_equal(actual, expected)

    def test_replay_samples_cover_full_nav_pattern_period(self) -> None:
        """验证 replay buffer 覆盖完整导航比特周期。

        功能说明：
        - 检查预生成 replay 样本是否覆盖完整 nav pattern 周期。
        - 验证 replay 长度是否满足 `导航比特数 × 20 ms × 1023 chip × samples_per_chip`。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `build_replay_samples()` 生成的复基带样本。

        输出说明：
        - 无返回值。
        - 期望行为是 replay 长度正确，且数据类型为 `complex64`。
        """
        # 生成完整导航模式周期对应的扩频 replay 基带。
        replay = build_replay_samples(
            prn_id=1,
            samples_per_chip=2,
            amplitude=0.5,
            nav_pattern=[1, 0, 1],
        )
        expected_len = 3 * 20 * 1023 * 2
        # 校验完整导航周期长度和复基带数据类型。
        self.assertEqual(len(replay), expected_len)
        self.assertEqual(replay.dtype, np.complex64)

    def test_non_prn1_replay_samples_match_reference_generator(self) -> None:
        replay = build_replay_samples(
            prn_id=7,
            samples_per_chip=2,
            amplitude=0.5,
            nav_pattern=[1, -1],
        )
        reference = GpsL1CaBpskGenerator(
            prn_id=7,
            samples_per_chip=2,
            amplitude=0.5,
            nav_pattern=[1, -1],
        ).generate_samples(len(replay))
        np.testing.assert_array_equal(replay, reference)

    def test_vector_source_repeats_replay_buffer(self) -> None:
        """验证 GNU Radio vector source 会循环回放 replay buffer。

        功能说明：
        - 构造参考 replay 样本和 GNU Radio `vector_source_c`。
        - 通过 `head` 截取超出一轮 replay 的长度，验证循环回放行为。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为 `build_replay_samples()` 与 `make_gps_l1_ca_vector_source()`。

        输出说明：
        - 无返回值。
        - 期望行为是输出等于参考 replay 样本按周期平铺后的前缀。
        """
        # 生成参考 replay 缓冲区。
        reference = build_replay_samples(
            prn_id=1,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1, -1],
        )
        # 生成 GNU Radio vector source，模拟连续回放。
        source = make_gps_l1_ca_vector_source(
            prn_id=1,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1, -1],
        )
        tb = gr.top_block()
        # 使用 head 限制输出长度，验证跨周期回放拼接是否正确。
        head = blocks.head(gr.sizeof_gr_complex, len(reference) + 16)
        sink = blocks.vector_sink_c()
        tb.connect(source, head, sink)
        tb.run()

        combined = np.array(sink.data(), dtype=np.complex64)
        tiled = np.tile(reference, 2)
        # 校验 replay 缓冲区按周期重复，无边界截断问题。
        np.testing.assert_array_equal(combined, tiled[: len(reference) + 16])

    def test_tx_top_block_without_qt_preview_builds_without_preview_widgets(self) -> None:
        """验证关闭 QT 预览时顶层流图不会创建预览窗口。

        功能说明：
        - 构造关闭 QT 预览的顶层发送流图。
        - 验证不会创建额外的 QT 预览窗口对象。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的 `TxBlockConfig(enable_qt_preview=False)`。

        输出说明：
        - 无返回值。
        - 期望行为是 `preview_window` 为 `None`。
        """
        # 构造不启用 QT 预览的顶层发送流图。
        tb = GpsL1CaTxTopBlock(
            TxBlockConfig(
                signal_mode="spread",
                samples_per_chip=1,
                sample_rate=1.023e6,
                enable_qt_preview=False,
            ),
            sink_block=None,
        )
        self.assertIsNone(tb.preview_window)

    def test_tx_top_block_with_qt_preview_constructs_preview_widgets(self) -> None:
        """验证启用 QT 预览时顶层流图会创建时域和频域预览。

        功能说明：
        - 构造启用 QT 预览的顶层发送流图。
        - 验证时域 sink、频域 sink 和窗口对象均被创建。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的 `TxBlockConfig(enable_qt_preview=True)`。

        输出说明：
        - 无返回值。
        - 期望行为是 QT 相关对象均非空。
        """
        # 构造启用 QT 预览的顶层发送流图，验证 GUI 装配逻辑。
        tb = GpsL1CaTxTopBlock(
            TxBlockConfig(
                signal_mode="spread",
                samples_per_chip=1,
                sample_rate=1.023e6,
                enable_qt_preview=True,
            ),
            sink_block=None,
        )
        # 校验时域和频域预览控件都被正确创建。
        self.assertIsNotNone(tb.preview_window)
        self.assertIsNotNone(tb.qt_time_sink)
        self.assertIsNotNone(tb.qt_freq_sink)


if __name__ == "__main__":
    unittest.main()
