# gnss_tx

基于 Ubuntu + Python + GNU Radio + USRP B210 的 GPS L1 C/A 扩频发射实验平台。

支持两种发射模式：
- **单星模式**：可选 PRN1~32 任意一颗卫星的 GPS L1 C/A 扩频发射
- **多星模式**：同时叠加发射全部 32 颗（或指定子集）PRN 的合并信号，√N 功率归一化

配套接收端项目：[GNSS_RX](../GNSS_RX/README.md)（IQ 采集 + MATLAB 离线捕获分析）

---

## 功能概述

| 功能 | 说明 |
|------|------|
| GPS L1 C/A 码生成 | 软件实现双 LFSR，生成标准 GPS L1 C/A PRN1~32 码（1023 chip/ms） |
| 扩频基带生成 | 导航 bit × C/A 码 = 扩频 chip，展开为 complex64 BPSK 基带 sample |
| 多星叠加合成 | 32 颗（或指定子集）PRN 线性叠加，√N 功率归一化，预生成回放缓冲区 |
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
│   ├── ca/               # C/A 码生成（PRN1~32 LFSR 实现）
│   ├── nav/              # 导航 bit 归一化与循环访问（50 bps）
│   ├── signal/           # BPSK 扩频状态机 + 单音 IQ 生成 + 多星叠加合成
│   ├── gr/               # GNU Radio top block + QT 预览 + replay source
│   ├── usrp/             # B210 sink 创建 + 运行时配置 + 实验报告
│   └── utils/            # YAML 加载（timebase/logging 为占位模块）
├── scripts/              # 可执行脚本（详见 scripts/README.md）
├── configs/              # 实验配置文件（详见 configs/README.md）
├── flowgraphs/           # GNU Radio Companion 工程文件（详见 grc/README.md）
├── grc/                  # GRC 自定义块定义（详见 grc/README.md）
├── experiments/          # 实验记录、清单、操作流程（详见 experiments/README.md）
├── results/              # 脚本输出（图像/NPY/CSV/日志）
├── docs/                 # 详细设计文档与架构分析
└── env/                  # 环境安装脚本与依赖说明
```

---

## 子目录文档索引

| 目录 | README | 说明 |
|------|--------|------|
| `scripts/` | [scripts/README.md](scripts/README.md) | 所有脚本运行命令（发射、分析、实验规划、GRC 启动） |
| `configs/` | [configs/README.md](configs/README.md) | 配置文件说明、关键字段、PAPR 注意事项 |
| `grc/` | [grc/README.md](grc/README.md) | GRC 流图与自定义块说明、GRC 启动命令 |
| `experiments/` | [experiments/README.md](experiments/README.md) | 实验记录格式与复现入口 |
| `docs/` | [docs/gnss_tx_architecture_analysis.md](docs/gnss_tx_architecture_analysis.md) | 完整架构分析、模块实现参考；各子模块含 `architecture.drawio` 架构图 |

---

## 架构图索引

项目各模块的架构图均以 [draw.io](https://app.diagrams.net/) 格式保存，可用 draw.io 桌面版或 VS Code draw.io 插件直接打开：

| 文件 | 说明 |
|------|------|
| [docs/system_architecture.drawio](docs/system_architecture.drawio) | 系统整体架构：基带生成 → GNU Radio → USRP 端到端流程 |
| [docs/gnss_tx_signal_chain.drawio](docs/gnss_tx_signal_chain.drawio) | GPS L1 C/A 信号链详细数据流 |
| [src/gnss_tx/ca/architecture.drawio](src/gnss_tx/ca/architecture.drawio) | C/A 码生成模块（双 LFSR 实现） |
| [src/gnss_tx/nav/architecture.drawio](src/gnss_tx/nav/architecture.drawio) | 导航 bit 归一化与循环访问模块 |
| [src/gnss_tx/signal/architecture.drawio](src/gnss_tx/signal/architecture.drawio) | BPSK 扩频状态机 + 单音生成 + 多星叠加合成 |
| [src/gnss_tx/gr/architecture.drawio](src/gnss_tx/gr/architecture.drawio) | GNU Radio top block 与回放流图结构 |
| [src/gnss_tx/usrp/architecture.drawio](src/gnss_tx/usrp/architecture.drawio) | B210 sink 创建与运行时配置 |
| [src/gnss_tx/utils/architecture.drawio](src/gnss_tx/utils/architecture.drawio) | 工具模块（YAML 加载、timebase、logging） |

---

## 环境安装

### 系统依赖（GNU Radio + UHD）

```bash
sudo apt update
sudo apt install -y gnuradio python3-gnuradio uhd-host python3-pip python3-venv
sudo uhd_images_downloader   # 首次使用或固件更新后必须执行
```

### Python 虚拟环境

```bash
cd ~/projects/gnss_tx
bash env/ubuntu/setup.sh     # 推荐：使用安装脚本
# 或手动：python3 -m venv .venv && source .venv/bin/activate && pip install -e .
```

激活虚拟环境（每次新终端）：

```bash
source ~/projects/gnss_tx/.venv/bin/activate
```

### 验证安装

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 scripts/quick_check.py
uhd_find_devices
```

---

## 快速开始

> 所有命令须在 `~/projects/gnss_tx` 目录下执行。详细参数和更多示例见 [scripts/README.md](scripts/README.md)。

```bash
# 干运行（不启动硬件，仅打印配置）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run

# 单星发射（已验证可见谱配置）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml --duration 30

# 32颗PRN叠加多星发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml --duration 60

# 指定子集多星发射（用于接收端验证）
PYTHONPATH=src python3 scripts/run_tx.py \
    --prn-ids 1,5,10,15 --duration 60

# 通过 GNU Radio Companion 发射（单星模式）
bash scripts/run_gnss_tx_grc.sh
```

---

## 单元测试

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## 当前版本限制

- 导航层为循环 bit pattern，**非真实 GPS NAV 子帧**
- 无 Doppler 控制、无时基管理
- 部分模块为占位空文件：`subframe_builder.py`、`timebase.py`、`logging.py`
- GRC 流图（`flowgraphs/gnss_tx_main.grc`）仅支持单星模式；多星叠加需通过 Python 运行时（`scripts/run_tx.py`）
