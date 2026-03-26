# scripts/ — 可执行脚本

本目录包含项目所有可执行脚本。所有命令均须在 `~/projects/gnss_tx` 目录下执行。

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
| `run_gnss_tx_grc.sh` | 启动 GNU Radio Companion（详见 grc/README.md） |

> 所有 Python 脚本须设置 `PYTHONPATH=src`，或在激活虚拟环境后运行。

---

## run_tx.py — 主发射入口

### 单星模式（PRN 可选 1~32）

```bash
cd ~/projects/gnss_tx

# 干运行（不启动硬件，仅打印配置）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run

# 切换到指定 PRN（干运行）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run --prn-id 7

# 保守基线发射（tx_gain=0，最低功率）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210.yaml \
    --duration 20

# 已验证可见谱配置
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30

# 持续发射（Ctrl-C 停止）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml

# 指定 PRN7 发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --prn-id 7 \
    --duration 30
```

### 多星模式（32颗PRN叠加）

```bash
cd ~/projects/gnss_tx

# 多星干运行（验证配置）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml \
    --dry-run

# 32颗PRN叠加发射（默认 amplitude=0.25 补偿 PAPR）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml \
    --duration 60

# 持续发射（Ctrl-C 停止）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml

# 覆盖 amplitude（进一步降低 PAPR）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml \
    --amplitude 0.2 \
    --duration 60
```

> **PAPR 说明**：32颗PRN叠加后峰值幅度约为 √32 ≈ 5.66（功率归一化后），
> `amplitude=0.25` 可将峰值压至约 1.4，避免 DAC 削波。

### 单音校准模式

```bash
cd ~/projects/gnss_tx

# 单音校准（确认 B210 → 同轴 → 频谱仪硬件链路正常）
PYTHONPATH=src python3 scripts/run_tx.py \
    --signal-mode tone \
    --center-freq 100e6 \
    --tone-offset-hz 500000 \
    --tx-gain 10 \
    --duration 20
```

### 启用 QT 软件侧预览

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --qt-preview \
    --duration 60
```

### 双 USRP OTA 空收

```bash
# TX 端（USRP serial=8003272），中心频率 150 MHz（FM 频段外）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_sn8003272.yaml \
    --duration 60
```

详细操作步骤见 [experiments/2026-03-24_dual_usrp_loopback_procedure.md](../experiments/2026-03-24_dual_usrp_loopback_procedure.md)。

### CLI 参数完整参考

| 参数 | 类型 | 说明 |
|------|------|------|
| `--config` | 路径 | YAML 配置文件（默认 `configs/tx_b210.yaml`） |
| `--prn-id` | int | 目标 PRN（1~32，单星模式有效） |
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

> 多星模式通过配置文件中的 `all_prns: true` 字段触发，不需要额外 CLI 参数。
> 详见 [configs/README.md](../configs/README.md)。

---

## analyze_prn1_spread.py — 扩频链离线分析

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

| 文件 | 说明 |
|------|------|
| `figs/prn{n}_spread_ca_code.png` | 目标 PRN 的 C/A 码波形（前 128 chip） |
| `figs/prn{n}_spread_samples.png` | 扩频基带样本（前 16 chip 展开） |
| `figs/prn{n}_spread_correlation.png` | 1 ms 自相关峰 |
| `npy/prn{n}_spread_*.npy` | numpy 数组 |
| `logs/prn{n}_spread_analysis.txt` | 文本报告（含相关峰统计） |

---

## plan_tx_visibility_sweep.py — 参数扫描实验规划

```bash
cd ~/projects/gnss_tx

# 使用默认可见谱配置
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py

# 指定配置和输出路径
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --csv-output results/csv/my_sweep.csv \
    --checklist-output experiments/my_checklist.md
```

生成产物：CSV 参数模板 + Markdown 操作清单 + 实验草稿文件。

扫描策略（参考）：
1. **基准确认**：`tx_gain=10, amplitude=0.50`，确认当天硬件可重复
2. **阶段1**：固定 `amplitude=0.50`，扫描 `tx_gain = 10 → 8 → 6`
3. **阶段2**：固定最小稳定 `tx_gain`，扫描 `amplitude = 0.50 → 0.40 → 0.30`
4. **阶段3**：最终组合重复 3 次，验证可重复性

---

## generate_test_iq.py — 生成测试单音 IQ

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 scripts/generate_test_iq.py
# 输出：results/npy/test_iq_tone.npy（1 MHz 采样，50 kHz 单音，10 ms）
```

---

## quick_check.py — 环境快速检查

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 scripts/quick_check.py
```

检查项：Python 版本、项目路径、numpy、gnss_tx 包导入是否正常。不需要硬件。

---

## run_gnss_tx_grc.sh — GNU Radio Companion 启动

GRC 相关命令见 [grc/README.md](../grc/README.md)。

---

## 单元测试

```bash
cd ~/projects/gnss_tx

# 运行全部测试
PYTHONPATH=src python3 -m unittest discover -s tests -v

# 运行单个模块
PYTHONPATH=src python3 -m unittest tests.test_spreader -v
PYTHONPATH=src python3 -m unittest tests.test_ca_prn -v
PYTHONPATH=src python3 -m unittest tests.test_multi_sat_combiner -v
PYTHONPATH=src python3 -m unittest tests.test_top_block -v
```

---

## 实际采样率确认

`run_tx.py` 启动后会自动打印 UHD 硬件确认的实际采样率：

```
[INFO] Python TX runtime requested sample rate : 4092000.000 Sps (4.092000 Msps)
[INFO] Python TX runtime actual sample rate    : 4092000.000 Sps (4.092000 Msps)
[INFO] Python TX runtime sample-rate delta     : +0.000 Sps (+0.000000%)
```

若 `sample-rate delta` 不为零，说明 USRP 整数分频链做了舍入，实际 samples/chip 偏离理论值，
接收端需用对应的实际采样率来做码相位对齐。
