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
    # n 是“第几个采样点”的索引，不是秒。
    n = np.arange(int(sample_rate * duration_s), dtype=np.float64)
    # 这里必须除以 sample_rate（fs），把采样点索引换算为时间 t=n/fs。
    # 复指数/正弦的相位应为 2*pi*f*t，所以离散形式是 2*pi*f*n/fs。
    # 也可理解为：每个采样点固定前进 2*pi*f/fs 弧度的相位。
    x = amplitude * np.exp(1j * 2 * np.pi * tone_freq * n / sample_rate)
    return x.astype(np.complex64)
