# 发端功率摸底测试记录

> 创建时间：2026-03-27
> 测试目的：确定两台 USRP B210 直连（不加衰减器）时安全的 tx_gain 和 amplitude 范围
> 测试阶段：发端独立测试（TX → 频谱仪），频谱确认后再接 RX

---

## 一、背景与安全边界回顾

| 参数 | 数值 | 来源 |
|------|------|------|
| B210 TX 典型输出功率（标称值） | > +10 dBm | [B210 Spec Sheet](../../../../../DataSheet/B200_B210/b200-b210_spec_sheet.pdf) p.2，RF Performance 表，"Power Output" 行（Typ 列，即标称典型值，对应 tx_gain 最大时的输出功率，用于反推公式 offset） |
| AD9361 RX 绝对最大输入（峰值） | **+2.5 dBm** | [AD9361 DataSheet](../../../../../DataSheet/AD9361/ad9361.pdf) p.17，**Table 11 Absolute Maximum Ratings**，RF Inputs (Peak Power) 行 |
| 目标 RX 安全输入 | ≤ −10 dBm | 保守裕量：+2.5 dBm − 12.5 dB（基于上行 AD9361 Table 11 数据推算） |
| TX 输出估算公式（100 MHz 实测，serial=193982） | `P_tx ≈ (tx_gain − 66) dBm` | **实测标定**（见下方，2026-03-27 serial=193982） |
| TX 输出估算公式（100 MHz 实测，serial=8003272） | `P_tx ≈ (tx_gain − 57) dBm` | **实测标定**（见第十节，2026-03-27 serial=8003272，同台设备功率高 9 dB） |
| GPS 扩频信号频谱带宽（C/A 码） | 主瓣宽度约 2 MHz（码片率 1.023 Mcps） | GPS ICD（IS-GPS-200），C/A 码码片率 1.023 Mcps，主瓣零点间距 = 2 × 码片率 |
| PSD 峰值 → 带内总功率换算 | `P_total ≈ P_psd_peak + 33 dB`（RBW=1 kHz） | 数学推导：10·log₁₀(BW_主瓣 / RBW) = 10·log₁₀(2×10⁶ / 10³) = 33 dB |

> ⚠️ **安全上限修正（基于 2026-03-27 实测，两台设备）**
>
> 原文档基于 `offset = 79.75` 推算，在 **100 MHz 频点误差约 14 dB**（B210 低频段增益远高于 L1 频段）。
> - **serial=193982**（offset=66）：tx_gain = 60 dB 时总功率已超安全阈值，无衰减器直连上限 **tx_gain ≤ 50 dB**
> - **serial=8003272**（offset=57）：功率比 193982 高 **9 dB**，无衰减器直连上限 **tx_gain ≤ 45 dB**
> - **推荐使用 serial=193982 作 TX**，配套 tx_gain=50（见第十节分析）

### TX 输出估算公式推导与实测修正

原始公式 `P_tx ≈ (tx_gain − 79.75) dBm` 基于 B210 标称最大值。

#### 物理模型：tx_gain 控制的是衰减器

B210 内部 AD9361 TX 链路结构如下：

```
数字基带 → DAC → 混频/滤波 → [可调衰减器] → SMA 输出
                                    ↑
                             UHD 通过这里控制功率
```

TX 功率控制的本质是**衰减器**，不是放大器——芯片有固定的最大输出功率，通过调节衰减量来降低输出。UHD 的 tx_gain 是对衰减器的反向包装：

```
tx_gain = 89.75 dB  →  内部衰减 = 0 dB      →  最大功率输出
tx_gain =  0    dB  →  内部衰减 = 89.75 dB  →  最小功率输出

内部衰减量 = 89.75 − tx_gain  (dB)
```

#### 公式的物理推导

```
P_tx = P_max − 内部衰减量
     = P_max − (89.75 − tx_gain)
     = tx_gain + (P_max − 89.75)
     = tx_gain + (10 − 89.75)        ← 代入 P_max = +10 dBm（手册标称）
     = (tx_gain − 79.75) dBm
```

各项的物理含义：

| 项 | 含义 |
|----|------|
| `P_max = +10 dBm` | AD9361 固有最大输出（硬件上限，B210 Spec Sheet p.2） |
| `89.75 dB` | UHD tx_gain 范围上限，对应内部衰减器从全开到全关的范围 |
| `offset = 89.75 − 10 = 79.75` | 两者之差，将绝对功率参考点编码进公式 |

> **offset 的倒推逻辑**：已知一个点（tx_gain=89.75 → P_tx=+10 dBm），代入线性模型
> `P_tx = tx_gain − offset`，解得 `offset = 89.75 − 10 = 79.75`。
> 本质上是用手册的最大输出标定了公式的绝对参考点。

```
B210 TX 增益范围（UHD 驱动）：0 ~ 89.75 dB
B210 手册标称最大输出：> +10 dBm（对应 tx_gain = 89.75 dB）
→ P_tx ≈ (tx_gain − 79.75) dBm（理论，适用于 GPS L1 1575 MHz 附近）
```

> 括号的含义：P_tx 的**数值**等于 (tx_gain − 79.75)，**单位**是 dBm。
> tx_gain 和 79.75 均为无单位的 dB 数，相减后赋予绝对功率单位 dBm。

<a id="calibration-100mhz"></a>

**2026-03-27 实测标定（serial=193982，100 MHz，amplitude=1.0）：**

```
实测：tx_gain=70 → 频谱仪 PSD 峰值 ≈ -28 dBm（RBW=1 kHz）
换算总功率：P_total = -28 + 33 = +5 dBm
倒推实测 offset：70 - 5 = 65 ≈ 66 dB

→ P_tx（100 MHz 实测）≈ (tx_gain − 66) dBm（amplitude=1.0 时）
  原公式误差约 14 dB（B210 100 MHz 功率远高于 1575 MHz）
```

`amplitude` 参数的影响（实测验证）：

```
P_tx = (tx_gain − 66) + 20·log₁₀(amplitude)  dBm（100 MHz 实测公式）

实测验证：
  tx_gain=70, amplitude=0.5 → PSD 峰值 ≈ -34 dBm（理论 -28-6=-34 ✓）
  tx_gain=70, amplitude=0.1 → PSD 峰值 ≈ -48 dBm（理论 -28-20=-48 ✓）
```

---

## 二、本次测试增益档位计划

> **实际执行情况（2026-03-27）：** 本阶段完成了比计划更系统的全扫描测试，
> 额外增加了 gain=0/10/20/30/40/60 dB 各档，形成 0~70 dB 每 10 dB 步进共 8 档全扫描。
> 所有测试均为 **TX → 频谱仪**，无 RX，无损坏风险。

| 档位 | tx_gain | amplitude | TX 总功率估算（实测公式） | 备注 | 实际执行 |
|------|---------|-----------|--------------------------|------|---------|
| T0   | 0 dB    | 1.0       | −66 dBm | 底噪验证 | ✅ 已测 |
| T1   | 10 dB   | 1.0       | −56 dBm | — | ✅ 已测 |
| T2   | 20 dB   | 1.0       | −46 dBm | — | ✅ 已测 |
| T3   | 30 dB   | 1.0       | −36 dBm | — | ✅ 已测 |
| T4   | 40 dB   | 1.0       | −26 dBm | — | ✅ 已测 |
| T5   | 50 dB   | 1.0       | −16 dBm | **安全上限推荐值** | ✅ 已测 |
| T6   | 60 dB   | 1.0       | −6 dBm | ⚠️ 超安全阈值 | ✅ 已测（仅接频谱仪） |
| T7   | 70 dB   | 1.0       | +5 dBm  | ⛔ 禁止直连 RX | ✅ 已测（仅接频谱仪） |
| T8   | 70 dB   | 0.5       | −1 dBm  | ⛔ 仍超安全阈值 | ✅ 已测（仅接频谱仪） |
| T9   | 70 dB   | 0.1       | −15 dBm | 等效 T5 功率 | ✅ 已测 |

> amplitude 对输出功率影响（实测验证）：
> - amplitude=0.5 → −6 dB（实测确认）
> - amplitude=0.1 → −20 dB（实测确认）

---

## 三、测试记录表（实测数据）

> 频谱仪设置：Center=100 MHz，Span=6 MHz，RBW=1 kHz，VBW=1 kHz，Att=0 dB，Ref=−20 dBm
>
> **注意**：P_psd_peak 为频谱仪显示的 PSD 峰值（每 RBW=1 kHz 的功率），
> **带内总功率** = P_psd_peak + 10·log₁₀(BW_主瓣/RBW) ≈ P_psd_peak + **33 dB**（BW≈2 MHz）。
> 安全判定以**带内总功率**为准，而非 PSD 峰值。

| 档位 | tx_gain | amplitude | 测试时间 | PSD 峰值 (dBm) | 带内总功率 (+33 dB) | 接 RX 预估输入 (−1 dB 线缆) | 安全? | 频谱特征 |
|------|---------|-----------|---------|---------------|--------------------|-----------------------------|-------|---------|
| T0   | 0 dB    | 1.0 | 14:34 | ≈ −100（噪底） | — | — | ✓ | 信号完全淹没噪底，不可见 |
| T1   | 10 dB   | 1.0 | 14:43 | ≈ −88 | ≈ −55 dBm | ≈ −56 dBm | ✓ | 微弱扩频轮廓刚露出噪底 |
| T2   | 20 dB   | 1.0 | 14:49 | ≈ −78 | ≈ −45 dBm | ≈ −46 dBm | ✓ | 扩频轮廓可见，sinc 形状初现 |
| T3   | 30 dB   | 1.0 | 14:51 | ≈ −68 | ≈ −35 dBm | ≈ −36 dBm | ✓ | sinc 旁瓣清晰，零点可见 |
| T4   | 40 dB   | 1.0 | 14:58 | ≈ −58 | ≈ −25 dBm | ≈ −26 dBm | ✓ | sinc 形状完整，旁瓣明显 |
| **T5** | **50 dB** | **1.0** | **14:59** | **≈ −48** | **≈ −15 dBm** | **≈ −16 dBm** | **✓ 推荐** | **信号强，sinc 清晰，安全裕量 6 dB** |
| T6   | 60 dB   | 1.0 | 15:00 | ≈ −38 | ≈ −5 dBm  | ≈ −6 dBm  | ⚠️ 超限 | 总功率超 −10 dBm 安全阈值 |
| T7   | 70 dB   | 1.0 | 15:02 | ≈ −28 | ≈ +5 dBm  | ≈ +4 dBm  | ⛔ 极危险 | 远超 AD9361 最大输入 (+2.5 dBm) |
| T8   | 70 dB   | 0.5 | 16:58 | ≈ −34 | ≈ −1 dBm  | ≈ −2 dBm  | ⛔ 危险 | 仍超安全阈值，amplitude=0.5 不够 |
| T9   | 70 dB   | 0.1 | 17:04 | ≈ −48 | ≈ −15 dBm | ≈ −16 dBm | ✓ | 等效 T5，证明功率线性可控 |

---

## 四、安全判定（实测结论）

安全判定标准（基于带内总功率）：

```
P_rx = P_total_tx − L_cable（约 1 dB）≤ −10 dBm
→ P_total_tx ≤ −9 dBm
→ PSD 峰值（RBW=1 kHz）≤ −9 − 33 = −42 dBm
→ 对应 tx_gain ≤ 70 − (−28 − (−42)) = 70 − 14 = 56 dB
→ 取保守整档：tx_gain ≤ 50 dB
```

> ⚠️ **修正说明**：原文档上限"70 dB"是基于 `offset=79.75` 的公式估算，
> 在 100 MHz 频点实测误差约 14 dB（B210 低频增益远高于 L1 频段），
> 实际安全上限应为 **50 dB**，不是 70 dB。

| 结论 | 选定 tx_gain | 选定 amplitude | 预估 RX 输入 (dBm) | 安全裕量 | 是否安全 |
|------|-------------|---------------|-------------------|---------|---------|
| **推荐参数** | **50 dB** | **1.0** | **≈ −16 dBm** | **6 dB** | **✓ 安全** |
| 保守参数 | 40 dB | 1.0 | ≈ −26 dBm | 16 dB | ✓ 极安全 |
| 高增益等效（不推荐用于直连） | 70 dB | 0.1 | ≈ −16 dBm | 6 dB | ✓ 安全（但 amplitude 太低，数字底噪影响较大） |
| ~~原文档上限~~（实测超标） | ~~70 dB~~ | ~~1.0~~ | ~~≈ +4 dBm~~ | ~~—~~ | ~~⛔ 极危险~~ |

**综合推荐（无衰减器+射频直连）：**

```
tx_gain  = 50 dB
amplitude = 1.0
预计 RX 输入 ≈ −16 dBm（安全，AD9361 裕量 18.5 dB）
```

如需更强信号（例如提升 BER 测试 SNR），可在**接好衰减器**后提升增益。

---

## 五、频谱仪参数说明

### 5.1 参考电平（Ref Level）

**参考电平是频谱仪屏幕最顶格对应的功率值。**

本次所有截图均设置为 `Ref = −20 dBm`，配合 `刻度/格 = 10 dB`，屏幕共 10 格，因此：

```
顶格（第 0 格）= −20 dBm
底格（第 10 格）= −20 − 10×10 = −120 dBm
```

这与截图中 Y 轴范围 −20 dBm 到 −120 dBm 完全一致。

**如何选取参考电平：**
- 应设置为**略高于被测信号最强峰值**，避免信号超出屏幕顶部（overload）
- 不要设得过高，否则噪底会被压到屏幕下方，弱信号看不清
- 本次测试信号最强约 −28 dBm（PSD 峰值），参考电平 −20 dBm 留有约 8 dB 余量，合理

### 5.2 输入衰减器（Att）

本次所有截图均设置为 `Att = 0 dB（手动）`。

频谱仪内部在射频输入端有一个可调步进衰减器，其作用是：

| 情形 | 衰减器影响 |
|------|-----------|
| 衰减器增大 | 保护混频器不过载，但显示噪底升高（灵敏度降低） |
| 衰减器减小 | 灵敏度提高，噪底更低，但输入过强时混频器可能压缩失真 |

**正常（自动）模式**：频谱仪根据参考电平自动设置衰减。`Ref = −20 dBm` 时，自动模式通常会加 10~20 dB 衰减，导致噪底提高 10~20 dB，弱信号难以观测。

**本次手动设为 0 dB 的原因**：被测扩频信号较弱（PSD 峰值约 −28 dBm 到 −100 dBm），需要最高灵敏度来观察信号。手动 Att=0 dB 使噪底尽可能低（约 −100 dBm），可以清楚看到信号形状。

> 注意：手动 Att=0 dB 时，若输入信号过强（> 约 +20 dBm），频谱仪混频器可能损坏。
> 本次 TX 最高 PSD 峰值约 −28 dBm，**带内总功率约 +5 dBm**（gain=70 时），
> 频谱仪通常可承受高达 +20~+30 dBm 输入，因此安全。

### 5.3 PSD 读数与带内总功率的关系

**频谱仪显示的是功率谱密度（PSD），单位是每 RBW 带宽的功率，而非信号总功率。**

```
P_psd_peak (dBm)  ← 频谱仪屏幕上读到的数值（每 RBW=1 kHz 的功率）
P_total    (dBm)  ← 信号带内积分总功率（RX 实际收到的功率）

换算：P_total ≈ P_psd_peak + 10·log₁₀(BW_等效 / RBW)

对于 GPS C/A 码（码片率 1.023 Mcps，主瓣宽度 ≈ 2 MHz）：
  P_total ≈ P_psd_peak + 10·log₁₀(2×10⁶ / 10³)
           = P_psd_peak + 33 dB
```

**这意味着**：频谱仪显示 −48 dBm，实际总功率约 −15 dBm。**安全判定必须以总功率为准**，直接用 PSD 读数判断会严重低估风险（差距约 33 dB）。实测验证见[一、2026-03-27 实测标定（serial=193982，100 MHz）](#calibration-100mhz)。

#### 推导过程

频谱仪用宽度为 RBW 的"窗口"逐频点扫描，每个格子显示该 RBW 带宽内的功率。
若信号在带宽 BW 内的 PSD 近似平坦（峰值为 P_psd_peak），则带内总功率为各格子之和：

```
P_total (线性) = P_psd (线性/Hz) × BW
               = P_psd_peak (线性) × (BW / RBW)

转换到 dBm：
P_total (dBm) = P_psd_peak (dBm) + 10·log₁₀(BW / RBW)

代入数值（BW = 2 MHz，RBW = 1 kHz）：
  10·log₁₀(2×10⁶ / 10³) = 10·log₁₀(2000) = 10 × 3.301 ≈ 33 dB
```

**直觉理解**：频谱仪用 1 kHz 的窗口扫描，而信号实际占了 2 MHz，相当于把 2000 个格子的功率加起来，比单格读数高 33 dB。

> **注意**：GPS C/A 码的频谱是 sinc² 形状，主瓣内并非完全平坦，上述换算是近似估算，实际总功率略低于 P_psd_peak + 33 dB，误差约 1–2 dB（可忽略，偏保守）。

### 5.4 B210 低频段增益远高于 L1 频段的原因

文档中多处提到"100 MHz 实测比 L1 公式偏高约 14 dB"，本节从数据手册和电路原理两个角度解释原因。

#### 数据手册证据

**AD9361 Table 1（[ad9361.pdf](../../../../../DataSheet/AD9361/ad9361.pdf) p.4–6）**：TX 最大输出功率随频率单调递减：

| 频率 | TX 最大输出功率（Typ） |
|------|----------------------|
| 800 MHz | **8 dBm** |
| 2.4 GHz | **7.5 dBm** |
| 5.5 GHz | **6.5 dBm** |

频率从 800 MHz 升到 5.5 GHz，输出功率下降了 1.5 dB。反过来，100 MHz 远低于 800 MHz，因此实际输出功率高于 8 dBm，高于 B210 Spec Sheet 标称的 ">10 dBm"。

**AD9361 Figure 16（[ad9361.pdf](../../../../../DataSheet/AD9361/ad9361.pdf) p.24）**："TX Output Power vs. TX LO Frequency, Attenuation Setting = 0 dB, Single Tone Output"，图中在 700–900 MHz 频段内 TX 输出约为 7.5–9.5 dBm，且呈现随频率升高略有下降的趋势。虽然图表未覆盖 100 MHz，但趋势延伸方向支持低频功率更高的结论。

**B210 Spec Sheet（[b200-b210_spec_sheet.pdf](../../../../../DataSheet/B200_B210/b200-b210_spec_sheet.pdf) p.2）**：仅给出 "Power Output >10 dBm"，**未注明测试频率**。该值是面向典型蜂窝/SDR 应用标定的，最可能在 800 MHz–2 GHz 附近测量，不代表 100 MHz 的实际输出。

#### 电路物理原因

**① 射频晶体管增益随频率下降**

功率放大管（PA）的功率增益 G 近似为：

```
G ∝ (fT / f)²   （f 远低于 fT 时）
```

频率越低，增益越高。AD9361 内部 TX 链路在 100 MHz 时的链路增益高于 1575 MHz，这是最根本的原因。

**② 混频器寄生电容损耗与频率成正比**

直接变频架构中，混频器（Gilbert cell）的上变频损耗来源之一是节点寄生电容的旁路。寄生电容的阻抗为：

```
Z = 1 / (j·2π·f·C)
```

频率越低，寄生阻抗越大，旁路电流越少，混频损耗越小，输出功率越高。

**③ B210 工作下限接近 70 MHz**

B210（AD9361）的 TX 工作下限是 ~47 MHz（AD9361 规格），100 MHz 已非常接近下限。接近下限频率时，内部 LC 匹配网络偏离设计中心，阻抗变换比改变，可能使输出功率出现额外偏高（或偏低），具体方向取决于板级设计，**B210 在此频段的实际功率需以实测为准**，手册标称值参考意义有限。

#### 对本实验公式的影响

| 频率 | offset 估算值 | 来源 |
|------|--------------|------|
| L1（1575 MHz，标称） | 79.75 dB | B210 Spec Sheet p.2，`offset = 89.75 − 10` |
| 100 MHz（实测修正） | **66 dB** | 2026-03-27 实测标定（serial=193982） |
| 差值 | **~14 dB** | B210 100 MHz 输出比 L1 公式高约 14 dB |

> 结论：**在 100 MHz 工作时，必须以实测标定公式（offset=66）为准**，B210 Spec Sheet 的标称值仅适用于典型中频段（约 800 MHz–2 GHz），不能直接用于 100 MHz 链路预算。

---

## 六、命令速查

### 5.1 硬件检测

```bash
# 检测系统是否识别到 USRP
uhd_find_devices

# 查看 B210 详细信息（固件版本、序列号等）
uhd_usrp_probe

# 若有两台 B210，按序列号区分
uhd_find_devices --args="type=b200"
```

### 5.2 关于 GNU Radio 流图预览与软件频谱

加 `--qt-preview` 参数可同时弹出 GNU Radio QT 预览窗口，窗口内包含：

- **上半部分**：时域 IQ 波形（`TX Baseband Time Preview`）
- **下半部分**：基带频谱（`TX Baseband Spectrum Preview`，FFT 2048 点，Blackman-Harris 窗）

> 注意：`--qt-preview` 显示的是**基带**信号（发射前的数字域），频率轴以 0 Hz 为中心，带宽 ±2.046 MHz。
> 这与频谱仪看到的射频频谱（以 100 MHz 为中心）不同，两者互为补充。
>
> 需要桌面显示环境（`DISPLAY` 或 `WAYLAND_DISPLAY`），SSH 无显示器时加 `--qt-preview` 会报错退出。

### 5.3 TX → 频谱仪（各档位发射命令）

```bash
# 切换到项目根目录
cd /home/shen/projects/gnss_tx

# 档位 L1：tx_gain=35，amplitude=1.0（热身）—— 不开 QT 预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 35 \
    --amplitude 1.0 \
    --duration 30

# 档位 L1：同上，开启 GNU Radio 基带流图 + 软件频谱
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 35 \
    --amplitude 1.0 \
    --duration 30 \
    --qt-preview

# 档位 L2：tx_gain=50，amplitude=1.0
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 50 \
    --amplitude 1.0 \
    --duration 30

# 档位 L2：开启 QT 预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 50 \
    --amplitude 1.0 \
    --duration 30 \
    --qt-preview

# 档位 L3：tx_gain=70，amplitude=1.0（无衰减器最大推荐值）
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 1.0 \
    --duration 30

# 档位 L3：开启 QT 预览
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 1.0 \
    --duration 30 \
    --qt-preview

# 档位 L4：tx_gain=70，amplitude=0.5
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 0.5 \
    --duration 30

# 档位 L5：tx_gain=70，amplitude=0.1
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 70 \
    --amplitude 0.1 \
    --duration 30
```

> **注意**：`--tx-gain` 和 `--amplitude` 是否支持命令行覆盖，取决于 `run_tx.py` 是否实现了对应参数。
> 如不支持，直接编辑 `configs/tx_b210_cable_loopback.yaml` 中的 `tx_gain` 和 `amplitude` 字段。

### 5.3 干运行（不开 RF，仅验证流图是否报错）

```bash
cd /home/shen/projects/gnss_tx
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --dry-run
```

### 5.4 查看当前配置文件

```bash
cat /home/shen/projects/gnss_tx/configs/tx_b210_cable_loopback.yaml
```

### 5.5 临时修改配置后发射（不想写命令行参数时）

```bash
# 先备份原配置
cp configs/tx_b210_cable_loopback.yaml configs/tx_b210_cable_loopback.yaml.bak

# 用编辑器修改 tx_gain 和 amplitude，然后发射
# 例如改完之后：
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --duration 30
```

---

## 八、观测重点（发射时看终端输出）

| 现象 | 含义 | 处理 |
|------|------|------|
| 无任何 `U` 打印 | 正常，无 underflow | 继续 |
| 偶发 `U`（1~2 次） | 轻微 USB 抖动，可接受 | 继续观察 |
| 持续 `U U U U...` | USB 带宽不足或 CPU 过载 | 降低 sample_rate 或关闭后台应用 |
| 程序报错退出 | 配置错误或设备问题 | 看报错信息，先跑 `uhd_find_devices` |

---

## 九、实测结论总结（serial=193982，2026-03-27 完成）

### 9.1 公式修正

| 项目 | 原估算（L1 公式） | 100 MHz 实测修正 |
|------|-----------------|----------------|
| TX 总功率公式 | `P_tx = gain − 79.75 dBm` | `P_tx ≈ gain − 66 dBm` |
| gain=70 时 TX 输出 | −9.75 dBm（估算） | **≈ +5 dBm（实测）** |
| 偏差原因 | 公式按 GPS L1 标定 | B210 在 100 MHz 功率远高于 1575 MHz |

### 9.2 频谱信号质量（从截图观察）

- **gain ≥ 20 dB**：扩频 sinc 轮廓可见，信号质量足以接收
- **gain ≥ 30 dB**：sinc 旁瓣零点清晰，码片率 1.023 Mcps 频谱形状完整
- **gain = 10 dB**：信号刚刚露出噪底，可能不够 BER 测试使用
- **gain = 0 dB**：完全淹没噪底（符合预期）

### 9.3 推荐参数（无衰减器+射频直连 BER 测试，serial=193982 发）

```yaml
tx_gain:   50.0      # 无衰减器直连安全推荐值（RX 输入约 -16 dBm，裕量 6 dB）
amplitude: 1.0
```

### 9.4 下一步

- [x] TX → 频谱仪功率摸底（完成）
- [x] 推荐参数确认（gain=50 dB，amplitude=1.0）
- [ ] 改接线路：`B210 TX → [线缆] → B210 RX`
- [ ] 跳转执行 `../ber_loopback_tx/2026-03-27_ber_loopback_tx_plan.md` Step 2（正式 BER 发射）

---

## 十、第二台设备标定（serial=8003272，2026-03-27）

> **测试背景**：serial=193982 的摸底测试完成后，继续使用 serial=8003272 进行同等条件的发射标定，
> 以比较两台设备的输出功率差异，并确定两台设备直连时的最优 TX/RX 分配方案。

### 10.1 测试记录

> 频谱仪设置与第三节相同：Center=100 MHz，Span=6 MHz，RBW=1 kHz，VBW=1 kHz，Att=0 dB，Ref=−20 dBm

**第一组（amplitude=1.0，增益扫描）：**

| 档位 | tx_gain | amplitude | 测试时间 | PSD 峰值 (dBm) | 带内总功率 (+33 dB) | 频谱特征 |
|------|---------|-----------|---------|----------------|--------------------|---------|
| S0   | 0 dB    | 1.0 | 15:29 | ≈ −95（噪底）  | —       | 信号完全淹没噪底；约 98.5 MHz 处有 −85 dBm 窄带干扰（与发射无关，背景 RFI） |
| S1   | 10 dB   | 1.0 | 15:32 | ≈ −80 dBm | ≈ −47 dBm | sinc 轮廓可见，旁瓣零点初现 |
| S2   | 20 dB   | 1.0 | 15:33 | ≈ −70 dBm | ≈ −37 dBm | sinc 形状清晰，旁瓣零点（±1 MHz）可见 |
| S3   | 30 dB   | 1.0 | 15:34 | ≈ −60 dBm | ≈ −27 dBm | sinc 完整，第二旁瓣（±2 MHz）可见 |
| S4   | 40 dB   | 1.0 | 15:35 | ≈ −50 dBm | ≈ −17 dBm | 信号充裕，旁瓣结构完整 |
| S5   | 50 dB   | 1.0 | 15:36 | ≈ −40 dBm | ≈ −7 dBm  | ⚠️ 总功率已超 −10 dBm 安全阈值 |
| S6   | 60 dB   | 1.0 | 15:38 | ≈ −30 dBm | ≈ +3 dBm  | ⛔ 直连 RX 极危险 |
| S7   | 65 dB   | 1.0 | 16:53 | ≈ −25 dBm | ≈ +8 dBm  | ⛔ 直连 RX 极危险（70 dB 时频谱仪超量程，降至 65 dB 测量） |

**第二组（tx_gain=65 dB 固定，amplitude 变化）：**

| 档位 | tx_gain | amplitude | 测试时间 | PSD 峰值 (dBm) | 带内总功率 (+33 dB) | 备注 |
|------|---------|-----------|---------|----------------|--------------------|----|
| S8   | 65 dB   | 0.5 | 16:55 | ≈ −31 dBm | ≈ −2 dBm  | amplitude=0.5 → −6 dB（实测验证） |
| S9   | 65 dB   | 0.1 | —     | ≈ −45 dBm | ≈ −12 dBm | amplitude=0.1 → −20 dB（实测验证） |

### 10.2 标定公式（serial=8003272，100 MHz）

**物理模型：tx_gain 控制的是衰减器**

B210 内部 AD9361 TX 链路结构如下：

```
数字基带 → DAC → 混频/滤波 → [可调衰减器] → SMA 输出
                                   ↑
                            UHD 通过这里控制功率
```

TX 功率控制的本质是**衰减器**，不是放大器——芯片有固定的最大输出功率，通过调节内部衰减量来降低输出。UHD 的 `tx_gain` 是对衰减器的**反向包装**（gain 越大 → 衰减越小 → 输出越强）：

```
tx_gain = 89.75 dB  →  内部衰减 = 0 dB      →  最大功率输出
tx_gain =  0    dB  →  内部衰减 = 89.75 dB  →  最小功率输出

内部衰减量 = 89.75 − tx_gain  (dB)
```

因此 TX 输出功率为：

```
P_tx = P_max − 内部衰减量
     = P_max − (89.75 − tx_gain)
     = tx_gain + (P_max − 89.75)
     = tx_gain − offset            ← 令 offset = 89.75 − P_max
```

这就是 `P_tx = tx_gain − offset` 的来源：**offset 把 P_max（硬件绝对功率参考点）和 tx_gain 范围上限 89.75 dB 编码成一个常数**，不同频率、不同个体的差异全部体现在 offset 的取值上。

**倒推 offset 的公式推导**

将上述物理模型与第 5.3 节 PSD 换算公式联立：

```
P_tx = tx_gain − offset          ← 物理模型（上方推导）
P_tx = PSD_peak + 33             ← 5.3 节：带内总功率 = PSD 峰值 + 10·log₁₀(BW/RBW)
                                            （BW=2 MHz，RBW=1 kHz，→ 33 dB）
```

两式右边相等，消去 P_tx：

```
tx_gain − offset = PSD_peak + 33
→ offset = tx_gain − (PSD_peak + 33)
```

由此，只需一个已知增益的频谱仪读数，即可直接倒推 offset。第一台设备的标定也用的是同一逻辑（serial=193982 标定块中分两步写出：先求 P_total，再做减法），这里合并成一步公式。

从 S1–S6 各档位代入，结果完全一致（每 10 dB 增益对应 PSD 峰值精确上升 10 dB，线性度极佳）：

```
以 S1 为例：offset = 10 − (−80 + 33) = 10 + 47 = 57

以 S6 为例：offset = 60 − (−30 + 33) = 60 − 3 = 57
```

**→ P_tx ≈ (tx_gain − 57) dBm（serial=8003272，100 MHz，amplitude=1.0）**

**amplitude 修正**

上面的 offset=57 是在 **amplitude=1.0** 条件下标定的。当 amplitude 取其他值时，需要额外修正。

`amplitude` 控制的是软件送给 DAC 的数字样本幅度（0.0 ~ 1.0）。这个缩放直接乘在波形电压上，射频输出功率正比于电压的平方：

```
电压 × amplitude  →  功率 × amplitude²
→ dB 变化 = 10·log₁₀(amplitude²) = 20·log₁₀(amplitude)
```

因此完整公式为：

```
P_tx = (tx_gain − 57) + 20·log₁₀(amplitude)  dBm
```

> **常见疑问**：offset=57 是用 33 dB 换算推出来的，现在又多了 20·log₁₀(amplitude)，会不会重复计算？
>
> 不会。33 dB 是**频谱仪测量工具的修正**（RBW 窗口比信号带宽窄，读数偏低），
> 只在推导 offset 那一步用过，用完就已经编码进 57 里了，之后不会再出现。
> 20·log₁₀(amplitude) 是**基带数字信号幅度缩放的物理效果**，两者来源完全不同，互相独立。
>
> | | 33 dB | 20·log₁₀(amplitude) |
> |--|--|--|
> | 作用时机 | 标定 offset 时（一次性） | 每次计算不同 amplitude 时 |
> | 物理来源 | 频谱仪 RBW 窗口与信号带宽的差距 | DAC 数字样本幅度缩放 |
> | offset 确定后还用吗 | 不用，已编码进 offset=57 | 要用，amplitude 变了功率就变 |

> **为什么用加号而不是减号？**
>
> `20·log₁₀(amplitude)` 本身对 amplitude < 1 就是负数，符号由 log 函数自己处理，写加号是数学上最自然的形式：
>
> ```
> amplitude = 1.0  →  20·log₁₀(1.0) = 0 dB    （不变，退化为基准公式）
> amplitude = 0.5  →  20·log₁₀(0.5) = −6 dB   （加负数 = 功率降低）
> amplitude = 0.1  →  20·log₁₀(0.1) = −20 dB  （加负数 = 功率降低）
> ```
>
> amplitude=1.0 时加 0，公式自动退化为 `P_tx = tx_gain − 57`，这也是标定选 amplitude=1.0 作基准的原因——让 offset 直接等于不带任何修正的值，公式最简洁。

实测验证（S7 基准 amplitude=1.0，PSD 峰值 −25 dBm）：
- amplitude=0.5 → 20·log₁₀(0.5)=**−6 dB**，理论峰值 −25−6=**−31 dBm** ✓（S8 实测 ≈ −31 dBm）
- amplitude=0.1 → 20·log₁₀(0.1)=**−20 dB**，理论峰值 −25−20=**−45 dBm** ✓（S9 实测 ≈ −45 dBm）

### 10.3 两台设备对比

| 参数 | serial=193982 | serial=8003272 | 差值 |
|------|--------------|----------------|------|
| 100 MHz offset | **66 dB** | **57 dB** | 9 dB |
| tx_gain=50 时 P_tx | **−16 dBm** | **−7 dBm** | 9 dB 偏高 |
| tx_gain=50 时 P_rx（-1 dB 线缆） | **≈ −17 dBm** ✅ | **≈ −8 dBm** ⚠️ | — |
| 无衰减器直连安全上限 | tx_gain ≤ 57 dB，保守取 **50 dB** | tx_gain ≤ 48 dB，保守取 **45 dB** | — |

> **9 dB 差异的可能原因**：B210 个体差异（AD9361 片内 TX 链路增益分散性 + 板级阻抗匹配差异）。
> 两台设备均在 AD9361 规格范围内，属正常单元间波动。**不可互换使用 serial=193982 的 offset=66 公式给 serial=8003272 做链路预算。**

### 10.4 直连 BER 测试：TX/RX 分配建议

**结论：serial=193982 作 TX，serial=8003272 作 RX。**

**理由：**

1. **安全边际**：serial=193982（offset=66）在 tx_gain=50 时 P_rx≈−17 dBm，比 −10 dBm 安全阈值有 **7 dB** 裕量；若改用 serial=8003272（offset=57）作 TX，相同 tx_gain 下 P_rx≈−8 dBm，仅有 **2 dB** 裕量，偏保守。

2. **配置文件一致性**：现有 `configs/tx_b210_cable_loopback.yaml` 已写 `usrp_addr: "serial=193982"`，沿用不需要修改。

3. **RX 端设备选择无关安全**：AD9361 RX 绝对最大输入（+2.5 dBm）两台相同，安全判定完全由 TX 功率决定，RX 用哪台均可。

**如果必须用 serial=8003272 作 TX**，将 tx_gain 降至 **45 dB**：

```
P_tx = 45 − 57 = −12 dBm
P_rx ≈ −12 − 1 = −13 dBm（安全裕量 3 dB，可接受）
```

**推荐接线方案（无衰减器直连）：**

```
B210 (serial=193982) TX/RX 端口
         │
    0.5 m SMA 线缆（插入损耗 ≈ 1 dB）
         │
B210 (serial=8003272) RX2 端口

TX 配置（serial=193982）：tx_gain=50, amplitude=1.0  → P_rx ≈ −17 dBm ✅
RX 配置（serial=8003272）：rx_gain 建议 40–50 dB（参考 rx_cable_loopback.yaml）
```
