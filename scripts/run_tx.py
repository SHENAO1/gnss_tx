from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time

from gnss_tx.usrp import (
    apply_overrides,
    build_tx_top_block,
    format_config_report,
    format_observation_checklist,
    is_b210_available,
    load_tx_runtime_config,
    uhd_find_devices_output,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the PRN1 GNU Radio + B210 transmit chain.")
    parser.add_argument("--config", default="configs/tx_b210.yaml")
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
        "--dry-run",
        action="store_true",
        help="Load and print the effective configuration without starting transmission.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_tx_runtime_config(Path(args.config))
    config = apply_overrides(
        config,
        center_freq=args.center_freq,
        tx_gain=args.tx_gain,
        sample_rate=args.sample_rate,
        samples_per_chip=args.samples_per_chip,
        signal_mode=args.signal_mode,
        nav_pattern=args.nav_pattern,
        tone_offset_hz=args.tone_offset_hz,
        duration_s=args.duration_s,
        amplitude=args.amplitude,
    )

    print(format_config_report(config))
    print("")
    print(format_observation_checklist(config))
    print("")
    device_report = uhd_find_devices_output()
    print("UHD discovery output:")
    print(device_report if device_report else "(no output)")

    if args.dry_run:
        print("")
        print("[INFO] Dry run requested. Transmission was not started.")
        return 0

    if not is_b210_available():
        print("")
        print("[ERROR] No UHD device detected. Refusing to start transmission.")
        return 1

    tb = build_tx_top_block(config)
    print("")
    print("[INFO] Starting transmission. Keep analyzer protection enabled for the first low-power observation.")
    tb.start()
    try:
        if config.duration_s is not None:
            time.sleep(config.duration_s)
        else:
            while True:
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping transmission on user request.")
    finally:
        tb.stop()
        tb.wait()

    print("[SUCCESS] Transmission finished cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
