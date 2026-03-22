import unittest

import numpy as np

from gnss_tx.nav.nav_bits import CyclicNavBitSource, normalize_nav_bits


class TestNavBits(unittest.TestCase):
    def test_normalize_nav_bits_maps_zero_to_minus_one(self) -> None:
        bits = normalize_nav_bits([1, 0, -1, "1", "0", "-"])
        expected = np.array([1, -1, -1, 1, -1, -1], dtype=np.int8)
        np.testing.assert_array_equal(bits, expected)

    def test_default_pattern_is_non_empty_and_binary(self) -> None:
        bits = normalize_nav_bits()
        self.assertGreater(bits.size, 0)
        self.assertTrue(np.all(np.isin(bits, (-1, 1))))

    def test_cyclic_source_wraps_indices(self) -> None:
        source = CyclicNavBitSource.from_pattern([1, -1, 1])
        self.assertEqual(source.bit_at(0), 1)
        self.assertEqual(source.bit_at(1), -1)
        self.assertEqual(source.bit_at(3), 1)
        self.assertEqual(source.bit_at(4), -1)


if __name__ == "__main__":
    unittest.main()
