from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, generate_ca_code
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT, CyclicNavBitSource


@dataclass
class GeneratorState:
    code_phase: int = 0
    nav_epoch_in_bit: int = 0
    nav_bit_index: int = 0
    sample_phase_in_chip: int = 0


class GpsL1CaBpskGenerator:
    """
    Stateful GPS L1 C/A PRN generator with 50 bps cyclic navigation bits.
    """

    def __init__(
        self,
        prn_id: int = 1,
        samples_per_chip: int = 1,
        amplitude: float = 0.8,
        nav_pattern: Sequence[str | int] | str | None = None,
        initial_code_phase: int = 0,
        initial_nav_epoch: int = 0,
        initial_nav_bit_index: int = 0,
    ) -> None:
        if samples_per_chip <= 0:
            raise ValueError("samples_per_chip must be a positive integer.")

        self.prn_id = prn_id
        self.samples_per_chip = int(samples_per_chip)
        self.amplitude = float(amplitude)
        self.ca_code = generate_ca_code(prn_id)
        self.nav_source = CyclicNavBitSource.from_pattern(nav_pattern)

        if not 0 <= initial_code_phase < CA_CODE_LENGTH:
            raise ValueError(f"initial_code_phase must be in [0, {CA_CODE_LENGTH}).")
        if not 0 <= initial_nav_epoch < CA_EPOCHS_PER_NAV_BIT:
            raise ValueError(f"initial_nav_epoch must be in [0, {CA_EPOCHS_PER_NAV_BIT}).")
        if initial_nav_bit_index < 0:
            raise ValueError("initial_nav_bit_index must be >= 0.")

        self.state = GeneratorState(
            code_phase=int(initial_code_phase),
            nav_epoch_in_bit=int(initial_nav_epoch),
            nav_bit_index=int(initial_nav_bit_index),
            sample_phase_in_chip=0,
        )

    def _current_nav_bit(self) -> int:
        return self.nav_source.bit_at(self.state.nav_bit_index)

    def _current_spread_chip(self) -> np.int8:
        return np.int8(self._current_nav_bit() * self.ca_code[self.state.code_phase])

    def _advance_chip(self) -> None:
        self.state.code_phase += 1
        if self.state.code_phase < CA_CODE_LENGTH:
            return

        self.state.code_phase = 0
        self.state.nav_epoch_in_bit += 1
        if self.state.nav_epoch_in_bit < CA_EPOCHS_PER_NAV_BIT:
            return

        self.state.nav_epoch_in_bit = 0
        self.state.nav_bit_index += 1

    def generate_chips(self, num_chips: int) -> np.ndarray:
        if num_chips < 0:
            raise ValueError("num_chips must be >= 0.")
        if self.state.sample_phase_in_chip != 0:
            raise RuntimeError("Generator is not chip-aligned; finish the current chip first.")

        chips = np.empty(num_chips, dtype=np.int8)
        for index in range(num_chips):
            chips[index] = self._current_spread_chip()
            self._advance_chip()
        return chips

    def generate_samples(self, num_samples: int) -> np.ndarray:
        if num_samples < 0:
            raise ValueError("num_samples must be >= 0.")
        out = np.empty(num_samples, dtype=np.complex64)
        if num_samples == 0:
            return out

        pos_level = np.complex64(self.amplitude + 0j)
        neg_level = np.complex64(-self.amplitude + 0j)

        write_index = 0
        while write_index < num_samples:
            spread_chip = self._current_spread_chip()
            run = min(
                self.samples_per_chip - self.state.sample_phase_in_chip,
                num_samples - write_index,
            )

            out[write_index : write_index + run] = pos_level if spread_chip > 0 else neg_level
            write_index += run
            self.state.sample_phase_in_chip += run

            if self.state.sample_phase_in_chip == self.samples_per_chip:
                self.state.sample_phase_in_chip = 0
                self._advance_chip()

        return out


__all__ = ["GeneratorState", "GpsL1CaBpskGenerator"]
