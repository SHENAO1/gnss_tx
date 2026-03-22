from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def main():
    project_root = Path(__file__).resolve().parents[1]
    in_file = project_root / "results" / "npy" / "test_iq_tone.npy"
    fig_dir = project_root / "results" / "figs"
    fig_dir.mkdir(parents=True, exist_ok=True)

    iq = np.load(in_file)
    i = np.real(iq)
    q = np.imag(iq)

    # 只显示前 200 个点的时域波形
    n_show = min(200, len(iq))
    n = np.arange(n_show)

    plt.figure(figsize=(10, 4))
    plt.plot(n, i[:n_show], label="I")
    plt.plot(n, q[:n_show], label="Q")
    plt.xlabel("Sample Index")
    plt.ylabel("Amplitude")
    plt.title("IQ Time Domain")
    plt.legend()
    plt.grid(True)
    time_fig = fig_dir / "test_iq_time.png"
    plt.tight_layout()
    plt.savefig(time_fig, dpi=150)
    plt.close()

    # 频谱
    N = len(iq)
    spec = np.fft.fftshift(np.fft.fft(iq))
    freq = np.fft.fftshift(np.fft.fftfreq(N, d=1.0 / 1_000_000.0))
    spec_db = 20 * np.log10(np.abs(spec) + 1e-12)

    plt.figure(figsize=(10, 4))
    plt.plot(freq, spec_db)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude (dB)")
    plt.title("IQ Spectrum")
    plt.grid(True)
    spec_fig = fig_dir / "test_iq_spectrum.png"
    plt.tight_layout()
    plt.savefig(spec_fig, dpi=150)
    plt.close()

    print("=" * 60)
    print("Plot Results")
    print("=" * 60)
    print(f"Input file      : {in_file}")
    print(f"Time-domain fig : {time_fig}")
    print(f"Spectrum fig    : {spec_fig}")
    print("[SUCCESS] Figures generated.")


if __name__ == "__main__":
    main()
