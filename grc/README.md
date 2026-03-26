# grc/ — GNU Radio Companion 自定义块与流图

本目录存放供 GNU Radio Companion（GRC）识别的**自定义块定义文件**（`.block.yml`），
以及对应的流图工程文件（`flowgraphs/`）说明。

---

## 目录结构

```
grc/
└── blocks/
    ├── gnss_tx_gps_l1_ca_source.block.yml   # 单星扩频基带源块（支持 PRN 1~32）
    └── gnss_tx_usrp_sink.block.yml          # UHD USRP 发射 sink 块（含采样率回读）

flowgraphs/
├── gnss_tx_main.grc       # 主流图：单星模式，支持 PRN 1~32 选择、QT 预览
├── single_tone_test.grc   # 单音测试流图
└── two_tone_test.grc      # 双音测试流图
```

---

## 如何启动（必须用脚本）

**直接双击 `.grc` 文件会导致自定义块显示为"未知块"**，因为 GRC 找不到 `grc/blocks/` 路径。

必须使用项目提供的启动脚本，它会在启动前设置 `GRC_BLOCKS_PATH` 环境变量：

```bash
cd ~/projects/gnss_tx

# 在 GRC 图形界面中打开主流图
bash scripts/run_gnss_tx_grc.sh

# 直接运行主流图（跳过 GRC 图形界面）
bash scripts/run_gnss_tx_grc.sh --run

# 无显示环境（SSH 无头模式）
bash scripts/run_gnss_tx_grc.sh --run --headless
```

脚本设置的环境变量：

```bash
export GRC_BLOCKS_PATH="/usr/share/gnuradio/grc/blocks:<项目根>/grc/blocks"
```

---

## 块说明

### `gnss_tx_gps_l1_ca_source`

| 属性 | 值 |
|------|----|
| GRC 显示名 | GNSS TX PRN Source |
| GRC 分类 | [GNSS TX] |
| 输出 | 1 路 complex64 基带流 |

**作用**：调用 `gnss_tx.gr.make_gps_l1_ca_vector_source()`，预生成一个完整导航 bit
周期的 GPS L1 C/A 扩频基带缓冲区，通过 `blocks.vector_source_c` 循环回放，
避免逐 sample 实时计算引起的 USRP underflow。

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| PRN ID | 卫星编号（1~32） | 1 |
| Samples / Chip | 每个 chip 的采样点数，采样率 = 1.023 MHz × 此值 | 4 |
| Internal Amplitude | 内部信号幅度（对外幅度由 `amplitude_scale` 块控制） | 1.0 |
| Nav Pattern | 循环导航 bit 序列（空格分隔，0 等价于 −1） | "1 0 1 1 0 0 1 0" |
| Initial Code Phase | PRN 周期内起始 chip 偏移 | 0 |
| Initial Nav Epoch | 导航 bit 内起始 1 ms epoch 偏移 | 0 |
| Initial Nav Bit Index | nav_pattern 起始 bit 索引 | 0 |

> **多星模式**：GRC 流图（`gnss_tx_main.grc`）仅支持单星模式（一次选一颗 PRN）。
> 如需发射全部 32 颗 PRN 的叠加信号，请使用 Python 运行时：
> ```bash
> PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_all32prn.yaml
> ```

---

### `gnss_tx_usrp_sink`

| 属性 | 值 |
|------|----|
| GRC 显示名 | GNSS TX UHD Sink |
| GRC 分类 | [GNSS TX] |
| 输入 | 1 路 complex 基带流 |

**作用**：封装 `uhd.usrp_sink`，配置采样率、中心频率、增益、天线和带宽。
初始化完成后**自动调用 `sink.get_samp_rate()` 读回硬件确认的实际采样率**，并打印到 GRC Console。

**参数**：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| Device Address | UHD 设备地址（`"type=b200"` 或 `"serial=8003272"`） | "type=b200" |
| Samp rate (Sps) | 请求采样率（通常填 GRC 变量 `samp_rate`） | samp_rate |
| Center Freq (Hz) | 射频中心频率 | 0 |
| Gain (dB) | TX 增益 | 0 |
| Antenna | 天线端口（B210 发射用 "TX/RX"） | "TX/RX" |
| Bandwidth (Hz) | 模拟前端带宽（通常与 samp_rate 相同） | 0 |

**实际采样率回读**（GRC Console 面板输出示例）：

```
[INFO] GNU Radio USRP sink requested sample rate : 4092000.000 Sps (4.092000 Msps)
[INFO] GNU Radio USRP sink actual sample rate    : 4092000.000 Sps (4.092000 Msps)
[INFO] GNU Radio USRP sink sample-rate delta     : +0.000 Sps (+0.000000%)
```

> USRP B210 通过整数分频链派生采样率，`get_samp_rate()` 返回硬件实际执行值。
> 若 `sample-rate delta` 不为零，说明硬件做了舍入，实际 samples/chip 偏离理论值。

---

## 在新流图中使用这些块

1. 用 `bash scripts/run_gnss_tx_grc.sh` 打开 GRC
2. 在 GRC 块搜索栏输入 `GNSS TX`，即可看到两个自定义块
3. 将 `GNSS TX PRN Source` → `amplitude_scale (multiply_const)` → `GNSS TX UHD Sink` 连接
4. 配置变量 `samp_rate = 1.023e6 * samples_per_chip`（推荐用 GRC variable 块）
5. 运行后在 **GRC Console 面板**（底部）确认实际采样率

---

## 与 Python 运行时的关系

这两个块与 `scripts/run_tx.py` 使用**完全相同的底层函数**：

| GRC 块 | Python 运行时等价 |
|--------|-----------------|
| `make_gps_l1_ca_vector_source(...)` | `build_replay_samples()` + `blocks.vector_source_c(...)` |
| `uhd.usrp_sink(...)` + 采样率回读 | `create_b210_sink(config)` + `format_uhd_tx_sample_rate_report(...)` |

GRC 流图是 Python 运行时发射链的**可视化镜像**，两者信号处理结果一致。
Python 运行时额外支持多星叠加模式（`all_prns: true`），GRC 流图暂不支持。
