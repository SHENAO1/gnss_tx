from pathlib import Path
import sys
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from gnss_tx.signal.iq_builder import generate_complex_tone


def main():
    project_root = Path(__file__).resolve().parents[1]
    out_dir = project_root / "results" / "npy"
    out_dir.mkdir(parents=True, exist_ok=True)

    sample_rate = 1_000_000.0   # 1 MHz
    tone_freq = 50_000.0        # 50 kHz 基带单音
    duration_s = 0.01           # 10 ms
    amplitude = 0.8

    iq = generate_complex_tone(
        sample_rate=sample_rate,
        tone_freq=tone_freq,
        duration_s=duration_s,
        amplitude=amplitude,
    )

    out_file = out_dir / "test_iq_tone.npy"
    np.save(out_file, iq)

    meta_file = out_dir / "test_iq_tone_meta.txt"
    meta_file.write_text(
        "\n".join([
            f"sample_rate={sample_rate}",
            f"tone_freq={tone_freq}",
            f"duration_s={duration_s}",
            f"amplitude={amplitude}",
            f"num_samples={len(iq)}",
            f"dtype={iq.dtype}",
        ]),
        encoding="utf-8"
    )

    print("=" * 60)
    print("Generate Test IQ")
    print("=" * 60)
    print(f"Output file : {out_file}")
    print(f"Meta file   : {meta_file}")
    print(f"Samples     : {len(iq)}")
    print(f"Dtype       : {iq.dtype}")
    print(f"First 5 IQ  : {iq[:5]}")
    print("[SUCCESS] Test IQ generated.")


if __name__ == "__main__":
    main()
