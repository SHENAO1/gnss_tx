#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: GNSS TX Single-Sat B210
# GNU Radio version: 3.10.9.2

"""
这个文件实现了一个最小可运行的 GNSS 发射示例：

1. 先生成某一颗 GPS L1 C/A 卫星的基带复数信号。
2. 再对信号做幅度缩放。
3. 一路送到 Qt 图形界面里做时域/频域观察。
4. 另一路送到 USRP B210 做实际发射。

如果你是第一次看 GNU Radio，可以把它理解成：
"先搭木块(block)，再把木块用 connect 串起来，形成一条信号流水线。"
"""

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import sip
from pathlib import Path

# 让脚本在直接运行时也能找到项目里的 `src/gnss_tx` 包。
# 这一步相当于手动把源码目录加入 Python 的模块搜索路径。
_p = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
_PROJECT_ROOT = next(
    (d for d in [_p] + list(_p.parents) if (d / "src" / "gnss_tx").exists()), _p
)
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))
from gnss_tx.gr import make_gps_l1_ca_vector_source
from gnuradio import uhd

# 这里再次补一次路径，作用与上面相同。
# 文件可能经过 GRC 生成和后处理，所以保留了这一段重复逻辑。
_p = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
_PROJECT_ROOT = next(
    (d for d in [_p] + list(_p.parents) if (d / "src" / "gnss_tx").exists()), _p
)
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))
from gnss_tx.usrp import format_uhd_tx_sample_rate_report



class gnss_tx_main(gr.top_block, Qt.QWidget):
    """GNU Radio 顶层流图 + Qt 主窗口。"""

    def __init__(self):
        # `gr.top_block` 负责整条信号流的启动/停止；
        # `Qt.QWidget` 负责图形界面窗口。
        gr.top_block.__init__(self, "GNSS TX Single-Sat B210", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("GNSS TX Single-Sat B210")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        # 用 Qt 的配置存储窗口大小、位置等 GUI 状态，
        # 这样下次打开时界面会尽量恢复到上次的样子。
        self.settings = Qt.QSettings("GNU Radio", "gnss_tx_main")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        # 每个码片(chip)用多少个采样点表示。
        # 值越大，采样率越高，波形显示更细，但硬件负担也更大。
        self.samples_per_chip = samples_per_chip = 4

        # UHD/USRP 的设备地址。`type=b200` 可以匹配 B200/B210 系列设备。
        self.usrp_addr = usrp_addr = "type=b200"

        # 发射增益，单位通常可理解为 dB 附近的硬件增益控制量。
        self.tx_gain = tx_gain = 0.0

        # GPS L1 C/A 的码片率是 1.023 MHz。
        # 这里的采样率 = 码片率 * 每码片采样点数。
        self.samp_rate = samp_rate = 1.023e6 * samples_per_chip

        # 选择哪颗卫星的 PRN 码。PRN 可以理解为"卫星的伪随机编号"。
        self.prn_id = prn_id = 1

        # 导航比特模式。这里用一个简化的固定比特序列反复发送。
        self.nav_pattern = nav_pattern = "1 0 1 1 0 0 1 0"

        # USRP 实际发射到射频时使用的中心频率。
        # 当前默认是 100 MHz，便于实验；并不是 GPS L1 真正的 1575.42 MHz。
        self.center_freq = center_freq = 100e6

        # 软件里的复数基带幅度缩放系数。
        self.amplitude = amplitude = 1.0

        ##################################################
        # Blocks
        ##################################################

        # USRP 发射端。它是整条链路最终把样本送到硬件的出口。
        self.usrp_sink = uhd.usrp_sink(
            ",".join(part for part in (usrp_addr,) if part),
            uhd.stream_args(
                cpu_format="fc32",
                channels=[0],
            ),
            "",
        )
        # 下面这些配置分别告诉硬件：
        # - 以什么采样率取走数据
        # - 发射到哪个中心频率
        # - 用多少发射增益
        # - 使用哪个天线口
        # - 模拟带宽设置多少
        self.usrp_sink.set_samp_rate(float(samp_rate))
        self.usrp_sink.set_center_freq(float(center_freq), 0)
        self.usrp_sink.set_gain(float(tx_gain), 0)
        self.usrp_sink.set_antenna("TX/RX", 0)
        self.usrp_sink.set_bandwidth(float(samp_rate), 0)

        # 打印实际采样率配置结果，方便确认 UHD 是否做了重采样或取整。
        print(format_uhd_tx_sample_rate_report(samp_rate, self.usrp_sink, label="GNU Radio USRP sink"))

        # 时域观察窗口：显示复数信号的 I/Q 波形。
        self.qt_time = qtgui.time_sink_c(
            512, #size
            samp_rate, #samp_rate
            "Selected PRN Baseband Time", #name
            1, #number of inputs
            None # parent
        )
        self.qt_time.set_update_time(0.10)
        self.qt_time.set_y_axis(-1.2, 1.2)

        self.qt_time.set_y_label('Amplitude', "")

        self.qt_time.enable_tags(False)
        self.qt_time.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qt_time.enable_autoscale(False)
        self.qt_time.enable_grid(True)
        self.qt_time.enable_axis_labels(True)
        self.qt_time.enable_control_panel(False)
        self.qt_time.enable_stem_plot(False)


        # 为时域图的每条曲线设置显示名称/颜色/线型。
        # 对复数信号来说，前两条线通常就是 I 和 Q。
        labels = ['I', 'Q', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'red', 'green', 'black', 'cyan',
            'magenta', 'yellow', 'dark red', 'dark green', 'dark blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(2):
            if len(labels[i]) == 0:
                if (i % 2 == 0):
                    self.qt_time.set_line_label(i, "Re{{Data {0}}}".format(i/2))
                else:
                    self.qt_time.set_line_label(i, "Im{{Data {0}}}".format(i/2))
            else:
                self.qt_time.set_line_label(i, labels[i])
            self.qt_time.set_line_width(i, widths[i])
            self.qt_time.set_line_color(i, colors[i])
            self.qt_time.set_line_style(i, styles[i])
            self.qt_time.set_line_marker(i, markers[i])
            self.qt_time.set_line_alpha(i, alphas[i])

        self._qt_time_win = sip.wrapinstance(self.qt_time.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qt_time_win, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)

        # 频域观察窗口：看当前输出信号在频谱上的分布。
        self.qt_freq = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            center_freq, #fc
            samp_rate, #bw
            "Selected PRN Baseband Spectrum", #name
            1,
            None # parent
        )
        self.qt_freq.set_update_time(0.10)
        self.qt_freq.set_y_axis((-120), 10)
        self.qt_freq.set_y_label('Relative Gain', 'dB')
        self.qt_freq.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qt_freq.enable_autoscale(False)
        self.qt_freq.enable_grid(True)
        self.qt_freq.set_fft_average(0.2)
        self.qt_freq.enable_axis_labels(True)
        self.qt_freq.enable_control_panel(False)
        self.qt_freq.set_fft_window_normalized(False)


        # 频谱图一般只画一路复数输入，因此这里只配置第一条曲线标签。
        labels = ["Selected PRN RF Preview", '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qt_freq.set_line_label(i, "Data {0}".format(i))
            else:
                self.qt_freq.set_line_label(i, labels[i])
            self.qt_freq.set_line_width(i, widths[i])
            self.qt_freq.set_line_color(i, colors[i])
            self.qt_freq.set_line_alpha(i, alphas[i])

        self._qt_freq_win = sip.wrapinstance(self.qt_freq.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qt_freq_win, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)

        # 自定义信号源：生成指定 PRN 的 GPS L1 C/A 基带复数样本。
        # 这里的输出还停留在"基带"层面，也就是还没搬移到真正的射频频点。
        self.prn_source = make_gps_l1_ca_vector_source(
            prn_id=prn_id,
            samples_per_chip=samples_per_chip,
            amplitude=1.0,
            nav_pattern=nav_pattern,
            initial_code_phase=0,
            initial_nav_epoch=0,
            initial_nav_bit_index=0,
        )

        # 乘常数块：最简单的幅度控制器，输入乘以 amplitude 后输出。
        self.amplitude_scale = blocks.multiply_const_cc(amplitude)


        ##################################################
        # Connections
        ##################################################
        # 这 4 行就是完整的信号流向：
        # PRN 源 -> 幅度缩放 -> 频谱显示 / 时域显示 / USRP 发射
        self.connect((self.amplitude_scale, 0), (self.qt_freq, 0))
        self.connect((self.amplitude_scale, 0), (self.qt_time, 0))
        self.connect((self.amplitude_scale, 0), (self.usrp_sink, 0))
        self.connect((self.prn_source, 0), (self.amplitude_scale, 0))


    def closeEvent(self, event):
        # 关闭窗口时，先保存 GUI 状态，再优雅地停掉流图线程。
        self.settings = Qt.QSettings("GNU Radio", "gnss_tx_main")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samples_per_chip(self):
        return self.samples_per_chip

    def set_samples_per_chip(self, samples_per_chip):
        self.samples_per_chip = samples_per_chip
        # 码片采样数变化后，整体采样率也必须同步变化。
        self.set_samp_rate(1.023e6 * self.samples_per_chip)

    def get_usrp_addr(self):
        return self.usrp_addr

    def set_usrp_addr(self, usrp_addr):
        self.usrp_addr = usrp_addr

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain
        self.usrp_sink.set_gain(self.tx_gain, 0)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        # 采样率一旦改变，相关的显示控件和硬件参数都要一起更新。
        self.qt_time.set_samp_rate(self.samp_rate)
        self.qt_freq.set_frequency_range(self.center_freq, self.samp_rate)
        self.usrp_sink.set_samp_rate(self.samp_rate)
        self.usrp_sink.set_bandwidth(self.samp_rate, 0)

    def get_nav_pattern(self):
        return self.nav_pattern

    def set_nav_pattern(self, nav_pattern):
        self.nav_pattern = nav_pattern

    def get_prn_id(self):
        return self.prn_id

    def set_prn_id(self, prn_id):
        self.prn_id = prn_id

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        # 同时更新频谱横轴显示和 USRP 的实际发射中心频率。
        self.qt_freq.set_frequency_range(self.center_freq, self.samp_rate)
        self.usrp_sink.set_center_freq(self.center_freq, 0)

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
        self.amplitude_scale.set_k(self.amplitude)




def main(top_block_cls=gnss_tx_main, options=None):
    # Qt 应用对象：所有 GUI 程序都需要先创建它。

    qapp = Qt.QApplication(sys.argv)

    # 创建并启动 GNU Radio 顶层流图。
    tb = top_block_cls()

    tb.start()

    # 显示主窗口。此时图形界面和信号流会同时运行。
    tb.show()

    def sig_handler(sig=None, frame=None):
        # 响应 Ctrl+C 或进程结束信号，确保硬件和线程被正确关闭。
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    # 定时器用于维持 Qt 事件循环的活跃状态，
    # 这是 GNU Radio Qt 程序里比较常见的写法。
    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
