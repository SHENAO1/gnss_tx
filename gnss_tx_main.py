#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: GNSS TX PRN1 B210
# GNU Radio version: 3.10.9.2

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
_p = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
_PROJECT_ROOT = next(
    (d for d in [_p] + list(_p.parents) if (d / "src" / "gnss_tx").exists()), _p
)
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))
from gnss_tx.gr import make_gps_l1_ca_vector_source
from gnuradio import uhd
_p = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd()
_PROJECT_ROOT = next(
    (d for d in [_p] + list(_p.parents) if (d / "src" / "gnss_tx").exists()), _p
)
_SRC_PATH = _PROJECT_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))
from gnss_tx.usrp import format_uhd_tx_sample_rate_report



class gnss_tx_main(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "GNSS TX PRN1 B210", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("GNSS TX PRN1 B210")
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
        self.samples_per_chip = samples_per_chip = 4
        self.usrp_addr = usrp_addr = "type=b200"
        self.tx_gain = tx_gain = 0.0
        self.samp_rate = samp_rate = 1.023e6 * samples_per_chip
        self.nav_pattern = nav_pattern = "1 0 1 1 0 0 1 0"
        self.center_freq = center_freq = 100e6
        self.amplitude = amplitude = 1.0

        ##################################################
        # Blocks
        ##################################################

        self.usrp_sink = uhd.usrp_sink(
            ",".join(part for part in (usrp_addr,) if part),
            uhd.stream_args(
                cpu_format="fc32",
                channels=[0],
            ),
            "",
        )
        self.usrp_sink.set_samp_rate(float(samp_rate))
        self.usrp_sink.set_center_freq(float(center_freq), 0)
        self.usrp_sink.set_gain(float(tx_gain), 0)
        self.usrp_sink.set_antenna("TX/RX", 0)
        self.usrp_sink.set_bandwidth(float(samp_rate), 0)
        print(format_uhd_tx_sample_rate_report(samp_rate, self.usrp_sink, label="GNU Radio USRP sink"))
        self.qt_time = qtgui.time_sink_c(
            512, #size
            samp_rate, #samp_rate
            "PRN1 Baseband Time", #name
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
        self.qt_freq = qtgui.freq_sink_c(
            2048, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            center_freq, #fc
            samp_rate, #bw
            "PRN1 Baseband Spectrum", #name
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



        labels = ["PRN1 RF Preview", '', '', '', '',
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
        self.prn_source = make_gps_l1_ca_vector_source(
            prn_id=1,
            samples_per_chip=samples_per_chip,
            amplitude=1.0,
            nav_pattern=nav_pattern,
            initial_code_phase=0,
            initial_nav_epoch=0,
            initial_nav_bit_index=0,
        )
        self.amplitude_scale = blocks.multiply_const_cc(amplitude)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.amplitude_scale, 0), (self.qt_freq, 0))
        self.connect((self.amplitude_scale, 0), (self.qt_time, 0))
        self.connect((self.amplitude_scale, 0), (self.usrp_sink, 0))
        self.connect((self.prn_source, 0), (self.amplitude_scale, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "gnss_tx_main")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samples_per_chip(self):
        return self.samples_per_chip

    def set_samples_per_chip(self, samples_per_chip):
        self.samples_per_chip = samples_per_chip
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
        self.qt_time.set_samp_rate(self.samp_rate)
        self.qt_freq.set_frequency_range(self.center_freq, self.samp_rate)
        self.usrp_sink.set_samp_rate(self.samp_rate)
        self.usrp_sink.set_bandwidth(self.samp_rate, 0)

    def get_nav_pattern(self):
        return self.nav_pattern

    def set_nav_pattern(self, nav_pattern):
        self.nav_pattern = nav_pattern

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.qt_freq.set_frequency_range(self.center_freq, self.samp_rate)
        self.usrp_sink.set_center_freq(self.center_freq, 0)

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
        self.amplitude_scale.set_k(self.amplitude)




def main(top_block_cls=gnss_tx_main, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
