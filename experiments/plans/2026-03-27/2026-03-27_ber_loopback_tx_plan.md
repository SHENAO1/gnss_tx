# 发射端实验计划：闭环 BER 验证（发端视角）

> 创建时间：2026-03-27
> 对应接收端计划：`/home/shen/projects/GNSS_RX/experiments/plans/2026-03-27/2026-03-27_ber_loopback_rx_plan.md`
> 状态：`[ ]` 待执行
> 里程碑目标：Milestone 1 — 射频线直连闭环 BER 验证

---

## 一、当前发端代码状态摘要

| 模块 | 状态 | 文件 |
|------|------|------|
| GPS L1 C/A PRN 码生成 | ✅ 已实现 | `src/gnss_tx/ca/prn_generator.py` |
| 导航 bit 循环源 | ✅ 已实现（8 bit 固定模式） | `src/gnss_tx/nav/nav_bits.py` |
| BPSK 扩频调制 | ✅ 已实现 | `src/gnss_tx/signal/spreader.py` |
| 预生成 + 循环回放 | ✅ 已实现 | `src/gnss_tx/gr/top_block.py` |
| USRP B210 发射 | ✅ 已验证可用 | `src/gnss_tx/usrp/b210_sink.py` |
| **多 bit 已知序列发射** | ✅ 可直接使用（见下方说明） | `configs/tx_b210_visible_spectrum.yaml` |

**结论：发端无需修改代码，直接使用现有配置运行即可。**

---

## 二、发端已知 bit 序列说明（BER 参考源）

当前 `DEFAULT_NAV_PATTERN` 定义在 `src/gnss_tx/nav/nav_bits.py:13`：

```
DEFAULT_NAV_PATTERN = (1, -1, 1, 1, -1, -1, 1, -1)
```

换算为 0/1 表示（1→1，-1→0）：`1, 0, 1, 1, 0, 0, 1, 0`

- 循环周期：8 bit
- 导航速率：50 bps
- 每个 bit 时长：20 ms
- 一个完整循环时长：8 × 20 ms = **160 ms**
- 接收端对比参考：`[1, 0, 1, 1, 0, 0, 1, 0]`（循环重复，需对齐相位）

**BER 统计所需发射时长估算：**

| BER 目标总 bit 数 | 所需时长 | 说明 |
|-------------------|----------|------|
| ≥ 10^3 bit | 20 秒 | 初步验证 |
| ≥ 10^4 bit | 200 秒（≈3.3 分钟） | 目标最低要求 |
| ≥ 10^5 bit | 2000 秒（≈33 分钟） | 理想精度，可选 |

**今日推荐：采集 250 秒（≈12,500 bit），超过 10^4 门限留足余量。**

---

## 三、功率安全核查（发端责任）⚠️

### 3.1 规格书参数摘录（b200-b210_spec_sheet.pdf）

| 参数 | 数值 | 单位 | 说明 |
|------|------|------|------|
| TX 输出功率 | >10 | dBm | 典型值（单通道，full gain） |
| RX IIP3 | −20 | dBm | @典型噪声系数 |
| SSB/LO 抑制 | −35/50 | dBc | 本振泄露抑制量 |
| RX 噪声系数 | <8 | dB | — |
| ADC/DAC 分辨率 | 12 | bit | — |
| **RX 最大允许输入功率** | **未注明** | — | **规格书缺失此关键参数** |

### 3.2 射频线直连功率预算

```
TX 输出（典型）：+10 dBm（tx_gain 典型设置下）
同轴电缆损耗：  − 1 dB（短线估算）
RX 输入估计：  ≈ +9 dBm
─────────────────────────────────────────────
RX IIP3：       −20 dBm
RX 1dB 压缩点： ≈ −30 dBm（IIP3 − 10 dB 经验值）
─────────────────────────────────────────────
过驱动量：      +9 − (−30) = +39 dB ← ⚠️ 严重过载
```

### 3.3 结论与强制措施

**不加衰减器直接射频线直连将导致 RX 前端严重饱和，可能损坏硬件。**

**必须采取措施（二选一）：**

| 方案 | 推荐度 | 说明 |
|------|--------|------|
| **串联 30 dB 固定衰减器** | ⭐ 首选 | 衰减后 RX 输入 ≈ −21 dBm，远低于压缩点，安全 |
| **串联 20 dB 固定衰减器** | ✅ 可用 | 衰减后 RX 输入 ≈ −11 dBm，仍留有余量 |
| 仅降低 tx_gain（不加衰减器） | ⚠️ 有风险 | UHD tx_gain=0 时实际输出功率不确定，不推荐 |

**补充建议：**
- 若有频谱仪，在接 RX 之前先用频谱仪测量 TX 实际输出功率，确认后再连 RX。
- 若无频谱仪，使用 30 dB 衰减器 + 低 tx_gain（20 dB）作为保守起点。

---

## 四、发端分步执行计划

### Step 0：安全核查（必须最先完成，预计 10 分钟）

**完成标志：** 衰减器已连接到 TX 输出端口，且频谱仪已确认 TX 输出功率
或 已决策使用保守增益设置并记录。

```
B210 TX 端口（TX/RX SMA） → [衰减器 ≥ 20 dB] → [同轴电缆] → B210 RX 端口
```

### Step 1：确认发端配置文件（预计 5 分钟）

查看当前基线配置：

```bash
cat /home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml
```

确认以下参数：
- `center_freq`：100000000（100 MHz）
- `sample_rate`：4092000（4.092 MHz）
- `prn_id`：1
- `nav_pattern`：`"1 0 1 1 0 0 1 0"`（与 BER 参考序列一致）
- `tx_gain`：建议不超过 20 dB（配合衰减器使用）

**完成标志：** 确认以上参数，记录 tx_gain 实际值。

### Step 2：启动发射（预计 2 分钟操作 + 等待接收端完成）

```bash
cd /home/shen/projects/gnss_tx
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 300
```

说明：
- `--duration 300`：发射 300 秒（≈15,000 bit，满足 ≥10^4 门限）
- 发射期间保持终端运行，观察是否有 underflow（U）报警
- 若出现连续 U 报警，说明 USB 带宽不足，可降低采样率或检查 USB 连接

**完成标志：** TX 终端显示正常运行，无持续 underflow，接收端已完成采集。

### Step 3：发射结束后记录

记录以下信息（填入接收端实验记录）：
- 实际使用的 tx_gain（dB）
- 衰减器规格（dB）
- center_freq（Hz）
- nav_pattern 字符串
- 实际发射时长（秒）

---

## 五、风险点与预案

| 风险 | 概率 | 预案 |
|------|------|------|
| 忘接衰减器直连导致 RX 损坏 | 中 | 严格执行 Step 0，接线前用万用表或目视确认衰减器在路 |
| USRP 未被系统识别 | 低 | `uhd_find_devices` 检查；重插 USB |
| 频繁 underflow（U） | 中 | 降低 tx_gain 或使用 `--dry-run` 先验证流图 |
| nav_pattern 与 BER 参考不一致 | 低 | Step 1 中显式打印并确认 nav_pattern 字段 |

---

## 六、附：快速启动命令参考

```bash
# 干运行（不开 RF，只测流图）
cd /home/shen/projects/gnss_tx
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --dry-run

# 正式发射（300 秒）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 300
```
