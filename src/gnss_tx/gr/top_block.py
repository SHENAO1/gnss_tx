from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT, normalize_nav_bits
from gnss_tx.signal.iq_builder import generate_complex_tone
from gnss_tx.signal.multi_sat_combiner import build_multi_sat_replay_samples
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator

try:
    from gnuradio import blocks, gr, qtgui
    from gnuradio.fft import window
except ImportError:  # pragma: no cover - GNU Radio is optional in the dev environment.
    blocks = None
    gr = None
    qtgui = None
    window = None

try:
    from PyQt5 import QtCore, QtWidgets
    import sip
except ImportError:  # pragma: no cover - optional in test environments
    QtCore = None
    QtWidgets = None
    sip = None

HAVE_GNURADIO = gr is not None
HAVE_QTGUI = HAVE_GNURADIO and qtgui is not None and QtWidgets is not None and sip is not None
_SyncBlockBase = gr.sync_block if HAVE_GNURADIO else object
_TopBlockBase = gr.top_block if HAVE_GNURADIO else object


@dataclass(frozen=True)
class TxBlockConfig:
    # 当前支持 GPS L1 C/A PRN1~32 的单星发送，以及 32 颗星叠加发送。
    prn_id: int = 1
    # True 时忽略 prn_id，发射 PRN 1~32 全部叠加的合并信号。
    all_prns: bool = False
    # 可选：指定要叠加的 PRN 子集；None 且 all_prns=True 时使用全部 32 颗。
    prn_ids: list | None = None
    # ``spread`` 对应 PRN 扩频发送，``tone`` 对应单音校准发送。
    signal_mode: str = "spread"
    # 每个 chip 展开为多少个 sample。
    # 因此 sample_rate = 1.023e6 * samples_per_chip。
    samples_per_chip: int = 4
    amplitude: float = 0.25
    nav_pattern: str | list[int] = "1 0 1 1 0 0 1 0"
    tone_offset_hz: float = 500e3
    tone_buffer_s: float = 0.1
    # 射频中心频率，对应 USRP 本振输出中心。
    center_freq: float = 100e6
    # 基带采样率，决定数字 sample 输出速度。
    sample_rate: float = 4.092e6
    tx_gain: float | None = None
    bandwidth: float | None = None
    antenna: str = "TX/RX"
    usrp_addr: str = "type=b200"
    enable_qt_preview: bool = False
    # 初始码相位，对应 C/A 周期内部从哪个 chip 开始发。
    initial_code_phase: int = 0
    # 初始导航 bit 内部的 1 ms epoch 偏移。
    initial_nav_epoch: int = 0
    # 初始导航 bit 索引。
    initial_nav_bit_index: int = 0


def _build_time_sink(sample_rate: float):
    if not HAVE_QTGUI:
        raise RuntimeError("GNU Radio Qt GUI support is not available in this Python environment.")

    sink = qtgui.time_sink_c(512, sample_rate, "TX Baseband Time Preview", 1, None)
    sink.set_update_time(0.10)
    sink.set_y_axis(-1.2, 1.2)
    sink.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
    if hasattr(sink, "enable_grid"):
        sink.enable_grid(True)
    if hasattr(sink, "enable_axis_labels"):
        sink.enable_axis_labels(True)
    if hasattr(sink, "set_line_label"):
        sink.set_line_label(0, "I")
        sink.set_line_label(1, "Q")
    return sink


def _build_freq_sink(center_freq: float, sample_rate: float):
    if not HAVE_QTGUI:
        raise RuntimeError("GNU Radio Qt GUI support is not available in this Python environment.")

    sink = qtgui.freq_sink_c(
        2048,
        window.WIN_BLACKMAN_hARRIS,
        center_freq,
        sample_rate,
        "TX Baseband Spectrum Preview",
        1,
        None,
    )
    sink.set_update_time(0.10)
    sink.set_y_axis(-120, 10)
    if hasattr(sink, "set_fft_average"):
        sink.set_fft_average(0.2)
    if hasattr(sink, "enable_grid"):
        sink.enable_grid(True)
    if hasattr(sink, "enable_axis_labels"):
        sink.enable_axis_labels(True)
    if hasattr(sink, "set_line_label"):
        sink.set_line_label(0, "TX Preview")
    return sink


class TxPreviewWindow(QtWidgets.QWidget if QtWidgets is not None else object):
    def __init__(self, time_sink, freq_sink) -> None:
        if not HAVE_QTGUI:
            raise RuntimeError("GNU Radio Qt GUI support is not available in this Python environment.")

        super().__init__()
        self.setWindowTitle("GNSS TX QT Preview")
        self.resize(1400, 900)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(sip.wrapinstance(time_sink.qwidget(), QtWidgets.QWidget))
        layout.addWidget(sip.wrapinstance(freq_sink.qwidget(), QtWidgets.QWidget))


def build_replay_samples(
    *,
    prn_id: int = 1,
    samples_per_chip: int = 4,
    amplitude: float = 1.0,
    nav_pattern: str | list[int] = "1 0 1 1 0 0 1 0",
    initial_code_phase: int = 0,
    initial_nav_epoch: int = 0,
    initial_nav_bit_index: int = 0,
) -> np.ndarray:
    """
    Precompute one full navigation-pattern period of baseband samples.

    Repeating a whole nav-pattern period keeps the loop boundary aligned to both
    the 1 ms C/A epoch and the 20 ms navigation-bit epoch, avoiding the
    discontinuities caused by restarting mid-pattern.

    物理意义：
    - 这里生成的是“可循环回放的完整基带片段”。
    - 长度按完整 nav pattern 周期来定，而不是随便截一段。
    - 这样 replay 到边界时，导航 bit 相位和 PRN 码相位都能无缝衔接。
    """
    nav_bits = normalize_nav_bits(nav_pattern)
    epochs_per_buffer = CA_EPOCHS_PER_NAV_BIT * len(nav_bits)
    sample_count = epochs_per_buffer * CA_CODE_LENGTH * int(samples_per_chip)

    generator = GpsL1CaBpskGenerator(
        prn_id=prn_id,
        samples_per_chip=samples_per_chip,
        amplitude=amplitude,
        nav_pattern=nav_bits.tolist(),
        initial_code_phase=initial_code_phase,
        initial_nav_epoch=initial_nav_epoch,
        initial_nav_bit_index=initial_nav_bit_index,
    )
    return generator.generate_samples(sample_count)


def build_tone_replay_samples(
    *,
    sample_rate: float,
    amplitude: float = 1.0,
    tone_offset_hz: float = 500e3,
    tone_buffer_s: float = 0.1,
) -> np.ndarray:
    # 单音模式不经过 nav bit 和 PRN 扩频链，
    # 直接生成复指数基带作为硬件链路校准信号。
    return generate_complex_tone(
        sample_rate=sample_rate,
        tone_freq=tone_offset_hz,
        duration_s=tone_buffer_s,
        amplitude=amplitude,
    )


def make_gps_l1_ca_vector_source(
    *,
    prn_id: int = 1,
    samples_per_chip: int = 4,
    amplitude: float = 1.0,
    nav_pattern: str | list[int] = "1 0 1 1 0 0 1 0",
    initial_code_phase: int = 0,
    initial_nav_epoch: int = 0,
    initial_nav_bit_index: int = 0,
):
    if not HAVE_GNURADIO:
        raise RuntimeError("GNU Radio is not available in this Python environment.")

    replay_samples = build_replay_samples(
        prn_id=prn_id,
        samples_per_chip=samples_per_chip,
        amplitude=amplitude,
        nav_pattern=nav_pattern,
        initial_code_phase=initial_code_phase,
        initial_nav_epoch=initial_nav_epoch,
        initial_nav_bit_index=initial_nav_bit_index,
    )
    return blocks.vector_source_c(replay_samples.tolist(), True, 1, [])


def make_tone_vector_source(
    *,
    sample_rate: float,
    amplitude: float = 1.0,
    tone_offset_hz: float = 500e3,
    tone_buffer_s: float = 0.1,
):
    if not HAVE_GNURADIO:
        raise RuntimeError("GNU Radio is not available in this Python environment.")

    replay_samples = build_tone_replay_samples(
        sample_rate=sample_rate,
        amplitude=amplitude,
        tone_offset_hz=tone_offset_hz,
        tone_buffer_s=tone_buffer_s,
    )
    return blocks.vector_source_c(replay_samples.tolist(), True, 1, [])


class GpsL1CaSourceBlock(_SyncBlockBase):
    """
    GNU Radio source block wrapper around the pure Python PRN/state machine.

    该块直接从 Python 状态机逐批生成 sample，适合理解信号处理链。
    当前运行时主链为了降低 underflow 风险，更多使用预生成 replay buffer。
    """

    def __init__(
        self,
        prn_id: int = 1,
        samples_per_chip: int = 1,
        amplitude: float = 0.8,
        nav_pattern=None,
        initial_code_phase: int = 0,
        initial_nav_epoch: int = 0,
        initial_nav_bit_index: int = 0,
    ) -> None:
        self.generator = GpsL1CaBpskGenerator(
            prn_id=prn_id,
            samples_per_chip=samples_per_chip,
            amplitude=amplitude,
            nav_pattern=nav_pattern,
            initial_code_phase=initial_code_phase,
            initial_nav_epoch=initial_nav_epoch,
            initial_nav_bit_index=initial_nav_bit_index,
        )
        self.prn_id = prn_id
        self.samples_per_chip = int(samples_per_chip)
        self.amplitude = float(amplitude)

        if HAVE_GNURADIO:
            super().__init__(
                name="gps_l1_ca_source",
                in_sig=None,
                out_sig=[np.complex64],
            )

    @property
    def state(self):
        return self.generator.state

    def generate(self, num_samples: int) -> np.ndarray:
        return self.generator.generate_samples(num_samples)

    def work(self, input_items, output_items) -> int:
        output = output_items[0]
        output[:] = self.generator.generate_samples(len(output))
        return len(output)


class GpsL1CaTxTopBlock(_TopBlockBase):
    """
    Minimal runtime flowgraph for single-satellite GPS L1 C/A transmission.

    数据流总览：
    - spread 模式：nav bit -> PRN chip -> spread chip -> sample -> replay source -> 幅度缩放 -> USRP
    - tone 模式：tone sample -> replay source -> 幅度缩放 -> USRP
    """

    def __init__(self, config: TxBlockConfig, sink_block=None) -> None:
        if not HAVE_GNURADIO:
            raise RuntimeError("GNU Radio is not available in this Python environment.")
        if config.enable_qt_preview and not HAVE_QTGUI:
            raise RuntimeError("Qt preview requested, but GNU Radio Qt GUI support is unavailable.")

        super().__init__("gnss_tx_single_sat_main")
        self.config = config
        self.preview_window = None
        self.qt_time_sink = None
        self.qt_freq_sink = None
        if config.signal_mode == "tone":
            # 单音链路：直接预生成一段复数单音 sample，再循环回放。
            self.replay_samples = build_tone_replay_samples(
                sample_rate=config.sample_rate,
                amplitude=1.0,
                tone_offset_hz=config.tone_offset_hz,
                tone_buffer_s=config.tone_buffer_s,
            )
        elif config.all_prns or config.prn_ids is not None:
            # 多星叠加模式：生成多颗 PRN 的合并基带 sample 缓冲区。
            # all_prns=True 且 prn_ids=None 时默认使用 PRN 1~32 全部 32 颗。
            self.replay_samples = build_multi_sat_replay_samples(
                prn_ids=config.prn_ids,
                samples_per_chip=config.samples_per_chip,
                nav_pattern=config.nav_pattern,
            )
        else:
            # 单星扩频链路：先在 Python 中生成完整的扩频 sample 缓冲区，
            # 再交给 GNU Radio 做稳定回放。
            self.replay_samples = build_replay_samples(
                prn_id=config.prn_id,
                samples_per_chip=config.samples_per_chip,
                amplitude=1.0,
                nav_pattern=config.nav_pattern,
                initial_code_phase=config.initial_code_phase,
                initial_nav_epoch=config.initial_nav_epoch,
                initial_nav_bit_index=config.initial_nav_bit_index,
            )
        # GNU Radio 运行时实际看到的源是一个循环的复数 sample 序列。
        self.source = blocks.vector_source_c(self.replay_samples.tolist(), True, 1, [])
        # 将“单位幅度 replay 样本”缩放为最终发射幅度。
        self.multiply_const = blocks.multiply_const_cc(config.amplitude)
        self.sink_block = sink_block

        self.connect(self.source, self.multiply_const)
        if config.enable_qt_preview:
            self.qt_time_sink = _build_time_sink(config.sample_rate)
            self.qt_freq_sink = _build_freq_sink(config.center_freq, config.sample_rate)
            self.preview_window = TxPreviewWindow(self.qt_time_sink, self.qt_freq_sink)
            self.connect(self.multiply_const, self.qt_time_sink)
            self.connect(self.multiply_const, self.qt_freq_sink)
        if sink_block is not None:
            # 最终把缩放后的 complex baseband sample 送入 USRP sink。
            self.connect(self.multiply_const, sink_block)

    def set_amplitude(self, amplitude: float) -> None:
        self.multiply_const.set_k(float(amplitude))

    def show_preview(self) -> None:
        if self.preview_window is not None:
            self.preview_window.show()

    def close_preview(self) -> None:
        if self.preview_window is not None:
            self.preview_window.close()


__all__ = [
    "GpsL1CaSourceBlock",
    "GpsL1CaTxTopBlock",
    "HAVE_GNURADIO",
    "HAVE_QTGUI",
    "TxBlockConfig",
    "TxPreviewWindow",
    "build_multi_sat_replay_samples",
    "build_replay_samples",
    "build_tone_replay_samples",
    "make_gps_l1_ca_vector_source",
    "make_tone_vector_source",
]
