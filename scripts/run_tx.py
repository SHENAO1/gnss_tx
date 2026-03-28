from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import sys
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from gnss_tx.usrp import (
    apply_overrides,
    build_tx_top_block,
    export_tx_truth_json,
    format_config_report,
    format_lab_table_summary,
    format_observation_checklist,
    format_uhd_tx_sample_rate_report,
    is_b210_available,
    load_tx_runtime_config,
    uhd_find_devices_output,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the single-satellite GPS L1 C/A GNU Radio + B210 transmit chain."
    )
    parser.add_argument("--config", default="configs/tx_b210.yaml")
    parser.add_argument("--prn-id", type=int)
    parser.add_argument(
        "--prn-ids",
        type=str,
        default=None,
        help="Comma-separated PRN subset to transmit, e.g. --prn-ids 1,5,10,15. Implies multi-satellite mode.",
    )
    parser.add_argument(
        "--all-prns",
        action="store_true",
        default=False,
        help="Transmit all 32 PRNs combined (overrides --prn-id).",
    )
    parser.add_argument("--center-freq", type=float)
    parser.add_argument("--tx-gain", type=float)
    parser.add_argument("--sample-rate", type=float)
    parser.add_argument("--samples-per-chip", type=int)
    parser.add_argument("--signal-mode", choices=["spread", "tone"])
    parser.add_argument("--nav-pattern")
    parser.add_argument("--tone-offset-hz", type=float)
    parser.add_argument("--duration", type=float, dest="duration_s")
    parser.add_argument("--amplitude", type=float)
    parser.add_argument(
        "--qt-preview",
        action="store_true",
        help="Show GNU Radio QT time/frequency previews while transmitting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and print the effective configuration without starting transmission.",
    )
    parser.add_argument(
        "--export-truth-json",
        type=str,
        default=None,
        help="Export the effective TX truth contract to a JSON file for RX BER analysis.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_tx_runtime_config(Path(args.config))

    prn_ids_parsed = None
    all_prns = args.all_prns
    if args.prn_ids is not None:
        prn_ids_parsed = [int(x.strip()) for x in args.prn_ids.split(",")]
        all_prns = True

    config = apply_overrides(
        config,
        prn_id=args.prn_id,
        **({"all_prns": True} if all_prns else {}),
        **({"prn_ids": prn_ids_parsed} if prn_ids_parsed is not None else {}),
        center_freq=args.center_freq,
        tx_gain=args.tx_gain,
        sample_rate=args.sample_rate,
        samples_per_chip=args.samples_per_chip,
        signal_mode=args.signal_mode,
        nav_pattern=args.nav_pattern,
        tone_offset_hz=args.tone_offset_hz,
        duration_s=args.duration_s,
        amplitude=args.amplitude,
        enable_qt_preview=args.qt_preview,
    )

    print(format_config_report(config))
    print("")
    print(format_observation_checklist(config))
    print("")
    device_report = uhd_find_devices_output()
    print("UHD discovery output:")
    print(device_report if device_report else "(no output)")
    print("")
    print(format_lab_table_summary(config, device_report))

    if args.export_truth_json:
        truth_path = export_tx_truth_json(config, args.export_truth_json)
        print("")
        print(f"[INFO] Exported TX truth JSON: {truth_path}")

    if args.dry_run:
        print("")
        print("[INFO] Dry run requested. Transmission was not started.")
        return 0

    if not is_b210_available():
        print("")
        print("[ERROR] No UHD device detected. Refusing to start transmission.")
        return 1

    tb = build_tx_top_block(config)
    app = None
    timer = None
    print("")
    if config.enable_qt_preview:
        from PyQt5 import QtCore, QtWidgets

        if "DISPLAY" not in os.environ and "WAYLAND_DISPLAY" not in os.environ and "QT_QPA_PLATFORM" not in os.environ:
            print("[ERROR] QT preview requested, but no display server was detected. Set DISPLAY or QT_QPA_PLATFORM.")
            return 1

        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        signal.signal(signal.SIGINT, lambda *_args: app.quit())
        timer = QtCore.QTimer()
        timer.start(200)
        timer.timeout.connect(lambda: None)
        if config.duration_s is not None:
            QtCore.QTimer.singleShot(int(config.duration_s * 1000), app.quit)
        tb.show_preview()
        print("[INFO] Starting transmission with QT preview. Keep analyzer protection enabled for the first low-power observation.")
    else:
        print("[INFO] Starting transmission. Keep analyzer protection enabled for the first low-power observation.")

    tb.start()
    try:
        print(format_uhd_tx_sample_rate_report(config.sample_rate, tb.sink_block, label="Python TX runtime"))
        if app is not None:
            app.exec_()
        elif config.duration_s is not None:
            time.sleep(config.duration_s)
        else:
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping transmission on user request.")
    finally:
        tb.close_preview()
        tb.stop()
        tb.wait()

    print("[SUCCESS] Transmission finished cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
