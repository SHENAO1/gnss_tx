# 发端功率摸底测试记录

> 创建时间：2026-03-27
> 测试目的：确定两台 USRP B210 直连（不加衰减器）时安全的 tx_gain 和 amplitude 范围
> 测试阶段：发端独立测试（TX → 频谱仪），频谱确认后再接 RX

---

## 一、背景与安全边界回顾

| 参数 | 数值 | 来源 |
|------|------|------|
| B210 TX 最大输出 | > +10 dBm | B210 Spec Sheet |
| AD9361 RX 绝对最大输入（峰值） | **+2.5 dBm** | AD9361 Table 11 |
| 目标 RX 安全输入 | ≤ −10 dBm | 保守裕量 12.5 dB |
| TX 输出估算公式 | `P_tx ≈ tx_gain − 79.75 dBm`（100 MHz） | 手册推算 |
| GPS 扩频信号 PAPR | 约 0~3 dB | 频谱仪平均值需加 3 dB 估算峰值 |

**无衰减器时 tx_gain 硬性上限：70 dB（对应 RX 输入 ≈ −11 dBm）**

### TX 输出估算公式推导

公式 `P_tx ≈ tx_gain − 79.75 dBm` 是基于 B210 Spec Sheet 倒推的经验估算，推导过程如下：

```
B210 TX 增益范围（UHD 驱动）：0 ~ 89.75 dB
B210 手册标称最大输出：> +10 dBm（对应 tx_gain = 89.75 dB）

倒推 offset：
  offset = 89.75 − 10 = 79.75 dB

→ P_tx ≈ tx_gain − 79.75 dBm（amplitude = 1.0 时）
```

`amplitude` 参数为数字域线性增益，对输出功率的影响：

```
P_tx = (tx_gain − 79.75) + 20·log₁₀(amplitude)  dBm

例：tx_gain=70, amplitude=0.5
  → (70 − 79.75) + 20·log₁₀(0.5) = −9.75 + (−6) = −15.75 dBm
```

**此公式的局限性：**
- `offset = 79.75` 是由标称最大值凑出的经验值，非手册直接给出的公式
- B210 实际输出因频点而异，100 MHz 附近通常比 GPS L1（1575 MHz）功率更高
- **实测优先**：频谱仪读数为准，公式仅用于事前安全评估

---

## 二、本次测试增益档位计划

本阶段仅 **TX → 频谱仪**，不接 RX，无损坏风险，可放心测试各档位。

| 档位 | tx_gain | amplitude | TX 输出估算 | 备注 |
|------|---------|-----------|------------|------|
| L1   | 35 dB   | 1.0       | −45 dBm | 热身，确认链路通 |
| L2   | 50 dB   | 1.0       | −30 dBm | 中间档 |
| L3   | 70 dB   | 1.0       | −10 dBm | 无衰减器推荐最大值 |
| L4   | 70 dB   | 0.5       | −16 dBm | amplitude 减半，验证幅度影响 |
| L5   | 70 dB   | 0.1       | −30 dBm | amplitude 低至 0.1，验证底噪 |

> amplitude 对输出功率影响约：$20\log_{10}(\text{amplitude})$ dB（线性幅度比）
> - amplitude=0.5 → −6 dB
> - amplitude=0.1 → −20 dB

---

## 三、测试记录表（每档填写频谱仪读数）

> 频谱仪设置建议：Center=100 MHz，Span=10 MHz，RBW=10 kHz，迹线模式=MaxHold/Average

| 档位 | tx_gain | amplitude | 频谱仪读数 P_meas (dBm) | 峰值估算 P_peak (dBm) | 备注 |
|------|---------|-----------|------------------------|----------------------|------|
| L1   | 35 dB   | 1.0       | ________ | P_meas + 3 = ________ | |
| L2   | 50 dB   | 1.0       | ________ | P_meas + 3 = ________ | |
| L3   | 70 dB   | 1.0       | ________ | P_meas + 3 = ________ | |
| L4   | 70 dB   | 0.5       | ________ | P_meas + 3 = ________ | |
| L5   | 70 dB   | 0.1       | ________ | P_meas + 3 = ________ | |

---

## 四、安全判定（填完上表后与 Claude 一起分析）

目标：找出满足以下条件的最大 tx_gain + amplitude 组合：

```
P_peak_at_rx = P_meas + 3 dB (PAPR) − L_cable (约 1 dB) ≤ −10 dBm
```

即：`P_meas ≤ −12 dBm` 时，直连 RX 安全（裕量 12 dB）。

| 结论 | 选定 tx_gain | 选定 amplitude | 预估 RX 输入 (dBm) | 是否安全 |
|------|-------------|---------------|-------------------|---------|
| **推荐参数** | ________ dB | ________ | ________ | ________ |

---

## 五、命令速查

### 5.1 硬件检测

```bash
# 检测系统是否识别到 USRP
uhd_find_devices

# 查看 B210 详细信息（固件版本、序列号等）
uhd_usrp_probe

# 若有两台 B210，按序列号区分
uhd_find_devices --args="type=b200"
```

### 5.2 关于 GNU Radio 流图预览与软件频谱

加 `--qt-preview` 参数可同时弹出 GNU Radio QT 预览窗口，窗口内包含：

- **上半部分**：时域 IQ 波形（`TX Baseband Time Preview`）
- **下半部分**：基带频谱（`TX Baseband Spectrum Preview`，FFT 2048 点，Blackman-Harris 窗）

> 注意：`--qt-preview` 显示的是**基带**信号（发射前的数字域），频率轴以 0 Hz 为中心，带宽 ±2.046 MHz。
> 这与频谱仪看到的射频频谱（以 100 MHz 为中心）不同，两者互为补充。
>
> 需要桌面显示环境（`DISPLAY` 或 `WAYLAND_DISPLAY`），SSH 无显示器时加 `--qt-preview` 会报错退出。

### 5.3 TX → 频谱仪（各档位发射命令）

```bash
# 切换到项目根目录
cd /home/shen/projects/gnss_tx

# 档位 L1：tx_gain=35，amplitude=1.0（热身）—— 不开 QT 预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 35 \
    --amplitude 1.0 \
    --duration 30

# 档位 L1：同上，开启 GNU Radio 基带流图 + 软件频谱
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 35 \
    --amplitude 1.0 \
    --duration 30 \
    --qt-preview

# 档位 L2：tx_gain=50，amplitude=1.0
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 50 \
    --amplitude 1.0 \
    --duration 30

# 档位 L2：开启 QT 预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 50 \
    --amplitude 1.0 \
    --duration 30 \
    --qt-preview

# 档位 L3：tx_gain=70，amplitude=1.0（无衰减器最大推荐值）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 1.0 \
    --duration 30

# 档位 L3：开启 QT 预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 1.0 \
    --duration 30 \
    --qt-preview

# 档位 L4：tx_gain=70，amplitude=0.5
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 0.5 \
    --duration 30

# 档位 L5：tx_gain=70，amplitude=0.1
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 0.1 \
    --duration 30
```

> **注意**：`--tx-gain` 和 `--amplitude` 是否支持命令行覆盖，取决于 `run_tx.py` 是否实现了对应参数。
> 如不支持，直接编辑 `configs/tx_b210_cable_loopback.yaml` 中的 `tx_gain` 和 `amplitude` 字段。

### 5.3 干运行（不开 RF，仅验证流图是否报错）

```bash
cd /home/shen/projects/gnss_tx
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --dry-run
```

### 5.4 查看当前配置文件

```bash
cat /home/shen/projects/gnss_tx/configs/tx_b210_cable_loopback.yaml
```

### 5.5 临时修改配置后发射（不想写命令行参数时）

```bash
# 先备份原配置
cp configs/tx_b210_cable_loopback.yaml configs/tx_b210_cable_loopback.yaml.bak

# 用编辑器修改 tx_gain 和 amplitude，然后发射
# 例如改完之后：
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --duration 30
```

---

## 六、观测重点（发射时看终端输出）

| 现象 | 含义 | 处理 |
|------|------|------|
| 无任何 `U` 打印 | 正常，无 underflow | 继续 |
| 偶发 `U`（1~2 次） | 轻微 USB 抖动，可接受 | 继续观察 |
| 持续 `U U U U...` | USB 带宽不足或 CPU 过载 | 降低 sample_rate 或关闭后台应用 |
| 程序报错退出 | 配置错误或设备问题 | 看报错信息，先跑 `uhd_find_devices` |

---

## 七、下一步（本阶段完成后）

1. 将上方记录表填完，截图/拍照保存频谱仪截图
2. 与 Claude 共同分析，确认推荐参数
3. 改接线路：`B210 TX → [线缆] → B210 RX`
4. 跳转执行 `../ber_loopback_tx/2026-03-27_ber_loopback_tx_plan.md` Step 2（正式 BER 发射）
