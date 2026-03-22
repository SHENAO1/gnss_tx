import unittest
import os

import numpy as np
from gnuradio import blocks, gr
from PyQt5 import QtWidgets

from gnss_tx.gr.top_block import (
    GpsL1CaSourceBlock,
    GpsL1CaTxTopBlock,
    TxBlockConfig,
    build_replay_samples,
    make_gps_l1_ca_vector_source,
)
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator


class TestGpsL1CaSourceBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        cls.qt_app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def test_block_outputs_complex64_samples(self) -> None:
        block = GpsL1CaSourceBlock(prn_id=1, samples_per_chip=2, amplitude=0.25, nav_pattern=[1, -1])
        output = np.empty(17, dtype=np.complex64)

        produced = block.work([], [output])

        self.assertEqual(produced, 17)
        self.assertEqual(output.dtype, np.complex64)
        self.assertTrue(np.all(np.isreal(output)))

    def test_block_uses_same_state_machine_as_reference_generator(self) -> None:
        reference = GpsL1CaBpskGenerator(
            prn_id=1,
            samples_per_chip=2,
            amplitude=0.75,
            nav_pattern=[1, 0, 1],
        )
        block = GpsL1CaSourceBlock(
            prn_id=1,
            samples_per_chip=2,
            amplitude=0.75,
            nav_pattern=[1, 0, 1],
        )

        expected = reference.generate_samples(64)
        out_a = np.empty(7, dtype=np.complex64)
        out_b = np.empty(57, dtype=np.complex64)

        block.work([], [out_a])
        block.work([], [out_b])
        actual = np.concatenate([out_a, out_b])

        np.testing.assert_array_equal(actual, expected)

    def test_replay_samples_cover_full_nav_pattern_period(self) -> None:
        replay = build_replay_samples(
            prn_id=1,
            samples_per_chip=2,
            amplitude=0.5,
            nav_pattern=[1, 0, 1],
        )
        expected_len = 3 * 20 * 1023 * 2
        self.assertEqual(len(replay), expected_len)
        self.assertEqual(replay.dtype, np.complex64)

    def test_vector_source_repeats_replay_buffer(self) -> None:
        reference = build_replay_samples(
            prn_id=1,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1, -1],
        )
        source = make_gps_l1_ca_vector_source(
            prn_id=1,
            samples_per_chip=1,
            amplitude=1.0,
            nav_pattern=[1, -1],
        )
        tb = gr.top_block()
        head = blocks.head(gr.sizeof_gr_complex, len(reference) + 16)
        sink = blocks.vector_sink_c()
        tb.connect(source, head, sink)
        tb.run()

        combined = np.array(sink.data(), dtype=np.complex64)
        tiled = np.tile(reference, 2)
        np.testing.assert_array_equal(combined, tiled[: len(reference) + 16])

    def test_tx_top_block_without_qt_preview_builds_without_preview_widgets(self) -> None:
        tb = GpsL1CaTxTopBlock(
            TxBlockConfig(
                signal_mode="spread",
                samples_per_chip=1,
                sample_rate=1.023e6,
                enable_qt_preview=False,
            ),
            sink_block=None,
        )
        self.assertIsNone(tb.preview_window)

    def test_tx_top_block_with_qt_preview_constructs_preview_widgets(self) -> None:
        tb = GpsL1CaTxTopBlock(
            TxBlockConfig(
                signal_mode="spread",
                samples_per_chip=1,
                sample_rate=1.023e6,
                enable_qt_preview=True,
            ),
            sink_block=None,
        )
        self.assertIsNotNone(tb.preview_window)
        self.assertIsNotNone(tb.qt_time_sink)
        self.assertIsNotNone(tb.qt_freq_sink)


if __name__ == "__main__":
    unittest.main()
