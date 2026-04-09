# gnss_tx

**GPS L1 C/A 信号软件发射机**：从零生成真实格式的 GPS 信号，经 GNU Radio 驱动 USRP B210 发射。支持单星（PRN1~32）、多星（最多 32 颗叠加）和单音校准三种模式，全参数 YAML 可配置。

配套接收端：[GNSS_RX](../GNSS_RX/README.md)（IQ 采集 + MATLAB 离线捕获/跟踪/BER 分析）

---

## 快速开始

所有命令须在 `~/projects/gnss_tx` 目录下执行。

```bash
# 激活虚拟环境（每次新终端）
source ~/projects/gnss_tx/.venv/bin/activate

# 干运行（无需硬件，验证配置）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run

# 单星发射（已验证可见谱配置）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml --duration 30

# 32颗PRN叠加多星发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml --duration 60

# 指定子集多星发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --prn-ids 1,5,10,15 --duration 60

# 通过 GNU Radio Companion 发射（单星模式）
bash scripts/run_gnss_tx_grc.sh
```

---

## 目录结构与文档索引

| 目录 | 用途 | 文档 |
| --- | --- | --- |
| `src/gnss_tx/` | 核心 Python 包（C/A 码、扩频、GNU Radio、USRP） | [src/gnss_tx/README.md](src/gnss_tx/README.md) |
| `scripts/` | 可执行脚本（发射、分析、实验规划、GRC 启动） | [scripts/README.md](scripts/README.md) |
| `configs/` | 实验配置文件（6 种预置场景） | [configs/README.md](configs/README.md) |
| `flowgraphs/` | GNU Radio Companion 工程文件 | [grc/README.md](grc/README.md) |
| `grc/` | GRC 自定义块定义 | [grc/README.md](grc/README.md) |
| `experiments/` | 实验记录、清单、操作流程 | [experiments/README.md](experiments/README.md) |
| `docs/` | 设计文档与架构分析（含 draw.io 图） | [docs/README.md](docs/README.md) |
| `results/` | 脚本输出（图像/NPY/CSV/日志） | — |
| `env/` | 环境安装脚本与依赖说明 | — |

---

## 功能概述

| 功能 | 说明 |
| --- | --- |
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
bash env/ubuntu/setup.sh     # 推荐：使用安装脚本（会创建能看到 GNU Radio/UHD 的 .venv）
# 或手动：python3 -m venv --system-site-packages .venv && source .venv/bin/activate && pip install -r env/ubuntu/requirements.txt && pip install -e .
```

### 验证安装

```bash
cd ~/projects/gnss_tx
python3 -c "from gnuradio import uhd; print(uhd.__file__)"
PYTHONPATH=src python3 scripts/quick_check.py
uhd_find_devices
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
