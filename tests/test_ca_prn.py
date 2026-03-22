import unittest

import numpy as np

from gnss_tx.ca.prn_generator import CA_CODE_LENGTH, generate_ca_code


class TestCaPrnGenerator(unittest.TestCase):
    def test_prn1_has_expected_length_and_symbols(self) -> None:
        code = generate_ca_code(1)
        self.assertEqual(code.shape, (CA_CODE_LENGTH,))
        self.assertEqual(code.dtype, np.int8)
        self.assertTrue(np.all(np.isin(code, (-1, 1))))

    def test_prn1_is_balanced(self) -> None:
        code = generate_ca_code(1)
        self.assertEqual(abs(int(code.sum())), 1)

    def test_prn1_periodic_autocorrelation_peaks_at_zero_shift(self) -> None:
        code = generate_ca_code(1).astype(np.int32)
        correlations = np.array(
            [int(np.dot(code, np.roll(code, shift))) for shift in range(CA_CODE_LENGTH)],
            dtype=np.int32,
        )
        self.assertEqual(int(correlations[0]), CA_CODE_LENGTH)
        self.assertLessEqual(int(np.max(np.abs(correlations[1:]))), 65)

    def test_unknown_prn_is_rejected_in_v1(self) -> None:
        with self.assertRaises(NotImplementedError):
            generate_ca_code(2)


if __name__ == "__main__":
    unittest.main()
