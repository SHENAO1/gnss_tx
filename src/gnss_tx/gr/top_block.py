from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT, normalize_nav_bits
from gnss_tx.signal.iq_builder import generate_complex_tone
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator

try:
    from gnuradio import blocks, gr
except ImportError:  # pragma: no cover - GNU Radio is optional in the dev environment.
    blocks = None
    gr = None

HAVE_GNURADIO = gr is not None
_SyncBlockBase = gr.sync_block if HAVE_GNURADIO else object
_TopBlockBase = gr.top_block if HAVE_GNURADIO else object


@dataclass(frozen=True)
class TxBlockConfig:
    prn_id: int = 1
    signal_mode: str = "spread"
    samples_per_chip: int = 4
    amplitude: float = 0.25
    nav_pattern: str | list[int] = "1 0 1 1 0 0 1 0"
    tone_offset_hz: float = 500e3
    tone_buffer_s: float = 0.1
    center_freq: float = 100e6
    sample_rate: float = 4.092e6
    tx_gain: float | None = None
    bandwidth: float | None = None
    antenna: str = "TX/RX"
    usrp_addr: str = "type=b200"
    initial_code_phase: int = 0
    initial_nav_epoch: int = 0
    initial_nav_bit_index: int = 0


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
    Minimal runtime flowgraph for PRN1 spread-spectrum transmission.
    """

    def __init__(self, config: TxBlockConfig, sink_block=None) -> None:
        if not HAVE_GNURADIO:
            raise RuntimeError("GNU Radio is not available in this Python environment.")

        super().__init__("gnss_tx_prn1_main")
        self.config = config
        if config.signal_mode == "tone":
            self.replay_samples = build_tone_replay_samples(
                sample_rate=config.sample_rate,
                amplitude=1.0,
                tone_offset_hz=config.tone_offset_hz,
                tone_buffer_s=config.tone_buffer_s,
            )
        else:
            self.replay_samples = build_replay_samples(
                prn_id=config.prn_id,
                samples_per_chip=config.samples_per_chip,
                amplitude=1.0,
                nav_pattern=config.nav_pattern,
                initial_code_phase=config.initial_code_phase,
                initial_nav_epoch=config.initial_nav_epoch,
                initial_nav_bit_index=config.initial_nav_bit_index,
            )
        self.source = blocks.vector_source_c(self.replay_samples.tolist(), True, 1, [])
        self.multiply_const = blocks.multiply_const_cc(config.amplitude)
        self.sink_block = sink_block

        self.connect(self.source, self.multiply_const)
        if sink_block is not None:
            self.connect(self.multiply_const, sink_block)

    def set_amplitude(self, amplitude: float) -> None:
        self.multiply_const.set_k(float(amplitude))


__all__ = [
    "GpsL1CaSourceBlock",
    "GpsL1CaTxTopBlock",
    "HAVE_GNURADIO",
    "TxBlockConfig",
    "build_replay_samples",
    "build_tone_replay_samples",
    "make_gps_l1_ca_vector_source",
    "make_tone_vector_source",
]
