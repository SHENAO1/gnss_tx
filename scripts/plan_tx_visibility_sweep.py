from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from gnss_tx.usrp.tx_controller import load_tx_runtime_config


DEFAULT_BASELINE_TX_GAIN = 10.0
DEFAULT_BASELINE_AMPLITUDE = 0.50
DEFAULT_STAGE1_TX_GAINS = (10.0, 8.0, 6.0)
DEFAULT_STAGE2_AMPLITUDES = (0.50, 0.40, 0.30)
DEFAULT_DURATION_S = 20.0
DEFAULT_REF_LEVEL_DBM = -66.0
DEFAULT_ATT_DB = 10.0
DEFAULT_RBW_HZ = 1_000.0
DEFAULT_VBW_HZ = 1_000.0
DEFAULT_SPAN_HZ = 5_000_000.0


@dataclass(frozen=True)
class SweepCase:
    stage: str
    step_label: str
    tx_gain: float
    amplitude: float
    note: str = ""


def build_baseline_case() -> SweepCase:
    return SweepCase(
        stage="基准确认",
        step_label="当天基准点",
        tx_gain=DEFAULT_BASELINE_TX_GAIN,
        amplitude=DEFAULT_BASELINE_AMPLITUDE,
        note="先确认已知可见组合在当天仍稳定可见；若这一步不稳定，先排查连线、频谱仪设置、underflow 和软件侧预览。",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="生成单星可选 PRN 的可见谱参数扫描模板、勾选清单和实验记录草稿。")
    parser.add_argument(
        "--config",
        default="configs/tx_b210_visible_spectrum.yaml",
        help="用于生成默认实验参数的配置文件路径。",
    )
    parser.add_argument(
        "--csv-output",
        default=None,
        help="CSV 模板输出路径。默认按当天日期生成到 experiments/records/YYYY-MM-DD/tx_visibility_sweep/。",
    )
    parser.add_argument(
        "--checklist-output",
        default=None,
        help="Markdown 勾选清单输出路径。默认按当天日期生成到 experiments/records/YYYY-MM-DD/tx_visibility_sweep/。",
    )
    parser.add_argument(
        "--draft-output",
        default=None,
        help="实验记录草稿输出路径。默认按当天日期生成到 experiments/records/YYYY-MM-DD/tx_visibility_sweep/。",
    )
    return parser


def spread_generation_label(prn_id: int) -> str:
    return f"PRN{prn_id} C/A 扩频缓冲回放"


def build_stage1_cases() -> list[SweepCase]:
    return [
        SweepCase(
            stage="阶段1",
            step_label="先扫 tx_gain",
            tx_gain=tx_gain,
            amplitude=DEFAULT_BASELINE_AMPLITUDE,
            note="固定 amplitude=0.50，按 10→8→6 的顺序寻找最低稳定可见的 tx_gain。",
        )
        for tx_gain in DEFAULT_STAGE1_TX_GAINS
    ]


def build_stage2_cases(selected_gain: str = "<阶段1选出的最小稳定tx_gain>") -> list[dict[str, str]]:
    return [
        {
            "stage": "阶段2",
            "step_label": "再扫 amplitude",
            "tx_gain": selected_gain,
            "amplitude": f"{amplitude:.2f}",
            "note": "固定阶段1选出的最小稳定 tx_gain，按 0.50→0.40→0.30 的顺序寻找最低稳定可见的 amplitude。",
        }
        for amplitude in DEFAULT_STAGE2_AMPLITUDES
    ]


def build_stage3_cases(
    selected_gain: str = "<最终tx_gain>",
    selected_amplitude: str = "<最终amplitude>",
) -> list[dict[str, str]]:
    return [
        {
            "stage": "阶段3",
            "step_label": f"重复性验证 #{index}",
            "tx_gain": selected_gain,
            "amplitude": selected_amplitude,
            "note": "重复运行 3 次，每次 20 s，确认谱形稳定且可重复。",
        }
        for index in range(1, 4)
    ]


def write_template_csv(output_path: Path, config_path: Path) -> None:
    config = load_tx_runtime_config(config_path)
    generation_label = spread_generation_label(config.prn_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "阶段",
                "步骤",
                "发送信号类型",
                "GNU Radio流图",
                "GNU Radio频谱",
                "频谱仪结果",
                "采样率",
                "射频中心频率",
                "发射增益",
                "带宽",
                "serial",
                "信号观测频率",
                "基带偏移频率",
                "幅度",
                "是否归一化",
                "是否直流偏置",
                "生成方式",
                "Span",
                "RBW",
                "VBW",
                "Att",
                "Ref Level",
                "频谱仪结果",
                "稳定性",
                "截图文件",
                "备注",
            ]
        )
        baseline = build_baseline_case()
        writer.writerow(
            [
                baseline.stage,
                baseline.step_label,
                "扩频",
                "按需启用 --qt-preview",
                "按需启用 --qt-preview",
                "手工填写",
                f"{config.sample_rate}",
                f"{config.center_freq}",
                f"{baseline.tx_gain:.0f}",
                f"{config.bandwidth}",
                "运行时填写",
                f"{config.center_freq}",
                "0.0",
                f"{baseline.amplitude:.2f}",
                "是",
                "否",
                generation_label,
                f"{DEFAULT_SPAN_HZ}",
                f"{DEFAULT_RBW_HZ}",
                f"{DEFAULT_VBW_HZ}",
                f"{DEFAULT_ATT_DB}",
                f"{DEFAULT_REF_LEVEL_DBM}",
                "明显可见 / 勉强可见 / 不可见",
                "稳定 / 边缘 / 不稳定",
                "",
                baseline.note,
            ]
        )
        for case in build_stage1_cases():
            writer.writerow(
                [
                    case.stage,
                    case.step_label,
                    "扩频",
                    "按需启用 --qt-preview",
                    "按需启用 --qt-preview",
                    "手工填写",
                    f"{config.sample_rate}",
                    f"{config.center_freq}",
                    f"{case.tx_gain:.0f}",
                    f"{config.bandwidth}",
                    "运行时填写",
                    f"{config.center_freq}",
                    "0.0",
                    f"{case.amplitude:.2f}",
                    "是",
                    "否",
                    generation_label,
                    f"{DEFAULT_SPAN_HZ}",
                    f"{DEFAULT_RBW_HZ}",
                    f"{DEFAULT_VBW_HZ}",
                    f"{DEFAULT_ATT_DB}",
                    f"{DEFAULT_REF_LEVEL_DBM}",
                    "明显可见 / 勉强可见 / 不可见",
                    "稳定 / 边缘 / 不稳定",
                    "",
                    case.note,
                ]
            )
        for case in build_stage2_cases():
            writer.writerow(
                [
                    case["stage"],
                    case["step_label"],
                    "扩频",
                    "按需启用 --qt-preview",
                    "按需启用 --qt-preview",
                    "手工填写",
                    f"{config.sample_rate}",
                    f"{config.center_freq}",
                    case["tx_gain"],
                    f"{config.bandwidth}",
                    "运行时填写",
                    f"{config.center_freq}",
                    "0.0",
                    case["amplitude"],
                    "是",
                    "否",
                    generation_label,
                    f"{DEFAULT_SPAN_HZ}",
                    f"{DEFAULT_RBW_HZ}",
                    f"{DEFAULT_VBW_HZ}",
                    f"{DEFAULT_ATT_DB}",
                    f"{DEFAULT_REF_LEVEL_DBM}",
                    "明显可见 / 勉强可见 / 不可见",
                    "稳定 / 边缘 / 不稳定",
                    "",
                    case["note"],
                ]
            )
        for case in build_stage3_cases():
            writer.writerow(
                [
                    case["stage"],
                    case["step_label"],
                    "扩频",
                    "按需启用 --qt-preview",
                    "按需启用 --qt-preview",
                    "手工填写",
                    f"{config.sample_rate}",
                    f"{config.center_freq}",
                    case["tx_gain"],
                    f"{config.bandwidth}",
                    "运行时填写",
                    f"{config.center_freq}",
                    "0.0",
                    case["amplitude"],
                    "是",
                    "否",
                    generation_label,
                    f"{DEFAULT_SPAN_HZ}",
                    f"{DEFAULT_RBW_HZ}",
                    f"{DEFAULT_VBW_HZ}",
                    f"{DEFAULT_ATT_DB}",
                    f"{DEFAULT_REF_LEVEL_DBM}",
                    "明显可见 / 勉强可见 / 不可见",
                    "稳定 / 边缘 / 不稳定",
                    "",
                    case["note"],
                ]
            )


def write_checklist(output_path: Path, config_path: Path) -> None:
    config = load_tx_runtime_config(config_path)
    generation_label = spread_generation_label(config.prn_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# PRN{config.prn_id} 发射参数试验清单",
        "",
        "## 实验前准备",
        "- [ ] 确认 B210 已连接并可被 `uhd_find_devices` 识别",
        "- [ ] 确认使用的配置文件正确",
        f"- [ ] 确认配置文件：`{config_path}`",
        "- [ ] 确认频谱仪输入阻抗为 `50 ohm`",
        "- [ ] 确认同轴线连接在 B210 的 `TX/RX` 口",
        "- [ ] 确认已启用前端保护，参考电平和输入衰减已设置",
        "",
        "## 固定实验条件",
        f"- [ ] `center_freq = {config.center_freq}`",
        f"- [ ] `sample_rate = {config.sample_rate}`",
        f"- [ ] `samples_per_chip = {config.samples_per_chip}`",
        f"- [ ] `prn_id = {config.prn_id}`",
        f"- [ ] `antenna = {config.antenna}`",
        "- [ ] 使用同一台频谱仪、同一根线缆、同一组基础显示参数",
        "",
        "## 推荐频谱仪设置",
        "- [ ] `Center = 100 MHz`",
        "- [ ] `Span = 5 MHz`",
        "- [ ] `RBW = 1 kHz`",
        "- [ ] `VBW = 1 kHz`",
        "- [ ] `Att = 10 dB`",
        "- [ ] `Ref Level = -66 dBm`",
        "",
        "## 基准确认：先确认当天已知可见组合",
        f"### 组合：tx_gain={DEFAULT_BASELINE_TX_GAIN:.0f}, amplitude={DEFAULT_BASELINE_AMPLITUDE:.2f}",
        f"- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config {config_path} --tx-gain {DEFAULT_BASELINE_TX_GAIN:.0f} --amplitude {DEFAULT_BASELINE_AMPLITUDE:.2f} --duration {DEFAULT_DURATION_S:.0f}`",
        "- [ ] 观察 20 s 内是否始终能看到宽带包络",
        "- [ ] 确认停止发射后包络消失",
        "- [ ] 如基准点不稳定，先排查连线、频谱仪设置、underflow 和 `--qt-preview` 软件侧频谱",
        "- [ ] 从终端复制“实验表格参数摘要”到实验表格",
        "",
        "## 阶段1：先扫 tx_gain（固定 amplitude = 0.50，顺序 10→8→6）",
    ]

    for case in build_stage1_cases():
        lines.extend(
            [
                f"### 组合：tx_gain={case.tx_gain:.0f}, amplitude={case.amplitude:.2f}",
                f"- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config {config_path} --tx-gain {case.tx_gain:.0f} --amplitude {case.amplitude:.2f} --duration {DEFAULT_DURATION_S:.0f}`",
                "- [ ] 观察 20 s 内是否始终能看到宽带包络",
                "- [ ] 记录停止发射后是否消失",
                "- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见",
                "- [ ] 记录稳定性：稳定 / 边缘 / 不稳定",
                "- [ ] 从终端复制“实验表格参数摘要”到实验表格",
                "- [ ] 如有必要，保存截图并记录截图文件名",
                "- [ ] 填写本组备注",
                "",
            ]
        )

    lines.extend(
        [
            "## 阶段2：再扫 amplitude（固定阶段1选出的最小稳定 tx_gain，顺序 0.50→0.40→0.30）",
        ]
    )

    for case in build_stage2_cases():
        lines.extend(
            [
                f"### 组合：tx_gain={case['tx_gain']}, amplitude={case['amplitude']}",
                f"- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config {config_path} --tx-gain {case['tx_gain']} --amplitude {case['amplitude']} --duration {DEFAULT_DURATION_S:.0f}`",
                "- [ ] 观察 20 s 内是否始终能看到宽带包络",
                "- [ ] 记录停止发射后是否消失",
                "- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见",
                "- [ ] 记录稳定性：稳定 / 边缘 / 不稳定",
                "- [ ] 从终端复制“实验表格参数摘要”到实验表格",
                "- [ ] 如有必要，保存截图并记录截图文件名",
                "- [ ] 填写本组备注",
                "",
            ]
        )

    lines.extend(
        [
            "## 阶段3：重复性验证（使用最终选定组合）",
        ]
    )

    for case in build_stage3_cases():
        lines.extend(
            [
                f"### {case['step_label']}",
                f"- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config {config_path} --tx-gain {case['tx_gain']} --amplitude {case['amplitude']} --duration {DEFAULT_DURATION_S:.0f}`",
                "- [ ] 确认谱形是否与前两轮一致",
                "- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见",
                "- [ ] 记录稳定性：稳定 / 边缘 / 不稳定",
                "- [ ] 记录是否存在漂移或偶发消失",
                "- [ ] 如有必要，保存截图并记录截图文件名",
                "",
            ]
        )

    lines.extend(
        [
            "## 实验结束后汇总",
            "- [ ] 找出最低稳定可见的参数组合",
            "- [ ] 找出最稳定、最容易复现的参数组合",
            "- [ ] 更新实验记录草稿中的结果汇总",
            "- [ ] 如需固化为新的默认实验配置，再决定是否更新配置文件",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_draft(output_path: Path, config_path: Path) -> None:
    config = load_tx_runtime_config(config_path)
    generation_label = spread_generation_label(config.prn_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {date.today().isoformat()} PRN{config.prn_id} 发射参数试验记录草稿",
        "",
        "## 基本信息",
        f"- 实验日期：`{date.today().isoformat()}`",
        "- 操作者：",
        f"- 配置文件：`{config_path}`",
        "- 实验目标：在可见谱配置基础上，寻找最低可见且稳定的发射参数组合，并同步填写实验表格关键字段",
        "",
        "## 固定发射条件",
        f"- `signal_mode = {config.signal_mode}`",
        f"- `center_freq = {config.center_freq}`",
        f"- `sample_rate = {config.sample_rate}`",
        f"- `samples_per_chip = {config.samples_per_chip}`",
        f"- `prn_id = {config.prn_id}`",
        f"- `antenna = {config.antenna}`",
        f"- `nav_pattern = {config.nav_pattern}`",
        "",
        "## 固定频谱仪条件",
        "- `Center = 100 MHz`",
        "- `Span = 5 MHz`",
        "- `RBW = 1 kHz`",
        "- `VBW = 1 kHz`",
        "- `Att = 10 dB`",
        "- `Ref Level = -66 dBm`",
        "",
        "## 试验顺序",
        f"- 基准确认：先用 `tx_gain = {DEFAULT_BASELINE_TX_GAIN:.0f}`、`amplitude = {DEFAULT_BASELINE_AMPLITUDE:.2f}` 做当天基准确认，每组运行 `{DEFAULT_DURATION_S:.0f} s`",
        f"- 阶段1：固定 `amplitude = {DEFAULT_BASELINE_AMPLITUDE:.2f}`，按顺序测试 `tx_gain = {', '.join(f'{value:.0f}' for value in DEFAULT_STAGE1_TX_GAINS)}`",
        f"- 阶段2：固定阶段1选出的最小稳定 `tx_gain`，按顺序测试 `amplitude = {', '.join(f'{value:.2f}' for value in DEFAULT_STAGE2_AMPLITUDES)}`",
        f"- 阶段3：对最终组合重复运行 3 次，每次 `{DEFAULT_DURATION_S:.0f} s`，验证可重复性",
        "",
        "## 表格关键字段",
        "",
        "- 发送信号类型：扩频",
        "- GNU Radio流图：按需启用 `--qt-preview`",
        "- GNU Radio频谱：按需启用 `--qt-preview`",
        "- 频谱仪结果：手工填写",
        f"- 采样率：`{config.sample_rate}`",
        f"- 射频中心频率：`{config.center_freq}`",
        f"- 带宽：`{config.bandwidth}`",
        f"- serial：优先抄录终端“实验表格参数摘要”中的 `serial`",
        f"- 信号观测频率：`{config.center_freq}`",
        "- 基带偏移频率：`0.0`",
        "- 频谱仪结果：`明显可见 / 勉强可见 / 不可见`",
        "- 稳定性：`稳定 / 边缘 / 不稳定`",
        "- 是否归一化：`是`",
        "- 是否直流偏置：`否`",
        f"- 生成方式：`{generation_label}`",
        "",
        "## 基准确认",
        "",
        "| tx_gain | amplitude | 频谱仪结果 | 稳定性 | 截图文件 | 备注 |",
        "| --- | --- | --- | --- | --- | --- |",
        f"| {DEFAULT_BASELINE_TX_GAIN:.0f} | {DEFAULT_BASELINE_AMPLITUDE:.2f} |  |  |  |  |",
        "",
        "## 阶段1 结果汇总表",
        "",
        "| tx_gain | amplitude | 频谱仪结果 | 稳定性 | 截图文件 | 备注 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for case in build_stage1_cases():
        lines.append(f"| {case.tx_gain:.0f} | {case.amplitude:.2f} |  |  |  |  |")

    lines.extend(
        [
            "",
            "## 阶段2 结果汇总表",
            "",
            "| tx_gain | amplitude | 频谱仪结果 | 稳定性 | 截图文件 | 备注 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case in build_stage2_cases():
        lines.append(f"| {case['tx_gain']} | {case['amplitude']} |  |  |  |  |")

    lines.extend(
        [
            "",
            "## 阶段3 重复性验证",
            "",
            "| 次数 | tx_gain | amplitude | 频谱仪结果 | 稳定性 | 是否一致 | 截图文件 | 备注 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for index, case in enumerate(build_stage3_cases(), start=1):
        lines.append(f"| {index} | {case['tx_gain']} | {case['amplitude']} |  |  |  |  |  |")

    lines.extend(
        [
            "",
            "## 结论",
            "",
            "- 最低稳定可见参数组合：",
            "- 最稳定参数组合：",
            "- 建议后续默认实验配置：",
            "",
            "## 后续动作",
            "",
            "- [ ] 如有必要，更新实验检查点记录",
            "- [ ] 如有必要，更新可见谱配置文件",
            "- [ ] 将本次截图按统一规则归档",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_commands(config_path: Path) -> None:
    print("基准确认：先确认当天已知可见组合")
    print(
        "PYTHONPATH=src python3 scripts/run_tx.py "
        f"--config {config_path} "
        f"--tx-gain {DEFAULT_BASELINE_TX_GAIN:.0f} "
        f"--amplitude {DEFAULT_BASELINE_AMPLITUDE:.2f} "
        f"--duration {DEFAULT_DURATION_S:.0f}"
    )
    print("")
    print("阶段1：先扫 tx_gain（固定 amplitude = 0.50，顺序 10→8→6）")
    for case in build_stage1_cases():
        print(
            "PYTHONPATH=src python3 scripts/run_tx.py "
            f"--config {config_path} "
            f"--tx-gain {case.tx_gain:.0f} "
            f"--amplitude {case.amplitude:.2f} "
            f"--duration {DEFAULT_DURATION_S:.0f}"
        )
    print("")
    print("阶段2：再扫 amplitude（把 <阶段1选出的最小稳定tx_gain> 替换成你的结果）")
    for case in build_stage2_cases():
        print(
            "PYTHONPATH=src python3 scripts/run_tx.py "
            f"--config {config_path} "
            f"--tx-gain {case['tx_gain']} "
            f"--amplitude {case['amplitude']} "
            f"--duration {DEFAULT_DURATION_S:.0f}"
        )
    print("")
    print("阶段3：重复性验证（把占位符替换成最终组合）")
    for case in build_stage3_cases():
        print(
            "PYTHONPATH=src python3 scripts/run_tx.py "
            f"--config {config_path} "
            f"--tx-gain {case['tx_gain']} "
            f"--amplitude {case['amplitude']} "
            f"--duration {DEFAULT_DURATION_S:.0f}"
        )


def main() -> None:
    args = build_parser().parse_args()
    config_path = Path(args.config)
    default_records_dir = Path("experiments") / "records" / date.today().isoformat() / "tx_visibility_sweep"
    csv_output = Path(args.csv_output) if args.csv_output else default_records_dir / "tx_visibility_sweep_template.csv"
    checklist_output = Path(args.checklist_output) if args.checklist_output else default_records_dir / "tx_visibility_sweep_checklist.md"
    draft_output = (
        Path(args.draft_output)
        if args.draft_output
        else default_records_dir / f"{date.today().isoformat()}_tx_visibility_sweep_draft.md"
    )

    write_template_csv(csv_output, config_path)
    write_checklist(checklist_output, config_path)
    write_draft(draft_output, config_path)

    print(f"已生成参数扫描模板：{csv_output}")
    print(f"已生成实验当天勾选清单：{checklist_output}")
    print(f"已生成实验记录草稿：{draft_output}")
    print("")
    print("建议执行的参数扫描命令：")
    print_commands(config_path)


if __name__ == "__main__":
    main()
