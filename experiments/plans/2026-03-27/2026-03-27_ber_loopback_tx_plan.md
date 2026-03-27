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

### 3.1 硬件参数汇总（双手册交叉核对）

B210 核心 RFIC 为 **Analog Devices AD9361**，从两份手册获得完整参数：

| 参数 | 数值 | 来源 | 说明 |
|------|------|------|------|
| TX 最大输出功率（800 MHz，芯片级） | **8 dBm** | AD9361 Table 1 | 1 MHz 单音，50 Ω 负载 |
| TX 最大输出功率（B210 整机） | **>10 dBm** | B210 Spec Sheet | 含外部 RF 开关网络 |
| TX 功率控制范围 / 分辨率 | 90 dB / 0.25 dB | AD9361 Table 1 | — |
| TX Carrier Leakage（0 dB 数字衰减） | **−50 dBc** | AD9361 Table 1 | 本振泄露相对载波功率 |
| **RX RF 输入绝对最大额定值（峰值）** | **+2.5 dBm** | AD9361 Table 11 | **超过将永久损坏芯片** |
| RX IIP3（800 MHz，最大增益） | −18 dBm | AD9361 Table 1 | 1 dB 压缩点 ≈ −28 dBm |
| RX 增益范围 | 0 ~ 74.5 dB | AD9361 Table 1 | 步进 1 dB |
| RX 噪声系数（800 MHz，最大增益） | 2 dB | AD9361 Table 1 | — |

### 3.2 操作流程：频谱仪先行，衰减量按实测决定

```
步骤 ①  B210 TX → 同轴线 → 频谱仪
         记录实测功率 P_meas（dBm）

步骤 ②  按下表选定衰减器 A（dB）

步骤 ③  B210 TX → [衰减器 A dB] → 同轴线 → B210 RX
```

**衰减量决策表**（目标：RX 输入峰值 ≤ 0 dBm，在 +2.5 dBm 绝对限值基础上留 2.5 dB 裕量）

> GPS 扩频信号峰均比（PAPR）约 0~3 dB，在频谱仪平均功率读数基础上额外加 3 dB 后再算衰减量。

| 频谱仪读数 P_meas | 考虑 PAPR 后峰值估算 | 最小衰减 A_min | **推荐选择** | 衰减后 RX 输入（估算） |
|-------------------|----------------------|---------------|--------------|------------------------|
| +10 dBm | +13 dBm | 13 dB | **20 dB 衰减器** | −10 dBm，安全 |
| +8 dBm | +11 dBm | 11 dB | **20 dB 衰减器** | −12 dBm，安全 |
| +5 dBm | +8 dBm | 8 dB | **20 dB 衰减器** | −15 dBm，安全 |
| ≤ +0 dBm | ≤ +3 dBm | 3 dB | **10 dB 衰减器** | ≤ −10 dBm，安全 |
| 未测量 | 未知 | — | **30 dB 衰减器（兜底）** | 保守安全 |

### 3.3 SNR 估算（两种场景）

噪声底（4.092 MHz BW，NF = 2 dB）：N ≈ −106 dBm

**场景 A：有 30 dB 衰减器，tx_gain = 89 dB（全功率）**

```
TX 输出：         +10 dBm
RX 输入：         10 − 30 − 1 = −21 dBm   安全裕量 23.5 dB
宽带 SNR：        −21 − (−106) = +85 dB
捕获后 SNR：      +85 + 43 = +128 dB  ← BER 理论趋近于 0
```

**场景 B：无衰减器，tx_gain = 70 dB（软件限幅）**

```
TX 输出：         70 − 79.75 ≈ −10 dBm
RX 输入：         −10 − 1 = −11 dBm     安全裕量 13.5 dB ✅
宽带 SNR：        −11 − (−106) = +95 dB
捕获后 SNR：      +95 + 43 = +138 dB  ← 同样远超要求，BER 无影响
```

**结论：两种场景下 SNR 均远超捕获门限，BER 测量结果等效。无衰减器时通过软件限制 tx_gain ≤ 70 dB 即可安全运行。**

---

## 四、发端分步执行计划

### Step 0：安全核查（必须最先完成，预计 5~15 分钟）

根据是否有衰减器，选择对应分支：

---

**分支 A：有衰减器（推荐）**

1. **TX → 频谱仪**：先将 B210 TX 输出接频谱仪，启动 TX，记录实测功率 P_meas
2. **查决策表**（§3.2）：根据 P_meas 选定衰减器规格
3. **改接线路**：断开频谱仪，串入衰减器后接 B210 RX

完成标志：
- [ ] 已记录 P_meas = ________ dBm，tx_gain = ________ dB
- [ ] 已选定衰减器：________ dB
- [ ] 衰减后 RX 输入估算 = ________ dBm（须 ≤ 0 dBm）
- [ ] 接线：`B210 TX → [衰减器] → [线缆] → B210 RX` 已确认

---

**分支 B：无衰减器，软件限幅（当前执行方案）**

无衰减器时必须通过软件限制 tx_gain，禁止超过安全上限：

```
B210 TX 输出估算：tx_gain − 79.75 dBm（100 MHz 附近）
RX 绝对最大输入：+2.5 dBm
目标 RX 输入：≤ −10 dBm（保守，安全裕量 12.5 dB）
→ tx_gain 上限：70 dB
```

| tx_gain | TX 输出估算 | RX 输入估算 | 是否安全 |
|---------|-----------|------------|---------|
| 35 dB | −45 dBm | −46 dBm | ✅ 安全（先用此值热身） |
| 50 dB | −30 dBm | −31 dBm | ✅ 安全 |
| 70 dB | −10 dBm | −11 dBm | ✅ 安全（无衰减器最大推荐值） |
| 80 dB | 0 dBm | −1 dBm | ⚠️ 接近红线，不建议 |
| **≥ 83 dB** | **≥ +3 dBm** | **≥ +2 dBm** | **❌ 危险，禁止** |

操作步骤：
1. 使用 `tx_b210_cable_loopback.yaml`（默认 tx_gain=70 dB）或在命令行用 `--tx-gain` 覆盖
2. 直接接线：`B210 TX(TX/RX) → [线缆] → B210 RX(RX2)`
3. 首次运行先用 tx_gain=35 dB 验证链路正常，再提升到 70 dB

完成标志：
- [ ] 已确认 tx_gain ≤ 70 dB（无衰减器时）
- [ ] 接线：`B210 TX → [线缆] → B210 RX` 已确认（无衰减器）

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
