# configs/ — 实验配置文件

本目录存放所有发射端 YAML 配置文件。配置文件通过 `--config` 参数传给 `scripts/run_tx.py`，
CLI 参数可覆盖配置文件中的任意字段。

---

## 配置文件一览

| 文件 | 发射模式 | 说明 |
|------|----------|------|
| `tx_b210.yaml` | 单星 PRN1 | 保守安全基线，`tx_gain=0`，最低功率，首次连线用 |
| `tx_b210_visible_spectrum.yaml` | 单星 PRN1 | 已验证可在频谱仪观察到宽带包络的配置 |
| `tx_b210_sn8003272.yaml` | 单星 PRN1 | 固定设备序列号，双 USRP OTA 空收用 |
| `tx_b210_all32prn.yaml` | 32星叠加 | 同时叠加发射 GPS L1 C/A PRN 1~32 |

---

## 关键字段说明

| 字段 | 说明 | 示例值 |
|------|------|--------|
| `prn_id` | 单星模式目标 PRN（1~32）；`all_prns: true` 时忽略 | `1` |
| `all_prns` | `true` = 多星叠加模式，忽略 `prn_id`，发射 PRN 1~32 全部叠加 | `false` |
| `signal_mode` | `spread`（扩频）或 `tone`（单音校准） | `"spread"` |
| `usrp_addr` | UHD 设备地址，`type=b200` 自动发现，或 `serial=8003272` 固定设备 | `"type=b200"` |
| `center_freq` | 射频中心频率（Hz） | `100000000.0` |
| `samples_per_chip` | 每 chip 的采样点数，采样率 = 1.023 MHz × 此值 | `4` |
| `sample_rate` | 基带采样率（Hz），通常由 `samples_per_chip` 派生 | `4092000.0` |
| `tx_gain` | USRP TX 增益（dB）。**首次使用从 0 开始** | `0.0` |
| `amplitude` | 发射幅度缩放（0~1），在 `multiply_const` 块中应用 | `1.0` |
| `nav_pattern` | 循环导航 bit 序列（空格分隔，0 等价于 −1） | `"1 0 1 1 0 0 1 0"` |
| `duration_s` | 发射时长（秒）；`null` 或不填则持续发射 | `null` |

---

## 多星模式（all_prns）注意事项

`tx_b210_all32prn.yaml` 中 `all_prns: true`，信号生成过程如下：

1. 分别生成 PRN 1~32 各自的基带信号（`amplitude=1.0`）
2. 线性叠加后除以 √32 进行功率归一化（每颗星的等效功率不变）
3. 叠加后的峰值幅度理论最大值为 √32 ≈ 5.66（所有码片同相时）

因此配置中 `amplitude=0.25`：实际输出峰值 ≈ 5.66 × 0.25 ≈ 1.4，确保不超出 DAC 满量程。
若需进一步降低峰值，可通过 CLI 覆盖：

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml \
    --amplitude 0.15
```

---

## 使用方式

```bash
cd ~/projects/gnss_tx

# 干运行（验证配置，不启动硬件）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210.yaml --dry-run

# 发射 30 秒
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30

# 多星叠加发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml \
    --duration 60
```

更多示例见 [scripts/README.md](../scripts/README.md)。
