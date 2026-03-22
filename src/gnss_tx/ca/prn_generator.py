from __future__ import annotations

import numpy as np

CA_CODE_LENGTH = 1023

_PRN_G2_TAPS: dict[int, tuple[int, int]] = {
    1: (2, 6),
}


def generate_ca_code(prn_id: int) -> np.ndarray:
    """
    Generate one GPS L1 C/A epoch as int8 chips in +/-1 representation.

    Only PRN1 is implemented in v1, but the interface keeps ``prn_id``
    configurable for future expansion.
    """
    if prn_id not in _PRN_G2_TAPS:
        raise NotImplementedError(f"Only PRN1 is implemented in v1, got PRN {prn_id}.")

    g1 = np.ones(10, dtype=np.uint8)
    g2 = np.ones(10, dtype=np.uint8)
    tap_a, tap_b = _PRN_G2_TAPS[prn_id]

    code = np.empty(CA_CODE_LENGTH, dtype=np.int8)
    for index in range(CA_CODE_LENGTH):
        g1_out = g1[9]
        g2_out = g2[tap_a - 1] ^ g2[tap_b - 1]
        code[index] = 1 if (g1_out ^ g2_out) == 0 else -1

        g1_feedback = g1[2] ^ g1[9]
        g2_feedback = g2[1] ^ g2[2] ^ g2[5] ^ g2[7] ^ g2[8] ^ g2[9]

        g1[1:] = g1[:-1]
        g1[0] = g1_feedback

        g2[1:] = g2[:-1]
        g2[0] = g2_feedback

    return code


__all__ = ["CA_CODE_LENGTH", "generate_ca_code"]
