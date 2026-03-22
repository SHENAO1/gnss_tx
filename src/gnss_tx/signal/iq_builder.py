from __future__ import annotations
import numpy as np


def generate_complex_tone(
    sample_rate: float,
    tone_freq: float,
    duration_s: float,
    amplitude: float = 0.8,
) -> np.ndarray:
    """
    生成一个最简单的复数基带单音:
        x[n] = A * exp(j*2*pi*f*n/fs)

    参数
    ----
    sample_rate : 采样率 Hz
    tone_freq   : 单音频率 Hz（基带）
    duration_s  : 时长 s
    amplitude   : 幅度，建议不超过 1.0

    返回
    ----
    complex64 ndarray
    """
    n = np.arange(int(sample_rate * duration_s), dtype=np.float64)
    x = amplitude * np.exp(1j * 2 * np.pi * tone_freq * n / sample_rate)
    return x.astype(np.complex64)
