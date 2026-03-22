import tempfile
import unittest
from pathlib import Path

from scripts.plan_tx_visibility_sweep import write_checklist, write_draft, write_template_csv


class TestSweepPlanner(unittest.TestCase):
    def test_write_template_csv_creates_chinese_headers(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "template.csv"
            write_template_csv(path, Path("configs/tx_b210_visible_spectrum.yaml"))
            text = path.read_text(encoding="utf-8")

        self.assertIn("发送信号类型", text)
        self.assertIn("serial", text)
        self.assertIn("生成方式", text)

    def test_write_checklist_creates_markdown_checkboxes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checklist.md"
            write_checklist(path, Path("configs/tx_b210_visible_spectrum.yaml"))
            text = path.read_text(encoding="utf-8")

        self.assertIn("# PRN1 发射参数试验清单", text)
        self.assertIn("- [ ]", text)
        self.assertIn("基准确认：先确认当天已知可见组合", text)
        self.assertIn("阶段1：先扫 tx_gain（固定 amplitude = 0.50，顺序 10→8→6）", text)
        self.assertIn("阶段2：再扫 amplitude（固定阶段1选出的最小稳定 tx_gain", text)
        self.assertIn("amplitude=0.50", text)
        self.assertIn("--duration 20", text)

    def test_write_draft_uses_visible_profile_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft.md"
            write_draft(path, Path("configs/tx_b210_visible_spectrum.yaml"))
            text = path.read_text(encoding="utf-8")

        self.assertIn("PRN1 发射参数试验记录草稿", text)
        self.assertIn("100000000.0", text)
        self.assertIn("4092000.0", text)
        self.assertIn("基准确认：先用 `tx_gain = 10`、`amplitude = 0.50`", text)
        self.assertIn("实验表格参数摘要", text)
        self.assertIn("稳定性", text)


if __name__ == "__main__":
    unittest.main()
