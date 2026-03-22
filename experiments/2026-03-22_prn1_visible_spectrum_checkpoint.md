# PRN1 可见频谱检查点

- 实验日期：`2026-03-22`
- 信号模式：`spread`
- 结果结论：`在频谱仪上已观察到可见的 PRN1 宽带包络`

## 发射配置

- 配置文件：[`configs/tx_b210_visible_spectrum.yaml`](/home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml)
- `center_freq = 100 MHz`
- `sample_rate = 4.092 Msps`
- `samples_per_chip = 4`
- `tx_gain = 10.0`
- `amplitude = 0.5`
- `antenna = TX/RX`

## 频谱仪设置

- `Center = 100 MHz`
- `Span = 5 MHz`
- `RBW = 1 kHz`
- `VBW = 1 kHz`
- `Att = 10 dB`
- `Ref Level = -66 dBm`

## 观察结果

- 在 `100 MHz` 附近能够看到稳定的宽带包络
- 结果说明 `B210 -> 同轴线 -> 频谱仪` 这条射频链路已经打通
- 当前配置可作为后续参数扫描之前的“可复现检查点”

## 截图记录

- 本次实验已拍摄频谱仪截图
- 建议本地截图文件名：`results/figs/2026-03-22_prn1_visible_spectrum.png`

## 下一步扫描建议

- 先做当天基准确认：`tx_gain = 10`、`amplitude = 0.50`
- 对 `tx_gain` 扫描：`10 -> 8 -> 6`
- 对 `amplitude` 扫描：`0.50 -> 0.40 -> 0.30`
- 单次发射时长建议：`20 s`
- 其余条件保持不变：
  - `center_freq`
  - `sample_rate`
  - 同一根线缆
  - 同一台频谱仪
  - 同一组 `Span / RBW / VBW / Att / Ref Level`
