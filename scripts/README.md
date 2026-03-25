# scripts/ — 可执行脚本

本目录包含项目所有可执行脚本。所有命令均须在项目根目录下执行。

---

## 脚本一览

| 脚本 | 说明 |
|------|------|
| `run_tx.py` | **主发射入口**，加载配置并驱动 GNU Radio + B210 发射链 |
| `analyze_prn1_spread.py` | 离线扩频链可视化分析（C/A 码图、样本图、相关峰） |
| `plan_tx_visibility_sweep.py` | 生成参数扫描实验文档（CSV + Markdown 清单 + 草稿） |
| `generate_test_iq.py` | 生成单音测试 IQ 数据文件（不需要硬件） |
| `export_iq.py` | 导出扩频基带 IQ 数据为文件 |
| `generate_nav.py` | 生成导航 bit 序列辅助文件 |
| `quick_check.py` | 检查项目目录结构与 Python 环境是否正常 |
| `run_gnss_tx_grc.sh` | 启动 GNU Radio Companion（必须通过此脚本，否则自定义块不可用） |

---

## 运行方法

> 所有 Python 脚本须设置 `PYTHONPATH=src`，或在激活虚拟环境后运行。

### run_tx.py — 主发射

```bash
cd ~/projects/gnss_tx

# 干运行（不启动发射，仅打印配置摘要）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run

# 保守基线发射（tx_gain=0，最低功率）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210.yaml \
    --duration 20

# 可见谱配置发射（已验证可在频谱仪观察宽带包络）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30

# 持续发射（Ctrl-C 停止）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml

# 单音校准模式
PYTHONPATH=src python3 scripts/run_tx.py \
    --signal-mode tone \
    --center-freq 100e6 \
    --tone-offset-hz 500000 \
    --tx-gain 10 \
    --duration 20

# 启用 QT 软件侧预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --qt-preview \
    --duration 60
```

**全部 CLI 参数**（均可覆盖配置文件对应字段）：

| 参数 | 类型 | 说明 |
|------|------|------|
| `--config` | 路径 | YAML 配置文件（默认 `configs/tx_b210.yaml`） |
| `--prn-id` | int | 目标 PRN 编号（当前支持 1~32） |
| `--center-freq` | float | 射频中心频率（Hz） |
| `--tx-gain` | float | TX 增益（dB） |
| `--sample-rate` | float | 基带采样率（Hz） |
| `--samples-per-chip` | int | 每 chip 样本数（采样率 = 1.023 MHz × 此值） |
| `--signal-mode` | spread/tone | 信号模式 |
| `--nav-pattern` | str | 导航 bit 序列（空格分隔，0 等价于 −1） |
| `--tone-offset-hz` | float | 单音频偏（Hz，仅 tone 模式有效） |
| `--amplitude` | float | 信号幅度 |
| `--duration` | float | 发射时长（秒），不填则持续发射 |
| `--qt-preview` | flag | 启用 GNU Radio QT 时/频域预览 |
| `--dry-run` | flag | 仅打印配置，不启动发射 |

---

### analyze_prn1_spread.py — 扩频链离线分析

```bash
cd ~/projects/gnss_tx

# 默认参数（40 ms，4 倍过采样，PRN1）
PYTHONPATH=src python3 scripts/analyze_prn1_spread.py

# 自定义 PRN 与输出前缀
PYTHONPATH=src python3 scripts/analyze_prn1_spread.py \
    --prn-id 7 \
    --num-ms 80 \
    --samples-per-chip 4 \
    --amplitude 1.0 \
    --prefix prn7_spread
```

输出到 `results/`：
- `figs/prn{n}_spread_ca_code.png` — 目标 PRN 的 C/A 码波形（前 128 chip）
- `figs/prn{n}_spread_samples.png` — 扩频基带样本（前 16 chip）
- `figs/prn{n}_spread_correlation.png` — 1 ms 自相关峰
- `npy/prn{n}_spread_*.npy` — numpy 数组
- `logs/prn{n}_spread_analysis.txt` — 文本报告

---

### plan_tx_visibility_sweep.py — 参数扫描规划

```bash
cd ~/projects/gnss_tx

# 使用默认可见谱配置
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py

# 指定输出路径
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --csv-output results/csv/my_sweep.csv \
    --checklist-output experiments/my_checklist.md
```

---

### generate_test_iq.py — 生成测试单音 IQ

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 scripts/generate_test_iq.py
# 输出：results/npy/test_iq_tone.npy（1 MHz 采样，50 kHz 单音，10 ms）
```

---

### quick_check.py — 环境快速检查

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 scripts/quick_check.py
```

检查项：Python 版本、项目路径、numpy、gnss_tx 包导入是否正常。不需要硬件。

---

### run_gnss_tx_grc.sh — GNU Radio Companion 启动

```bash
cd ~/projects/gnss_tx

# 打开 GRC 图形界面（默认）
bash scripts/run_gnss_tx_grc.sh

# 直接运行流图（跳过 GRC 界面）
bash scripts/run_gnss_tx_grc.sh --run

# 无显示环境（如 SSH）
bash scripts/run_gnss_tx_grc.sh --run --headless
```

> **必须通过此脚本启动**，它会设置 `GRC_BLOCKS_PATH` 使 GRC 能找到 `grc/blocks/` 中的自定义块。直接双击 `.grc` 文件会导致自定义块显示为"未知块"。
