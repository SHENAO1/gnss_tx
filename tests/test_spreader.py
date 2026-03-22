import unittest

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, generate_ca_code
from gnss_tx.nav.nav_bits import CA_EPOCHS_PER_NAV_BIT
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator


class TestGpsL1CaBpskGenerator(unittest.TestCase):
    def test_first_nav_bit_covers_20_code_epochs(self) -> None:
        code = generate_ca_code(1)
        generator = GpsL1CaBpskGenerator(
            prn_id=1,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1, -1],
        )

        first_bit = generator.generate_samples(CA_CODE_LENGTH * CA_EPOCHS_PER_NAV_BIT).real.astype(np.int8)
        second_bit = generator.generate_samples(CA_CODE_LENGTH * CA_EPOCHS_PER_NAV_BIT).real.astype(np.int8)

        np.testing.assert_array_equal(first_bit, np.tile(code, CA_EPOCHS_PER_NAV_BIT))
        np.testing.assert_array_equal(second_bit, -np.tile(code, CA_EPOCHS_PER_NAV_BIT))

    def test_split_generation_matches_single_shot(self) -> None:
        sample_count = 3000
        single = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=3, amplitude=0.5, nav_pattern=[1, 0, 1])
        split = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=3, amplitude=0.5, nav_pattern=[1, 0, 1])

        expected = single.generate_samples(sample_count)
        actual = np.concatenate(
            [
                split.generate_samples(7),
                split.generate_samples(1001),
                split.generate_samples(2),
                split.generate_samples(sample_count - 1010),
            ]
        )

        np.testing.assert_array_equal(actual, expected)

    def test_sample_repetition_respects_chip_boundaries(self) -> None:
        code = generate_ca_code(1)
        generator = GpsL1CaBpskGenerator(
            prn_id=1,
            samples_per_chip=4,
            amplitude=1.0,
            nav_pattern=[1],
        )

        first_eight = generator.generate_samples(8).real.astype(np.int8)
        np.testing.assert_array_equal(first_eight[:4], np.full(4, code[0], dtype=np.int8))
        np.testing.assert_array_equal(first_eight[4:], np.full(4, code[1], dtype=np.int8))

    def test_one_epoch_correlation_has_expected_sign(self) -> None:
        code = generate_ca_code(1).astype(np.float32)
        positive = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=1, amplitude=1.0, nav_pattern=[1])
        negative = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=1, amplitude=1.0, nav_pattern=[0])

        pos_epoch = positive.generate_samples(CA_CODE_LENGTH).real.astype(np.float32)
        neg_epoch = negative.generate_samples(CA_CODE_LENGTH).real.astype(np.float32)

        self.assertEqual(int(np.dot(pos_epoch, code)), CA_CODE_LENGTH)
        self.assertEqual(int(np.dot(neg_epoch, code)), -CA_CODE_LENGTH)

    def test_state_advances_after_partial_chip_chunk(self) -> None:
        generator = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=4, amplitude=1.0, nav_pattern=[1, -1])

        generator.generate_samples(3)
        self.assertEqual(generator.state.code_phase, 0)
        self.assertEqual(generator.state.sample_phase_in_chip, 3)

        generator.generate_samples(1)
        self.assertEqual(generator.state.code_phase, 1)
        self.assertEqual(generator.state.sample_phase_in_chip, 0)


if __name__ == "__main__":
    unittest.main()
