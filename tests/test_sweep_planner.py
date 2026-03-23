"""实验扫描模板生成相关单元测试。

本模块用于验证：
- sweep CSV 模板是否包含实验表格关键字段
- checklist 是否生成现场可勾选的执行项
- draft 是否基于当前配置生成正确的实验草稿文本
"""

import tempfile
import unittest
from pathlib import Path

from scripts.plan_tx_visibility_sweep import write_checklist, write_draft, write_template_csv


class TestSweepPlanner(unittest.TestCase):
    """验证实验扫描辅助脚本输出内容的测试集合。"""

    def test_write_template_csv_creates_chinese_headers(self) -> None:
        """验证 CSV 模板包含中文表头和关键实验字段。

        功能说明：
        - 调用模板生成函数写出 CSV。
        - 检查实验表格字段名是否完整，便于后续人工记录。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为临时目录和 `configs/tx_b210_visible_spectrum.yaml`。

        输出说明：
        - 无返回值。
        - 期望行为是 CSV 中包含中文表头、`serial` 和 `生成方式` 等关键列。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "template.csv"
            # 生成实验 sweep CSV 模板，用于现场结果回填。
            write_template_csv(path, Path("configs/tx_b210_visible_spectrum.yaml"))
            text = path.read_text(encoding="utf-8")

        self.assertIn("发送信号类型", text)
        self.assertIn("serial", text)
        self.assertIn("生成方式", text)

    def test_write_checklist_creates_markdown_checkboxes(self) -> None:
        """验证 checklist 文档包含 Markdown 勾选项与实验阶段说明。

        功能说明：
        - 生成实验执行 checklist。
        - 检查是否包含勾选框、阶段标题和典型运行命令。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为临时目录和 `configs/tx_b210_visible_spectrum.yaml`。

        输出说明：
        - 无返回值。
        - 期望行为是生成适合现场执行的 Markdown 清单文本。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "checklist.md"
            # 生成现场勾选清单，验证实验流程说明完整性。
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
        """验证实验草稿默认继承可见谱配置中的关键参数。

        功能说明：
        - 生成实验记录草稿文档。
        - 验证草稿中是否包含频率、采样率、基准确认组合和摘要字段。

        输入参数说明：
        - 无显式输入参数。
        - 测试数据来源为临时目录和 `configs/tx_b210_visible_spectrum.yaml`。

        输出说明：
        - 无返回值。
        - 期望行为是草稿包含当前实验的默认配置与回填说明。
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "draft.md"
            # 生成实验草稿，验证其能反映当前配置默认值。
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
