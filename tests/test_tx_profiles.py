import unittest
from pathlib import Path

from gnss_tx.usrp.tx_controller import load_tx_runtime_config


class TestTxProfiles(unittest.TestCase):
    def test_safe_baseline_profile_is_conservative(self) -> None:
        config = load_tx_runtime_config(Path("configs/tx_b210.yaml"))
        self.assertEqual(config.tx_gain, 0.0)
        self.assertEqual(config.amplitude, 0.25)

    def test_visible_spectrum_profile_matches_checkpoint(self) -> None:
        config = load_tx_runtime_config(Path("configs/tx_b210_visible_spectrum.yaml"))
        self.assertEqual(config.tx_gain, 10.0)
        self.assertEqual(config.amplitude, 0.5)
        self.assertEqual(config.signal_mode, "spread")


if __name__ == "__main__":
    unittest.main()
