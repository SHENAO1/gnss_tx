# gnss_tx

基于 Ubuntu + Python + GNU Radio + USRP B210 的 GPS L1 C/A 扩频发射实验平台。

当前实现：以 **PRN1** 为核心，通过预生成复基带缓冲区循环回放的方式，驱动 USRP B210 发射 GPS L1 C/A 扩频信号，并通过频谱仪观察宽带包络验证链路正确性。支持单音校准模式、QT 软件侧频谱预览、参数扫描实验规划和双 USRP 空收验证场景。

---

## 功能概述

| 功能 | 说明 |
|------|------|
| GPS L1 C/A 码生成 | 软件实现双 LFSR，生成标准 PRN1 C/A 码（1023 chip/ms） |
| 扩频基带生成 | 导航 bit × C/A 码 = 扩频 chip，展开为 complex64 BPSK 基带 sample |
| 单音校准模式 | 生成复指数单音用于硬件链路（同轴 + 频谱仪）校准 |
| GNU Radio 发射链 | `vector_source_c` 缓冲回放 + `multiply_const_cc` + `uhd.usrp_sink` |
| QT 预览 | 实时时域/频域软件侧频谱预览（需 GNU Radio Qt GUI） |
| 配置系统 | YAML 配置 + CLI 命令行覆盖 + 参数合法性校验 |
| 实验规划 | 自动生成参数扫描 CSV、Markdown 清单、实验草稿 |
| 离线分析 | 扩频链可视化分析（C/A 码图、样本图、1 ms 相关峰） |
| 双 USRP 空收 | 固定序列号配置文件，支持 TX/RX 双机 OTA 验证 |

---

## 目录结构

```
gnss_tx/
├── src/gnss_tx/          # 核心 Python 包
│   ├── ca/               # C/A 码生成（PRN1 LFSR 实现）
│   ├── nav/              # 导航 bit 归一化与循环访问（50 bps）
│   ├── signal/           # BPSK 扩频状态机 + 单音 IQ 生成 + 调制
│   ├── gr/               # GNU Radio top block + QT 预览 + replay source
│   ├── usrp/             # B210 sink 创建 + 运行时配置 + 实验报告
│   └── utils/            # YAML 加载（timebase/logging 为占位模块）
├── scripts/              # 可执行脚本
│   ├── run_tx.py         # 主发射入口
│   ├── analyze_prn1_spread.py   # 扩频链离线分析
│   ├── plan_tx_visibility_sweep.py  # 参数扫描实验规划
│   ├── generate_test_iq.py      # 单音测试 IQ 生成
│   ├── quick_check.py    # 环境快速检查
│   └── run_gnss_tx_grc.sh       # GNU Radio Companion 启动脚本
├── configs/              # 实验配置文件
│   ├── tx_b210.yaml                   # 保守安全基线（tx_gain=0）
│   ├── tx_b210_visible_spectrum.yaml  # 已验证可见谱配置
│   └── tx_b210_sn8003272.yaml         # 固定序列号 OTA 双机配置
├── flowgraphs/           # GNU Radio Companion 工程文件
├── experiments/          # 实验记录、清单、操作流程
├── results/              # 脚本输出（图像/NPY/CSV/日志）
├── docs/                 # 详细设计文档与架构分析
└── env/                  # 环境安装脚本与依赖说明
```

---

## Ubuntu 环境安装

### 系统依赖（GNU Radio + UHD）

```bash
sudo apt update
sudo apt install -y gnuradio python3-gnuradio uhd-host python3-pip python3-venv
# 下载 UHD FPGA 固件（首次使用或固件版本更新后必须执行）
sudo uhd_images_downloader
```

### Python 虚拟环境

```bash
cd /path/to/gnss_tx

# 方式一：使用项目提供的安装脚本（推荐）
bash env/ubuntu/setup.sh

# 方式二：手动安装
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r env/ubuntu/requirements.txt
pip install -e .
```

激活虚拟环境（后续每次使用前执行）：

```bash
source .venv/bin/activate
```

### 验证安装

```bash
# 检查项目结构与 Python 环境
PYTHONPATH=src python3 scripts/quick_check.py

# 检查 USRP 设备是否可识别
uhd_find_devices
```

---

## 快速开始

### 1. 干运行（不启动发射，仅打印配置）

```bash
PYTHONPATH=src python3 scripts/run_tx.py --dry-run
```

### 2. 保守基线发射（tx_gain=0，最低功率）

连接 B210 TX/RX 口到频谱仪（加衰减器保护），再运行：

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210.yaml \
    --duration 20
```

### 3. 可见谱配置发射（已验证可在频谱仪观察到宽带包络）

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30
```

### 4. 持续发射（按 Ctrl-C 停止）

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml
```

### 5. 单音校准模式

在扩频包络不易观察时，先用单音确认 B210 → 同轴 → 频谱仪硬件链路正常：

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --signal-mode tone \
    --center-freq 100e6 \
    --tone-offset-hz 500000 \
    --tx-gain 10 \
    --duration 20
```

### 6. 启用 QT 软件侧预览

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --qt-preview \
    --duration 60
```

---

## 发射参数调整示例

所有 CLI 参数会覆盖配置文件中对应的字段：

```bash
# 调整中心频率、增益和幅度
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210.yaml \
    --center-freq 150e6 \
    --tx-gain 15 \
    --amplitude 0.5 \
    --duration 30

# 使用 4 倍过采样（默认）
PYTHONPATH=src python3 scripts/run_tx.py \
    --samples-per-chip 4   # sample_rate 自动派生为 4.092 MHz

# 使用 8 倍过采样
PYTHONPATH=src python3 scripts/run_tx.py \
    --samples-per-chip 8   # sample_rate 自动派生为 8.184 MHz

# 指定导航 bit 循环模式（空格分隔，0 等价于 -1）
PYTHONPATH=src python3 scripts/run_tx.py \
    --nav-pattern "1 0 1 1 0 0 1 0"
```

---

## 双 USRP OTA 空收

TX 端（USRP serial=8003272）发射，RX 端（第二台 USRP）接收，两台天线相距 0.5~2 m：

```bash
# 使用固定序列号配置，中心频率 150 MHz（FM 频段外）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_sn8003272.yaml \
    --duration 60
```

详细操作步骤见 [experiments/2026-03-24_dual_usrp_loopback_procedure.md](experiments/2026-03-24_dual_usrp_loopback_procedure.md)。

---

## 离线信号分析

### 扩频链可视化分析

```bash
# 默认参数（40 ms，4 倍过采样）
PYTHONPATH=src python3 scripts/analyze_prn1_spread.py

# 自定义
PYTHONPATH=src python3 scripts/analyze_prn1_spread.py \
    --num-ms 80 \
    --samples-per-chip 4 \
    --amplitude 1.0 \
    --prefix prn1_spread
```

输出到 `results/`：
- `figs/prn1_spread_ca_code.png` — PRN1 C/A 码波形（前 128 chip）
- `figs/prn1_spread_samples.png` — 扩频基带样本（前 16 chip 展开）
- `figs/prn1_spread_correlation.png` — 1 ms 自相关峰
- `npy/prn1_spread_*.npy` — numpy 数组
- `logs/prn1_spread_analysis.txt` — 文本报告（含相关峰统计）

### 生成测试单音 IQ

```bash
PYTHONPATH=src python3 scripts/generate_test_iq.py
# 输出：results/npy/test_iq_tone.npy（1 MHz 采样，50 kHz 单音，10 ms）
```

---

## 参数扫描实验规划

生成完整实验文档（CSV 参数模板 + Markdown 清单 + 草稿）：

```bash
# 使用默认可见谱配置
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py

# 指定配置文件
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --csv-output results/csv/my_sweep.csv \
    --checklist-output experiments/my_checklist.md
```

扫描策略：
1. **基准确认**：`tx_gain=10, amplitude=0.50`，确认当天硬件可重复
2. **阶段1**：固定 `amplitude=0.50`，扫描 `tx_gain = 10 → 8 → 6`
3. **阶段2**：固定最小稳定 `tx_gain`，扫描 `amplitude = 0.50 → 0.40 → 0.30`
4. **阶段3**：最终组合重复 3 次，验证可重复性

---

## GNU Radio Companion

```bash
# 打开主流图（GRC 界面）
bash scripts/run_gnss_tx_grc.sh

# 直接运行（跳过 GRC 界面）
bash scripts/run_gnss_tx_grc.sh --run

# 无显示环境（如 SSH）
bash scripts/run_gnss_tx_grc.sh --run --headless
```

> **注意**：必须通过脚本启动 GRC，否则自定义块（`grc/blocks/`）无法被 GRC 找到。
> 直接双击 `.grc` 文件会导致自定义块显示为未知。

---

## 单元测试

```bash
# 运行全部单元测试
PYTHONPATH=src python3 -m unittest discover -s tests -v

# 运行单个测试模块
PYTHONPATH=src python3 -m unittest tests/test_spreader.py -v
PYTHONPATH=src python3 -m unittest tests/test_ca_prn.py -v
```

---

## 频谱仪观察建议

首次连线 RF 前：

1. 先用 `--dry-run` 确认配置正确
2. 频谱仪输入阻抗设为 **50 ohm**，开启前端保护
3. 设置参考电平和输入衰减后再连接同轴线
4. 从 `tx_b210.yaml`（`tx_gain=0`）开始，确认信号可见后再逐步提高增益

推荐频谱仪设置（100 MHz 中心频率场景）：

| 参数 | 值 |
|------|----|
| Center | 100 MHz |
| Span | 5 MHz |
| RBW | 1 kHz |
| VBW | 1 kHz |
| Att | 10 dB |
| Ref Level | -66 dBm |

预期观察：扩频模式下为宽带噪声形包络（约 4 MHz 带宽），不是单根谱线。停止发射后包络消失。

---

## 文档索引

| 文档 | 说明 |
|------|------|
| [docs/gnss_tx_architecture_analysis.md](docs/gnss_tx_architecture_analysis.md) | 完整架构分析、模块实现参考、配置参数说明、脚本命令参考 |
| [docs/spectrum_analyzer_observation.md](docs/spectrum_analyzer_observation.md) | 频谱仪观察方法、排障顺序与实验建议 |
| [docs/git_workflow.md](docs/git_workflow.md) | 分支策略、提交规范与工作流 |
| [experiments/2026-03-24_dual_usrp_loopback_procedure.md](experiments/2026-03-24_dual_usrp_loopback_procedure.md) | 双 USRP OTA 空收实验操作流程 |
| [experiments/tx_visibility_sweep_checklist.md](experiments/tx_visibility_sweep_checklist.md) | 可见谱参数扫描清单（当前） |

---

## 当前版本限制

- 仅支持 **PRN1**（其他 PRN 的 G2 抽头表待补充）
- 导航层为循环 bit pattern，**非真实 GPS NAV 子帧**
- 无多卫星合成、无 Doppler 控制、无时基管理
- 部分模块为占位空文件：`subframe_builder.py`、`timebase.py`、`logging.py`
