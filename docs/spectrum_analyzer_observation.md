# 频谱仪观察说明

当前工程可以通过 B210 发射一段缓冲回放的单星 GPS L1 C/A 扩频基带信号，并在频谱仪上观察其宽带包络。当前代码支持 `PRN1~32`，每次选择一颗星发送。

## 字段语义说明

- `带宽`
  - 这里指的是 USRP Sink 的 `Bandwidth` 参数。
  - Python 运行链路中会调用 `set_bandwidth()`，GRC 主流图中对应 `Ch0: Bandwidth (Hz)`。
  - 当前默认把 `bandwidth` 设成 `sample_rate`，这是便于实验的 v1 简化设置，不表示“理论信号占用带宽严格等于采样率”。

- `射频中心频率`
  - 指 USRP 发射本振中心频率，也就是 `center_freq`。

- `基带偏移频率`
  - spread 模式下默认为 `0`。
  - tone 模式下等于 `tone_offset_hz`。

- `信号观测频率`
  - spread 模式下等于 `center_freq`。
  - tone 模式下等于 `center_freq + tone_offset_hz`。

- `prn_id`
  - 表示当前单星发送使用的 GPS L1 C/A PRN 编号。
  - 当前支持范围为 `1~32`。
  - 可由 YAML 配置或 `scripts/run_tx.py --prn-id` 指定。

## 推荐配置

- 安全基线配置：[`configs/tx_b210.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210.yaml)
- 可见谱复现配置：[`configs/tx_b210_visible_spectrum.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml)

建议保留安全基线配置作为默认起点；当你需要复现或继续观察宽带包络时，使用可见谱配置。

当前仓库里建议把这三类信息区分开：

- `configs/tx_b210.yaml`
  - Python runtime 的默认安全基线。
- `configs/tx_b210_visible_spectrum.yaml`
  - 当前 runtime / Ubuntu bring-up 的可见谱配置。
- [`experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md`](/home/shen/projects/gnss_tx/experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md)
  - 历史实验检查点，记录的是当日 `PRN1` 实验事实，不代表当前功能边界仍限于 PRN1。

## 推荐排障顺序

如果在扩频模式下仍只能看到噪声底，先切换到单音校准模式：

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
  --config configs/tx_b210.yaml \
  --signal-mode tone \
  --tone-offset-hz 500000 \
  --duration 5
```

当 `center_freq = 100 MHz` 且 `tone_offset_hz = 500 kHz` 时，应在 `100.5 MHz` 附近寻找一根窄峰。  
如果单音可见而扩频不可见，通常说明硬件链路没有问题，剩余问题在于频谱仪显示参数或扩频信号的观察灵敏度。

## 第一次射频观察建议

1. 在频谱仪处于未知设置状态时，不要先启动发射。
2. 确认频谱仪输入阻抗为 `50 ohm`。
3. 保持前端保护：
   - 参考电平先设高一些
   - 输入衰减先打开
4. 使用同轴线将 B210 的 `TX/RX` 口连接到频谱仪。
5. 若是首次排障，优先使用安全基线配置：
   - `center_freq = 100 MHz`
   - `sample_rate = 4.092 Msps`
   - `samples_per_chip = 4`
   - `tx_gain = 0.0`
   - `amplitude = 0.25`

## 频谱仪设置建议

- 中心频率：`100 MHz`
- 首先使用较宽的 `Span`：`20 MHz` 或 `10 MHz`
- 找到信号后，再缩小到 `5 MHz`，必要时再缩到 `2 MHz`
- `RBW / VBW` 先设宽一些，看到信号后再逐步减小

## QT 频谱与频谱仪的区别

- `--qt-preview`
  - 用来观察发给 USRP 之前的软件侧预览信号。
  - 同时显示 QT 时域和 QT 频谱。
  - 适合先确认当前发射参数下，软件链路里的基带包络或单音偏移是否符合预期。

- 频谱仪
  - 用来观察真正从 B210 发射出来的射频信号。
  - 适合确认线缆、硬件链路和仪器侧实际接收到的谱形。

推荐顺序：

1. 先用 `--qt-preview` 看软件侧频谱是否合理
2. 再连接频谱仪，看真实 RF 发射结果是否一致

示例命令：

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
  --config configs/tx_b210_visible_spectrum.yaml \
  --prn-id 7 \
  --qt-preview
```

## 什么算成功

- 在 `100 MHz` 附近能看到连续存在的宽带包络
- 该包络不是单音尖峰
- 停止发射后该包络消失
- 在单音校准模式下，`100.5 MHz` 附近会出现一根窄峰，停止发射后消失

## 安全提醒

- 频谱仪最大输入：`30 dBm`
- 频谱仪最大直流：`50 V`
- 在没有外部衰减器的情况下，不要在未确认安全前继续提高 `tx_gain` 或 `amplitude`

## 实验记录与自动化

- 检查点记录：[`experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md`](/home/shen/projects/gnss_tx/experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md)
- 射频观察模板：[`experiments/templates/general/observation_log_template.md`](/home/shen/projects/gnss_tx/experiments/templates/general/observation_log_template.md)
- sweep 参数模板：[`experiments/records/2026-03-22/tx_visibility_sweep/tx_visibility_sweep_template.csv`](/home/shen/projects/gnss_tx/experiments/records/2026-03-22/tx_visibility_sweep/tx_visibility_sweep_template.csv)
- 实验当天勾选清单和实验草稿：由 `scripts/plan_tx_visibility_sweep.py` 自动生成

## 发射参数试验建议

推荐按“先基准确认，再向下缩减”的顺序试验：

1. 先用已知可见组合 `tx_gain = 10.0`、`amplitude = 0.50` 做当天基准确认
2. 固定 `amplitude = 0.50`，按顺序测试 `tx_gain = 10, 8, 6`
3. 选出最低稳定可见的 `tx_gain`
4. 固定该 `tx_gain`，按顺序测试 `amplitude = 0.50, 0.40, 0.30`
5. 对最终组合重复运行 3 次，确认宽带包络稳定且可重复

建议每组使用固定时长 `15~20 s`；当前自动生成的 sweep 清单默认按 `20 s` 生成。

每次运行 `scripts/run_tx.py` 时，终端都会额外打印一段“实验表格参数摘要”。  
这段摘要专门对应实验表格里的关键字段，例如：

- `发送信号类型`
- `prn_id`
- `采样率`
- `射频中心频率`
- `发射增益`
- `带宽`
- `serial`
- `信号观测频率`
- `基带偏移频率`
- `幅度`
- `是否归一化`
- `是否直流偏置`
- `生成方式`

`GNU Radio流图`、`GNU Radio频谱`、`频谱仪结果` 这类非自动产出的栏位，建议继续人工填写或留空。

现场记录时，建议把频谱仪判断统一成这 3 档：

- `频谱仪结果`：`明显可见 / 勉强可见 / 不可见`
- `稳定性`：`稳定 / 边缘 / 不稳定`
