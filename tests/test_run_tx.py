import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from scripts import run_tx


class TestRunTxScript(unittest.TestCase):
    def test_dry_run_with_qt_preview_prints_renamed_summary_fields(self) -> None:
        argv = [
            "run_tx.py",
            "--config",
            "configs/tx_b210_visible_spectrum.yaml",
            "--dry-run",
            "--qt-preview",
        ]

        with mock.patch("sys.argv", argv):
            with mock.patch.object(run_tx, "uhd_find_devices_output", return_value="serial: 193982"):
                buffer = io.StringIO()
                with redirect_stdout(buffer):
                    exit_code = run_tx.main()

        output = buffer.getvalue()
        self.assertEqual(exit_code, 0)
        self.assertIn("enable_qt_preview=True", output)
        self.assertIn("GNU Radio流图=QT 预览开启", output)
        self.assertIn("GNU Radio频谱=QT 频谱预览开启", output)
        self.assertIn("射频中心频率=100000000.0", output)
        self.assertIn("信号观测频率=100000000.0", output)
        self.assertIn("基带偏移频率=0.0", output)


if __name__ == "__main__":
    unittest.main()
