from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
import subprocess
from typing import Any

from gnss_tx.gr.top_block import GpsL1CaTxTopBlock, TxBlockConfig
from gnss_tx.usrp.b210_sink import create_b210_sink
from gnss_tx.utils.io import load_yaml_file

GPS_CA_CHIP_RATE = 1.023e6
SPECTRUM_ANALYZER_MAX_INPUT_DBM = 30.0
SPECTRUM_ANALYZER_MAX_DC_V = 50.0
DEFAULT_OBSERVATION_SPANS_HZ = (20e6, 10e6, 5e6, 2e6)


@dataclass(frozen=True)
class TxRuntimeConfig:
    prn_id: int = 1
    signal_mode: str = "spread"
    usrp_addr: str = "type=b200"
    center_freq: float = 100e6
    sample_rate: float = 4.092e6
    samples_per_chip: int = 4
    tx_gain: float | None = None
    amplitude: float = 0.25
    antenna: str = "TX/RX"
    bandwidth: float | None = None
    nav_pattern: str = "1 0 1 1 0 0 1 0"
    tone_offset_hz: float = 500e3
    tone_buffer_s: float = 0.1
    enable_qt_preview: bool = False
    duration_s: float | None = None
    continuous: bool = True
    initial_code_phase: int = 0
    initial_nav_epoch: int = 0
    initial_nav_bit_index: int = 0

    def validate(self) -> "TxRuntimeConfig":
        if self.signal_mode not in {"spread", "tone"}:
            raise ValueError("signal_mode must be one of: spread, tone.")
        if self.prn_id != 1:
            raise NotImplementedError("v1 only supports PRN1.")
        if self.samples_per_chip <= 0:
            raise ValueError("samples_per_chip must be > 0.")
        if self.center_freq <= 0:
            raise ValueError("center_freq must be > 0.")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be > 0.")
        if not 0.0 < self.amplitude <= 1.0:
            raise ValueError("amplitude must be in the range (0, 1].")
        if self.duration_s is not None and self.duration_s <= 0:
            raise ValueError("duration_s must be > 0 when provided.")
        if self.tone_buffer_s <= 0:
            raise ValueError("tone_buffer_s must be > 0.")
        if abs(self.tone_offset_hz) >= (self.sample_rate / 2.0):
            raise ValueError("tone_offset_hz must lie strictly within +/- sample_rate/2.")

        if self.signal_mode == "spread":
            derived_rate = GPS_CA_CHIP_RATE * self.samples_per_chip
            if abs(self.sample_rate - derived_rate) > 1e-6:
                raise ValueError(
                    f"sample_rate must equal 1.023e6 * samples_per_chip ({derived_rate})."
                )
        return self

    def to_block_config(self) -> TxBlockConfig:
        return TxBlockConfig(
            prn_id=self.prn_id,
            signal_mode=self.signal_mode,
            samples_per_chip=self.samples_per_chip,
            amplitude=self.amplitude,
            nav_pattern=self.nav_pattern,
            tone_offset_hz=self.tone_offset_hz,
            tone_buffer_s=self.tone_buffer_s,
            center_freq=self.center_freq,
            sample_rate=self.sample_rate,
            tx_gain=self.tx_gain,
            bandwidth=self.bandwidth,
            antenna=self.antenna,
            usrp_addr=self.usrp_addr,
            enable_qt_preview=self.enable_qt_preview,
            initial_code_phase=self.initial_code_phase,
            initial_nav_epoch=self.initial_nav_epoch,
            initial_nav_bit_index=self.initial_nav_bit_index,
        )


def load_tx_runtime_config(path: str | Path) -> TxRuntimeConfig:
    raw = load_yaml_file(path)
    if "sample_rate" not in raw and "samples_per_chip" in raw:
        raw["sample_rate"] = GPS_CA_CHIP_RATE * int(raw["samples_per_chip"])
    if "bandwidth" not in raw and "sample_rate" in raw:
        raw["bandwidth"] = float(raw["sample_rate"])
    return TxRuntimeConfig(**raw).validate()


def apply_overrides(config: TxRuntimeConfig, **overrides: Any) -> TxRuntimeConfig:
    effective: dict[str, Any] = {}
    for key, value in overrides.items():
        if value is not None:
            effective[key] = value

    candidate = replace(config, **effective)
    if "sample_rate" not in effective and "samples_per_chip" in effective:
        candidate = replace(candidate, sample_rate=GPS_CA_CHIP_RATE * candidate.samples_per_chip)
    if "bandwidth" not in effective and (
        "sample_rate" in effective or "samples_per_chip" in effective
    ):
        candidate = replace(candidate, bandwidth=candidate.sample_rate)
    if "duration_s" in effective:
        candidate = replace(candidate, continuous=False)

    return candidate.validate()


def format_config_report(config: TxRuntimeConfig) -> str:
    lines = [
        "=" * 60,
        "GNSS TX Runtime Config",
        "=" * 60,
    ]
    for key, value in asdict(config).items():
        lines.append(f"{key}={value}")
    lines.extend(
        [
            "",
            f"Spectrum analyzer max input: {SPECTRUM_ANALYZER_MAX_INPUT_DBM} dBm",
            f"Spectrum analyzer max DC   : {SPECTRUM_ANALYZER_MAX_DC_V} V",
            "Safety reminder            : start with minimum TX gain and low amplitude before connecting the analyzer.",
        ]
    )
    return "\n".join(lines)


def format_observation_checklist(config: TxRuntimeConfig) -> str:
    center_mhz = config.center_freq / 1e6
    sample_rate_mhz = config.sample_rate / 1e6
    span_labels = ", ".join(f"{span / 1e6:.0f} MHz" for span in DEFAULT_OBSERVATION_SPANS_HZ)
    expected_waveform = (
        f"single calibration tone near {center_mhz + config.tone_offset_hz / 1e6:.3f} MHz"
        if config.signal_mode == "tone"
        else "continuous spread-spectrum signal, not a single-tone spike"
    )
    duration_text = (
        f"{config.duration_s:.1f} s"
        if config.duration_s is not None
        else "a short fixed-duration run is recommended for the first RF check"
    )

    lines = [
        "=" * 60,
        "Spectrum Analyzer Observation Checklist",
        "=" * 60,
        "1. Keep the transmitter stopped while configuring the analyzer.",
        "2. Configure the analyzer input for 50 ohm and keep front-end protection enabled.",
        "3. Start with a high reference level and input attenuation before connecting the cable.",
        f"4. Connect B210 port {config.antenna} to the analyzer with a coax cable.",
        f"5. Set analyzer center frequency to {center_mhz:.3f} MHz.",
        f"6. Use a wide span first ({span_labels}); then narrow once the signal is found.",
        "7. Start with wider RBW/VBW; reduce RBW only after the signal is clearly visible.",
        f"8. Expected TX waveform: {expected_waveform}.",
        f"9. Expected occupied bandwidth scale: on the order of the chip-rate sample stream ({sample_rate_mhz:.3f} Msps playback).",
        f"10. Run a first transmit capture for {duration_text}.",
        "11. Success criterion: the wideband signal appears during TX and disappears after TX stops.",
        "",
        f"Analyzer safety limits: {SPECTRUM_ANALYZER_MAX_INPUT_DBM} dBm max input, {SPECTRUM_ANALYZER_MAX_DC_V} V DC max.",
        "Do not increase tx_gain or amplitude until the first low-power observation is confirmed safe.",
    ]
    return "\n".join(lines)


def extract_uhd_device_field(device_report: str, field_name: str) -> str:
    prefix = f"{field_name}:"
    for line in device_report.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            return stripped.split(":", maxsplit=1)[1].strip()
    return ""


def _signal_center_frequency_hz(config: TxRuntimeConfig) -> float:
    if config.signal_mode == "tone":
        return config.center_freq + config.tone_offset_hz
    return config.center_freq


def _signal_offset_frequency_hz(config: TxRuntimeConfig) -> float:
    if config.signal_mode == "tone":
        return config.tone_offset_hz
    return 0.0


def _signal_generation_label(config: TxRuntimeConfig) -> str:
    if config.signal_mode == "tone":
        return "单音缓冲回放"
    return "PRN1 C/A 扩频缓冲回放"


def format_lab_table_summary(config: TxRuntimeConfig, device_report: str = "") -> str:
    serial = extract_uhd_device_field(device_report, "serial") or config.usrp_addr
    gr_flowgraph_field = "QT 预览开启" if config.enable_qt_preview else "不输出"
    gr_spectrum_field = "QT 频谱预览开启" if config.enable_qt_preview else "不输出"
    lines = [
        "=" * 60,
        "实验表格参数摘要",
        "=" * 60,
        f"发送信号类型={'扩频' if config.signal_mode == 'spread' else '单音'}",
        f"GNU Radio流图={gr_flowgraph_field}",
        f"GNU Radio频谱={gr_spectrum_field}",
        "频谱仪结果=手工填写",
        f"采样率={config.sample_rate}",
        f"射频中心频率={config.center_freq}",
        f"发射增益={config.tx_gain}",
        f"带宽={config.bandwidth}",
        f"serial={serial}",
        f"信号观测频率={_signal_center_frequency_hz(config)}",
        f"基带偏移频率={_signal_offset_frequency_hz(config)}",
        f"幅度={config.amplitude}",
        "是否归一化=是",
        "是否直流偏置=否",
        f"生成方式={_signal_generation_label(config)}",
    ]
    return "\n".join(lines)


def uhd_find_devices_output() -> str:
    completed = subprocess.run(
        ["uhd_find_devices"],
        check=False,
        capture_output=True,
        text=True,
    )
    return (completed.stdout + completed.stderr).strip()


def is_b210_available() -> bool:
    output = uhd_find_devices_output()
    lowered = output.lower()
    return "no uhd devices found" not in lowered and "device" in lowered


def build_tx_top_block(config: TxRuntimeConfig) -> GpsL1CaTxTopBlock:
    sink = create_b210_sink(config.to_block_config())
    return GpsL1CaTxTopBlock(config=config.to_block_config(), sink_block=sink)


__all__ = [
    "DEFAULT_OBSERVATION_SPANS_HZ",
    "GPS_CA_CHIP_RATE",
    "SPECTRUM_ANALYZER_MAX_DC_V",
    "SPECTRUM_ANALYZER_MAX_INPUT_DBM",
    "TxRuntimeConfig",
    "apply_overrides",
    "build_tx_top_block",
    "extract_uhd_device_field",
    "format_config_report",
    "format_lab_table_summary",
    "format_observation_checklist",
    "is_b210_available",
    "load_tx_runtime_config",
    "uhd_find_devices_output",
]
