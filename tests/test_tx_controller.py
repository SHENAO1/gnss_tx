import tempfile
import unittest
from pathlib import Path

from gnss_tx.usrp.tx_controller import (
    GPS_CA_CHIP_RATE,
    TxRuntimeConfig,
    apply_overrides,
    format_config_report,
    format_observation_checklist,
    load_tx_runtime_config,
)


class TestTxController(unittest.TestCase):
    def test_load_tx_runtime_config_derives_bandwidth(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "tx.yaml"
            path.write_text(
                "\n".join(
                    [
                        "prn_id: 1",
                        "usrp_addr: \"type=b200\"",
                        "center_freq: 100000000.0",
                        "samples_per_chip: 4",
                        "sample_rate: 4092000.0",
                        "tx_gain: 0.0",
                        "amplitude: 0.25",
                        "antenna: \"TX/RX\"",
                        "nav_pattern: \"1 0 1 1 0 0 1 0\"",
                        "continuous: true",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_tx_runtime_config(path)

        self.assertEqual(config.bandwidth, 4092000.0)
        self.assertEqual(config.samples_per_chip, 4)

    def test_apply_overrides_updates_sample_rate_from_samples_per_chip(self) -> None:
        config = TxRuntimeConfig().validate()

        updated = apply_overrides(config, samples_per_chip=8)

        self.assertEqual(updated.sample_rate, GPS_CA_CHIP_RATE * 8)
        self.assertEqual(updated.bandwidth, GPS_CA_CHIP_RATE * 8)

    def test_report_contains_safety_text(self) -> None:
        report = format_config_report(TxRuntimeConfig().validate())
        self.assertIn("Spectrum analyzer max input", report)
        self.assertIn("Safety reminder", report)

    def test_observation_checklist_mentions_frequency_and_span(self) -> None:
        checklist = format_observation_checklist(TxRuntimeConfig().validate())
        self.assertIn("100.000 MHz", checklist)
        self.assertIn("20 MHz", checklist)
        self.assertIn("TX/RX", checklist)

    def test_tone_mode_accepts_non_chip_rate_sample_rate(self) -> None:
        config = TxRuntimeConfig(
            signal_mode="tone",
            sample_rate=2_000_000.0,
            samples_per_chip=4,
            tone_offset_hz=250_000.0,
        ).validate()
        self.assertEqual(config.signal_mode, "tone")

    def test_spread_mode_still_requires_chip_rate_sample_rate(self) -> None:
        with self.assertRaises(ValueError):
            TxRuntimeConfig(signal_mode="spread", sample_rate=2_000_000.0).validate()


if __name__ == "__main__":
    unittest.main()
