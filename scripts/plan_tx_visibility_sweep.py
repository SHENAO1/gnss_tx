from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


DEFAULT_TX_GAINS = (6.0, 8.0, 10.0, 12.0)
DEFAULT_AMPLITUDES = (0.30, 0.40, 0.50, 0.60)


@dataclass(frozen=True)
class SweepCase:
    tx_gain: float
    amplitude: float


def build_cases() -> list[SweepCase]:
    return [
        SweepCase(tx_gain=tx_gain, amplitude=amplitude)
        for tx_gain in DEFAULT_TX_GAINS
        for amplitude in DEFAULT_AMPLITUDES
    ]


def write_template_csv(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "tx_gain",
                "amplitude",
                "center_freq_hz",
                "sample_rate_sps",
                "span_hz",
                "rbw_hz",
                "vbw_hz",
                "att_db",
                "ref_level_dbm",
                "visible",
                "repeatable",
                "screenshot_file",
                "notes",
            ]
        )
        for case in build_cases():
            writer.writerow(
                [
                    f"{case.tx_gain:.0f}",
                    f"{case.amplitude:.2f}",
                    "100000000.0",
                    "4092000.0",
                    "5000000.0",
                    "1000.0",
                    "1000.0",
                    "10.0",
                    "-66.0",
                    "",
                    "",
                    "",
                    "",
                ]
            )


def print_commands() -> None:
    for case in build_cases():
        print(
            "PYTHONPATH=src python3 scripts/run_tx.py "
            "--config configs/tx_b210_visible_spectrum.yaml "
            f"--tx-gain {case.tx_gain:.0f} "
            f"--amplitude {case.amplitude:.2f} "
            "--duration 10"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a small TX visibility sweep plan.")
    parser.add_argument(
        "--output",
        default="results/csv/tx_visibility_sweep_template.csv",
        help="CSV template output path.",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    write_template_csv(output_path)
    print(f"Saved sweep template: {output_path}")
    print("")
    print("Suggested sweep commands:")
    print_commands()


if __name__ == "__main__":
    main()
