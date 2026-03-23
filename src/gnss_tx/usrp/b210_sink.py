from __future__ import annotations

from gnss_tx.gr.top_block import TxBlockConfig

try:
    from gnuradio import uhd
except ImportError:  # pragma: no cover - optional in test environments
    uhd = None

HAVE_UHD = uhd is not None


def create_b210_sink(config: TxBlockConfig):
    """
    根据运行时配置创建 UHD B210 发射端。

    物理意义：
    - ``sample_rate`` 决定 USRP 从主机接收数字基带 sample 的速率。
    - ``center_freq`` 决定射频搬移后的中心频率。
    - ``tx_gain`` 控制发射增益。
    - ``bandwidth`` 是 USRP 端模拟/数字链路的带宽设置。
    """
    if not HAVE_UHD:
        raise RuntimeError("GNU Radio UHD bindings are not available.")

    sink = uhd.usrp_sink(
        ",".join(part for part in [config.usrp_addr] if part),
        uhd.stream_args(cpu_format="fc32", otw_format="sc16", channels=[0]),
        "",
    )
    # 主机侧产生的 complex baseband sample 以该速率送入 USRP。
    sink.set_samp_rate(float(config.sample_rate))
    # 数字基带会上变频到这个射频中心频率附近发出。
    sink.set_center_freq(float(config.center_freq), 0)
    sink.set_antenna(str(config.antenna), 0)

    if config.bandwidth is not None:
        sink.set_bandwidth(float(config.bandwidth), 0)

    if config.tx_gain is None:
        # 未显式指定增益时，使用设备支持范围中的最小值作为保守起点。
        gain = float(sink.get_gain_range(0).start())
    else:
        gain = float(config.tx_gain)
    sink.set_gain(gain, 0)

    return sink


__all__ = ["HAVE_UHD", "create_b210_sink"]
