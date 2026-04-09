# gnss_tx 介绍指南

> **文档用途**：向他人介绍发射端工程时的讲解导引，配合 Draw.io 图表按顺序展示。
> 完整的系统介绍（含接收端和实验工作流）见 [`GNSS_RX/docs/introduction_guide.md`](../../GNSS_RX/docs/introduction_guide.md)。

---

## 一句话描述

> gnss_tx 是一套 **GPS L1 C/A 信号软件发射机**：从零生成真实格式的 GPS 信号，经 GNU Radio 驱动 USRP B210 发射，支持单星、多星（最多32颗）和单音校准三种模式，全参数可配置。

---

## 第一步：建立全局认知（5 分钟）

**图表**：[`system_architecture.drawio`](system_architecture.drawio)

用四条泳道快速建立全局框架，向听众说明整个收发系统的边界：

| 泳道 | 颜色 | 内容 |
|------|------|------|
| TX 链路（gnss_tx）| 绿色 | Python 信号生成 → GNU Radio → USRP 发射 |
| RF 信道 | 橙色 | 有线回环（实验室）或 OTA（真实环境）|
| RX 链路（GNSS_RX）| 蓝色 | USRP 接收 → 量化 → 落盘 |
| MATLAB 离线分析 | 紫色 | PRN 捕获 → DLL/PLL 跟踪 → BER 评估 |

**口述要点**：
- **GPS L1 C/A 标准**：1.023 MHz 芯片率，50 bps 导航数据，BPSK 调制
- **中心频率**：实验室用 100 MHz（规避 1575.42 MHz 真实 GPS 频段，合规且安全）
- **采样率**：4.092 MHz（= 1.023 MHz × 4，最低满足奈奎斯特的 4 倍过采样）
- **硬件**：USRP B210，USB 3.0，TX/RX 端口发射，RX2 端口接收

---

## 第二步：深入信号生成原理（10 分钟）

**图表**：[`gnss_tx_signal_chain.drawio`](gnss_tx_signal_chain.drawio)

从配置文件到 RF 输出的完整信号生成链，分四个层次讲解：

### ① 配置层（黄色）

- YAML 文件驱动，任何参数可通过 CLI 覆盖，无需改代码
- `TxRuntimeConfig`（frozen dataclass）统一校验参数合法性
- `--dry-run` 模式：无硬件也能完整验证配置

**6 种预置配置文件**：

| 配置文件 | 场景 |
|----------|------|
| `tx_b210.yaml` | 单星 PRN1，保守基线 |
| `tx_b210_visible_spectrum.yaml` | 频谱仪可见谱验证 |
| `tx_b210_sn8003272.yaml` | 固定设备序列号（OTA 测试）|
| `tx_b210_all32prn.yaml` | 32 星全并发合成 |
| `tx_b210_prn_subset.yaml` | 自定义 PRN 子集 |
| `tx_b210_cable_loopback.yaml` | 有线回环 BER 基线 |

### ② 信号生成层（绿色）

**C/A 码生成**（`ca/prn_generator.py`）：
- 双 LFSR 结构，PRN 1–32 各自对应不同抽头位置
- 输出：1023 chips/ms，`int8(±1)`

**导航比特**（`nav/nav_bits.py`）：
- `CyclicNavBitSource`：循环重播预设导航比特序列
- 速率：50 bps，每比特持续 20 ms（= 20 个 C/A 周期）

**BPSK 扩频**（`signal/spreader.py`）：

$$s[k] = \text{nav\_bit}[k] \times \text{ca\_code}[k]$$

`GpsL1CaBpskGenerator` 维护三层有状态时间基准：码相位 / 导航历元 / 样本相位，支持任意起始状态的连续生成。

**多星叠加**（`signal/multi_sat_combiner.py`）：
- 最多 32 颗卫星信号线性叠加
- √N 功率归一化：利用 C/A 码伪正交性，合理控制峰均比

数据格式转换：`int8(±1) → complex64`（I=chip 值，Q=0）

### ③ GNU Radio 层（蓝色）

```
vector_source_c（回放 complex64 缓冲，循环）
    ↓
multiply_const_cc（幅度缩放 × amplitude）
    ↓
[可选] qtgui 时域 / 频域旁路观测
    ↓
uhd.usrp_sink
```

顶层类 `GpsL1CaTxTopBlock`（`gr/top_block.py`）装配上述流图，`run()` 后阻塞至结束。

### ④ 硬件层（红色）

USRP B210 内部：`fc32 → sc16`（节省 USB 3.0 带宽 50%）→ DAC → 上变频 → 天线

---

## 发射端技术亮点

### 完全可控的信号源
- 发端 PRN、导航数据、功率全部已知 → 与接收端做精确 BER 对比
- `--export-truth-json` 导出真值文件，供 MATLAB 验证使用

### 多星仿真一机完成
- 单台 USRP B210 可同时模拟最多 32 颗卫星信号
- 信号超位置互相关峰不超过 1/N 量级，信号质量可保证

### 软硬件完全解耦
- `--dry-run` 无硬件验证配置
- 发射缓冲（`replay_samples`）可以独立导出验证，无需运行硬件

---

## 常用命令

```bash
cd ~/projects/gnss_tx
source .venv/bin/activate

# 环境自检
PYTHONPATH=src python3 scripts/quick_check.py

# 验证配置（无硬件）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run --config configs/tx_b210.yaml

# 单星发射 30 秒
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30

# 32 星合成发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml \
    --duration 60
```

---

## 常见问题

**Q：为什么不直接用真实 GPS 频率 1575.42 MHz？**
A：发射真实 GPS 频率未经授权属于违规，且会干扰周围所有 GPS 接收机。实验室用 100 MHz 中心频率通过有线连接，合规、安全，且能验证全部核心信号处理算法。

**Q：32 星叠加为什么要 √N 归一化？**
A：叠加后功率是单星的 N 倍，不归一化会导致 USRP DAC 幅度溢出截幅。除以 √N 后总功率保持为单星功率，PAPR（峰均比）在 C/A 码伪正交性保证下仍处于合理范围。

**Q：int8 为什么能表示 C/A 码？**
A：GPS L1 C/A 码是二进制序列，每个 chip 只有 +1 或 −1 两个值，int8 完全够用且内存最紧凑。扩频后需要复数表示才扩展到 complex64。

---

## 深入阅读

| 文档 | 内容 |
|------|------|
| [`gnss_tx_architecture_analysis.md`](gnss_tx_architecture_analysis.md) | 模块完整设计分析 |
| [`spectrum_analyzer_observation.md`](spectrum_analyzer_observation.md) | 频谱仪验证配置指南 |
| [`design/actual_sample_rate_detection.md`](design/actual_sample_rate_detection.md) | 硬件实际采样率检测机制 |
