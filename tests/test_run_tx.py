"""运行脚本 dry-run 行为相关单元测试。

本模块用于验证：
- `run_tx.py` 在 dry-run 模式下能否正确装载配置并打印摘要
- QT 预览开关是否会反映到终端输出字段
- 运行时摘要中的频率与观测字段是否符合预期
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from scripts import run_tx
from gnss_tx.usrp import TxRuntimeConfig, build_tx_truth_payload


class TestRunTxScript(unittest.TestCase):
    """验证发送脚本 dry-run 输出行为的测试集合。"""

    def test_dry_run_with_qt_preview_prints_renamed_summary_fields(self) -> None:
        """验证 dry-run + QT 预览时的终端摘要字段。

        功能说明：
        - 模拟命令行执行 `run_tx.py --dry-run --qt-preview`。
        - 验证运行时配置和实验摘要是否包含关键字段。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为内部构造的命令行参数以及 mock 的 UHD 设备发现输出。

        输出说明：
        - 无返回值。
        - 期望行为是脚本返回码为 `0`，并打印 QT 预览与频率摘要信息。
        """
        # 模拟用户从命令行触发 dry-run，并启用 QT 预览。
        argv = [
            "run_tx.py",
            "--config",
            "configs/tx_b210_visible_spectrum.yaml",
            "--dry-run",
            "--qt-preview",
        ]

        # mock 设备探测输出，避免测试依赖真实 USRP 硬件。
        with mock.patch("sys.argv", argv):
            with mock.patch.object(run_tx, "uhd_find_devices_output", return_value="serial: 193982"):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    # 执行脚本主入口，捕获终端输出。
                    exit_code = run_tx.main()

        output = buffer.getvalue()
        # 验证 dry-run 模式下关键实验摘要字段都已输出。
        self.assertEqual(exit_code, 0)
        self.assertIn("enable_qt_preview=True", output)
        self.assertIn("GNU Radio流图=QT 预览开启", output)
        self.assertIn("GNU Radio频谱=QT 频谱预览开启", output)
        self.assertIn("射频中心频率=100000000.0", output)
        self.assertIn("信号观测频率=100000000.0", output)
        self.assertIn("基带偏移频率=0.0", output)

    def test_dry_run_accepts_prn_override_and_reports_selected_prn(self) -> None:
        argv = [
            "run_tx.py",
            "--config",
            "configs/tx_b210_visible_spectrum.yaml",
            "--prn-id",
            "7",
            "--dry-run",
        ]

        with mock.patch("sys.argv", argv):
            with mock.patch.object(run_tx, "uhd_find_devices_output", return_value="serial: 193982"):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = run_tx.main()

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("prn_id=7", output)
        self.assertIn("生成方式=PRN7 C/A 扩频缓冲回放", output)

    def test_dry_run_can_export_truth_json_with_effective_runtime_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            truth_path = Path(tmpdir) / "tx_truth.json"
            argv = [
                "run_tx.py",
                "--config",
                "configs/tx_b210_visible_spectrum.yaml",
                "--dry-run",
                "--export-truth-json",
                str(truth_path),
            ]

            with mock.patch("sys.argv", argv):
                with mock.patch.object(run_tx, "uhd_find_devices_output", return_value="serial: 193982"):
                    buffer = io.StringIO()
                    with redirect_stdout(buffer):
                        exit_code = run_tx.main()

            output = buffer.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertTrue(truth_path.exists())
            payload = json.loads(truth_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["nav_bits_pattern_pm1"], [1, -1, 1, 1, -1, -1, 1, -1])
            self.assertEqual(payload["nav_bits_pattern_01"], [1, 0, 1, 1, 0, 0, 1, 0])
            self.assertEqual(payload["initial_nav_bit_index"], 0)
            self.assertEqual(payload["initial_nav_epoch"], 0)
            self.assertIn("Exported TX truth JSON", output)

    def test_build_tx_truth_payload_preserves_non_default_initial_offsets(self) -> None:
        payload = build_tx_truth_payload(
            TxRuntimeConfig(
                prn_id=7,
                nav_pattern="1 0 1 1 0 0 1 0",
                sample_rate=4.092e6,
                samples_per_chip=4,
                initial_code_phase=17,
                initial_nav_epoch=5,
                initial_nav_bit_index=3,
            )
        )

        self.assertEqual(payload["prn_id"], 7)
        self.assertEqual(payload["initial_code_phase"], 17)
        self.assertEqual(payload["initial_nav_epoch"], 5)
        self.assertEqual(payload["initial_nav_bit_index"], 3)
        self.assertEqual(payload["epochs_per_bit"], 20)
        self.assertEqual(payload["nav_bits_pattern_pm1"], [1, -1, 1, 1, -1, -1, 1, -1])


if __name__ == "__main__":
    unittest.main()
