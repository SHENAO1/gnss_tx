from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from gnss_tx.ca import CA_CODE_LENGTH, generate_ca_code
from gnss_tx.nav import CA_EPOCHS_PER_NAV_BIT, normalize_nav_bits
from gnss_tx.signal import GpsL1CaBpskGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate analysis artifacts for the PRN1 GPS L1 C/A spread-spectrum chain."
    )
    parser.add_argument("--prn-id", type=int, default=1)
    parser.add_argument("--samples-per-chip", type=int, default=4)
    parser.add_argument("--amplitude", type=float, default=1.0)
    parser.add_argument("--num-ms", type=int, default=40)
    parser.add_argument("--nav-pattern", default="1 0 1 1 0 0 1 0")
    parser.add_argument("--prefix", default="prn1_spread")
    return parser


def parse_nav_pattern(nav_pattern: str) -> np.ndarray:
    return normalize_nav_bits(nav_pattern)


def build_text_report(
    *,
    prn_id: int,
    samples_per_chip: int,
    amplitude: float,
    num_ms: int,
    nav_bits: np.ndarray,
    ca_code: np.ndarray,
    spread_chips: np.ndarray,
    spread_samples: np.ndarray,
    correlation: np.ndarray,
) -> str:
    lines = [
        "=" * 60,
        "PRN1 Spread Analysis",
        "=" * 60,
        f"prn_id={prn_id}",
        f"samples_per_chip={samples_per_chip}",
        f"amplitude={amplitude}",
        f"num_ms={num_ms}",
        f"nav_pattern={nav_bits.tolist()}",
        f"ca_code_length={len(ca_code)}",
        f"epochs_per_nav_bit={CA_EPOCHS_PER_NAV_BIT}",
        f"spread_chip_count={len(spread_chips)}",
        f"spread_sample_count={len(spread_samples)}",
        f"dtype_samples={spread_samples.dtype}",
        f"correlation_peak={float(np.max(correlation))}",
        f"correlation_min={float(np.min(correlation))}",
        "",
        "First 32 C/A chips:",
        str(ca_code[:32].tolist()),
        "",
        "First 32 spread chips:",
        str(spread_chips[:32].tolist()),
        "",
        "First 16 complex samples:",
        str(spread_samples[:16].tolist()),
        "",
        "First 16 correlation values:",
        str(correlation[:16].round(4).tolist()),
    ]
    return "\n".join(lines)


def save_preview_csv(path: Path, ca_code: np.ndarray, spread_chips: np.ndarray, spread_samples: np.ndarray) -> None:
    preview_len = min(64, len(spread_chips))
    sample_preview = np.real(spread_samples[: preview_len * 1])

    header = "index,ca_chip,spread_chip,spread_sample_real"
    rows = [
        f"{index},{int(ca_code[index % len(ca_code)])},{int(spread_chips[index])},{float(sample_preview[index])}"
        for index in range(preview_len)
    ]
    path.write_text("\n".join([header, *rows]), encoding="utf-8")


def plot_ca_code(path: Path, ca_code: np.ndarray) -> None:
    n_show = min(128, len(ca_code))
    x = np.arange(n_show)
    plt.figure(figsize=(10, 3.5))
    plt.step(x, ca_code[:n_show], where="post")
    plt.xlabel("Chip Index")
    plt.ylabel("Chip")
    plt.title("PRN1 C/A Code Preview")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_spread_samples(path: Path, spread_samples: np.ndarray, samples_per_chip: int) -> None:
    n_show = min(16 * samples_per_chip, len(spread_samples))
    x = np.arange(n_show)
    plt.figure(figsize=(10, 3.5))
    plt.step(x, np.real(spread_samples[:n_show]), where="post")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.title("PRN1 Spread Baseband Samples Preview")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_correlation(path: Path, correlation: np.ndarray) -> None:
    x = np.arange(len(correlation))
    plt.figure(figsize=(10, 3.5))
    plt.plot(x, correlation)
    plt.xlabel("Code Phase Shift")
    plt.ylabel("Dot Product")
    plt.title("1 ms Local Code Correlation")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main() -> None:
    args = build_parser().parse_args()
    project_root = Path(__file__).resolve().parents[1]
    fig_dir = project_root / "results" / "figs"
    log_dir = project_root / "results" / "logs"
    npy_dir = project_root / "results" / "npy"
    csv_dir = project_root / "results" / "csv"

    fig_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    npy_dir.mkdir(parents=True, exist_ok=True)
    csv_dir.mkdir(parents=True, exist_ok=True)

    nav_bits = parse_nav_pattern(args.nav_pattern)
    ca_code = generate_ca_code(args.prn_id)
    chip_count = CA_CODE_LENGTH * args.num_ms

    generator = GpsL1CaBpskGenerator(
        prn_id=args.prn_id,
        samples_per_chip=args.samples_per_chip,
        amplitude=args.amplitude,
        nav_pattern=nav_bits.tolist(),
    )

    chip_generator = GpsL1CaBpskGenerator(
        prn_id=args.prn_id,
        samples_per_chip=1,
        amplitude=1.0,
        nav_pattern=nav_bits.tolist(),
    )
    spread_chips = chip_generator.generate_chips(chip_count)
    spread_samples = generator.generate_samples(chip_count * args.samples_per_chip)

    first_epoch = spread_chips[:CA_CODE_LENGTH].astype(np.float32)
    local_code = ca_code.astype(np.float32)
    correlation = np.array(
        [float(np.dot(first_epoch, np.roll(local_code, shift))) for shift in range(CA_CODE_LENGTH)],
        dtype=np.float32,
    )

    prefix = args.prefix
    code_npy = npy_dir / f"{prefix}_ca_code.npy"
    chips_npy = npy_dir / f"{prefix}_spread_chips.npy"
    samples_npy = npy_dir / f"{prefix}_spread_samples.npy"
    report_txt = log_dir / f"{prefix}_analysis.txt"
    preview_csv = csv_dir / f"{prefix}_preview.csv"
    code_fig = fig_dir / f"{prefix}_ca_code.png"
    samples_fig = fig_dir / f"{prefix}_samples.png"
    corr_fig = fig_dir / f"{prefix}_correlation.png"

    np.save(code_npy, ca_code)
    np.save(chips_npy, spread_chips)
    np.save(samples_npy, spread_samples)
    save_preview_csv(preview_csv, ca_code, spread_chips, spread_samples)
    plot_ca_code(code_fig, ca_code)
    plot_spread_samples(samples_fig, spread_samples, args.samples_per_chip)
    plot_correlation(corr_fig, correlation)

    report = build_text_report(
        prn_id=args.prn_id,
        samples_per_chip=args.samples_per_chip,
        amplitude=args.amplitude,
        num_ms=args.num_ms,
        nav_bits=nav_bits,
        ca_code=ca_code,
        spread_chips=spread_chips,
        spread_samples=spread_samples,
        correlation=correlation,
    )
    report_txt.write_text(report, encoding="utf-8")

    print(report)
    print("")
    print(f"Saved code npy      : {code_npy}")
    print(f"Saved chips npy     : {chips_npy}")
    print(f"Saved samples npy   : {samples_npy}")
    print(f"Saved preview csv   : {preview_csv}")
    print(f"Saved report txt    : {report_txt}")
    print(f"Saved code figure   : {code_fig}")
    print(f"Saved sample figure : {samples_fig}")
    print(f"Saved corr figure   : {corr_fig}")


if __name__ == "__main__":
    main()
