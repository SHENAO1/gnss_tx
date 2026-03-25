# 双USRP空收实验操作流程（OTA）

**设备分配**
- TX：USRP serial=8003272，天线接 `TX/RX` 口
- RX：USRP serial=193982，天线接 `RX2` 口

**关键参数**
- 中心频率：150 MHz（FM频段外，已规避87.5~108 MHz干扰）
- TX 增益：20 dB
- RX 增益：35 dB
- 采样率：4.092 MHz（PRN1 C/A × 4 采样/chip）

> **注意：100 MHz 位于 FM 广播频段（87.5~108 MHz）。**
> 室内短距离（1~2 m）测试时，TX 信号强度通常远高于 FM 背景，可正常捕获。
> 但若 MATLAB 频谱图中出现强 FM 干扰峰、导致捕获失败，
> 应将两端 `center_freq` 同步改到频段外（如 70 MHz 或 150 MHz）。

---

## 前提条件

- [ ] 两台 USRP 均已通过 USB3 连接主机
- [ ] TX USRP `TX/RX` 口和 RX USRP `RX2` 口均已接天线
- [ ] 两台 USRP 天线相距 **0.5~2 米**，无金属遮挡
- [ ] 共享目录可访问：`/mnt/hgfs/GongXiangDocument/GNSS_RX_Data/`
- [ ] MATLAB 函数软链接已建立（仅需执行一次，见下方步骤0.5）

---

## 步骤0.5：建立 MATLAB 函数软链接（一次性）

MATLAB 运行在 Windows 宿主机，无法直接访问 VM 内 `/home/shen/projects/GNSS_RX/matlab`。
需在 VM 终端执行一次，将 matlab 目录暴露到共享文件夹：

```bash
ln -s /home/shen/projects/GNSS_RX/matlab /mnt/hgfs/GongXiangDocument/GNSS_RX_matlab
```

执行后，Windows 宿主机可通过 `C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab\` 访问。

---

## 步骤0：确认设备识别

```bash
uhd_find_devices
```

预期输出中同时出现：

```
serial: 8003272
serial: 193982
```

---

## 步骤1：dry-run 验证

**终端A（TX）**

```bash
cd /home/shen/projects/gnss_tx
python3 scripts/run_tx.py --dry-run --config configs/tx_b210_sn8003272.yaml
```

确认输出中 `usrp_addr = serial=8003272`，`tx_gain = 20.0`。

**终端B（RX）**

```bash
cd /home/shen/projects/GNSS_RX
PYTHONPATH=src python3 scripts/record_rx.py --dry-run --config configs/rx_prn1_sn193982.yaml
```

确认输出中 `usrp_addr = serial=193982`，`rx_gain_db = 35.0`。

---

## 步骤2：单音校准

**目标**：验证空口链路畅通，确认接收端能看到 TX 发出的信号。

**终端A — 发射单音（持续运行，不要终止）**

```bash
cd /home/shen/projects/gnss_tx
python3 scripts/run_tx.py \
  --config configs/tx_b210_sn8003272.yaml \
  --signal-mode tone \
  --tx-gain 20.0
```

此时 TX 在 150.5 MHz（150 MHz + 500 kHz 偏置）发射单音。

**终端B — 录制 2 秒**

```bash
cd /home/shen/projects/GNSS_RX
PYTHONPATH=src python3 scripts/record_rx.py \
  --config configs/rx_prn1_sn193982.yaml \
  --duration 2
```

**MATLAB 验证**

```matlab
addpath('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab\functions')
addpath('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab\scripts')
result = run_capture_analysis();
```

打开 `overview_spectrum.png`，确认在 **500 kHz 处出现明显单音峰值**。

- [ ] 单音校准通过

---

## 步骤3：扩频信号采集

**终端A — 停止单音（Ctrl+C），切换为扩频**

```bash
cd /home/shen/projects/gnss_tx
python3 scripts/run_tx.py --config configs/tx_b210_sn8003272.yaml
```

等待约 3 秒，TX 输出稳定后再采集。

**终端B — 录制 2 秒**

```bash
 
```

采集完成后，输出文件位于：

```
/mnt/hgfs/GongXiangDocument/GNSS_RX_Data/<YYYY>/<YYYY-MM-DD>/
  <stem>.sc16
  <stem>.json
```

建议重复采集 3 次，验证可重复性：

```bash
for i in 1 2 3; do
  PYTHONPATH=src python3 scripts/record_rx.py \
    --config configs/rx_prn1_sn193982.yaml \
    --duration 2
  sleep 5
done
```

---

## 步骤4：MATLAB 离线分析

```matlab
addpath('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab\functions')
addpath('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab\scripts')

% 自动分析最新采集文件
result = run_capture_analysis();

% 查看捕获结果
result.acq_result
```

**通过判据**

| 检查项 | 期望值 |
|--------|--------|
| `result.acq_result.detected` | `true` |
| `result.acq_result.peak_metric` | ≥ 2.5 |
| `result.acq_result.best_doppler_hz` | 接近 0 Hz（两台设备静止，无相对运动） |
| `overview_spectrum.png` | 约 4 MHz 宽扩频平台，可能叠加 FM 背景 |
| `iq_scatter.png` | 两个 BPSK 星座点（±实轴） |

- [ ] 扩频采集与捕获分析通过

---

## 步骤5：停止发射端

在终端A按 `Ctrl+C` 停止发射。

---

## 增益调整建议

若捕获失败，按以下顺序尝试：

| 问题现象 | 调整方法 |
|---------|---------|
| 频谱图完全平坦，无任何信号 | TX 增益提高到 30 dB（`--tx-gain 30`），或缩短两台天线距离 |
| RX 频谱饱和/削波 | RX 增益降低到 20 dB（`--rx-gain 20`） |
| 有明显 FM 峰值干扰，捕获失败 | 将两端 `center_freq` 同步改为 70 MHz 或 150 MHz（FM 频段外） |
| `detected=false` 但有扩频平台 | 将采集时长改为 5 秒（`--duration 5`），MATLAB 中 `noncoherent_ms` 改为 20 |
| Doppler 偏差较大 | MATLAB 中 `doppler_step_hz` 改为 250，扩大 `doppler_max_hz` 到 20000 |

---

## 故障排查

| 现象 | 处理方法 |
|------|---------|
| `uhd_find_devices` 只看到一台 | 检查 USB 线缆和 USB3 端口，重新插拔；确认两台分别独立供电 |
| dry-run 报设备未找到 | 单独探测：`uhd_usrp_probe --args serial=8003272` |
| USRP underflow 警告 | 正常现象，不影响采集质量 |
| TX 启动后立即崩溃 | 检查 Python 路径：`cd gnss_tx` 后再运行，不要在其他目录执行 |

---

## 使用的配置文件

- TX：[configs/tx_b210_sn8003272.yaml](../configs/tx_b210_sn8003272.yaml)（tx_gain=20 dB）
- RX：[GNSS_RX/configs/rx_prn1_sn193982.yaml](../../GNSS_RX/configs/rx_prn1_sn193982.yaml)（rx_gain=35 dB）
