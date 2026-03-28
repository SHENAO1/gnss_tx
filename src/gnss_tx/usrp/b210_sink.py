from __future__ import annotations

from gnss_tx.gr.top_block import TxBlockConfig

# `uhd` 来自 GNU Radio 的 UHD 模块，用于控制 USRP 设备。
# 在某些测试环境里不会安装 UHD，因此这里做“可选导入”。
try:
    from gnuradio import uhd
except ImportError:  # pragma: no cover - optional in test environments
    uhd = None

# 对外暴露一个布尔标志，调用方可据此判断当前环境是否具备 UHD 能力。
HAVE_UHD = uhd is not None


def create_b210_sink(config: TxBlockConfig):
    """
    根据运行时配置创建 UHD B210 发射端。

    物理意义：
    - ``sample_rate`` 决定 USRP 从主机接收数字基带 sample 的速率。
    - ``center_freq`` 决定射频搬移后的中心频率。
    - ``tx_gain`` 控制发射增益。
    - ``bandwidth`` 是 USRP 端模拟/数字链路的带宽设置。

    返回值：
    - 一个已完成基础参数配置的 `uhd.usrp_sink` 对象。
      上层 flowgraph 会把复数基带流连接到该 sink，最终由硬件发射。
    """
    # 早失败（fail fast）：如果当前 Python 环境没有 UHD 绑定，
    # 直接给出明确错误，避免后续出现更难理解的 AttributeError。
    if not HAVE_UHD:
        raise RuntimeError("GNU Radio UHD bindings are not available.")

    # 创建 UHD 发射 sink。
    # 1) 设备地址字符串：例如 "type=b200" 或者带 serial 的地址。
    # 2) stream_args：
    #    - cpu_format="fc32" 表示主机侧使用 complex float32 数据。
    #    - otw_format="sc16" 表示发往设备链路时使用 complex int16 格式。
    #    - channels=[0] 仅启用第 0 路 TX 通道。
    # 3) 第三个参数是设备参数字符串，这里留空表示使用默认设置。
    # 增大 USB 发送缓冲区以减少 underflow：
    #   send_frame_size=4104  — 每帧样本数（8 的倍数且非 1024 的倍数）
    #   num_send_frames=512   — 缓冲帧数
    device_addr = ",".join(
        part for part in [
            config.usrp_addr,
            "send_frame_size=4104",
            "num_send_frames=512",
        ] if part
    )
    sink = uhd.usrp_sink(
        device_addr,
        uhd.stream_args(cpu_format="fc32", otw_format="sc16", channels=[0]),
        "",
    )
    # 主机侧产生的 complex baseband sample 以该速率送入 USRP。
    sink.set_samp_rate(float(config.sample_rate))
    # 数字基带会上变频到这个射频中心频率附近发出。
    sink.set_center_freq(float(config.center_freq), 0)
    # 选择发射天线端口（例如 B210 常见的 "TX/RX"）。
    sink.set_antenna(str(config.antenna), 0)

    # 带宽是可选项：未提供时，交给 UHD/硬件使用默认值。
    if config.bandwidth is not None:
        sink.set_bandwidth(float(config.bandwidth), 0)

    if config.tx_gain is None:
        # 未显式指定增益时，使用设备支持范围中的最小值作为保守起点。
        # 这样做更安全，适合首次连线或不确定外部仪器承受能力时。
        gain = float(sink.get_gain_range(0).start())
    else:
        # 若用户显式给了增益，则按用户指定值设置。
        gain = float(config.tx_gain)
    # 将最终增益写入第 0 路发射通道。
    sink.set_gain(gain, 0)

    # 返回已配置好的 sink，供上层 GNU Radio 拓扑继续连接与启动。
    return sink


__all__ = ["HAVE_UHD", "create_b210_sink"]
