from __future__ import annotations

from gnss_tx.gr.top_block import TxBlockConfig

try:
    from gnuradio import uhd
except ImportError:  # pragma: no cover - optional in test environments
    uhd = None

HAVE_UHD = uhd is not None


def create_b210_sink(config: TxBlockConfig):
    if not HAVE_UHD:
        raise RuntimeError("GNU Radio UHD bindings are not available.")

    sink = uhd.usrp_sink(
        ",".join(part for part in [config.usrp_addr] if part),
        uhd.stream_args(cpu_format="fc32", otw_format="sc16", channels=[0]),
        "",
    )
    sink.set_samp_rate(float(config.sample_rate))
    sink.set_center_freq(float(config.center_freq), 0)
    sink.set_antenna(str(config.antenna), 0)

    if config.bandwidth is not None:
        sink.set_bandwidth(float(config.bandwidth), 0)

    if config.tx_gain is None:
        gain = float(sink.get_gain_range(0).start())
    else:
        gain = float(config.tx_gain)
    sink.set_gain(gain, 0)

    return sink


__all__ = ["HAVE_UHD", "create_b210_sink"]
