# 2026-03-22 今日任务归档

## 今日目标

- 完成 PRN1 扩频信号的可见频谱验证
- 打通 `run_tx.py -> GNU Radio -> B210 -> 频谱仪` 的观测链路
- 增加软件侧 QT 预览，便于同时观察 GNU Radio 频谱与频谱仪结果
- 形成一套“稳定频谱优先”的测量与记录流程

## 今日完成内容

### 1. 频谱可见性检查点

- 已确认在频谱仪上可以看到 `PRN1` 的宽带包络
- 当前可见谱复现配置：
  - 配置文件：[`configs/tx_b210_visible_spectrum.yaml`](../configs/tx_b210_visible_spectrum.yaml)
  - `center_freq = 100 MHz`
  - `sample_rate = 4.092 Msps`
  - `samples_per_chip = 4`
  - `tx_gain = 10.0`
  - `amplitude = 0.5`
  - `antenna = TX/RX`

### 2. 运行时链路增强

- `run_tx.py` 增加了 `--qt-preview`
- 运行时摘要明确区分：
  - `射频中心频率`
  - `信号观测频率`
  - `基带偏移频率`
- `bandwidth` 明确对应 USRP Sink 的 `Bandwidth` 参数

### 3. 测量流程固化

- 已形成“先基准确认、再向下缩减”的测量方法
- 当前推荐顺序：
  1. 基准确认：`tx_gain=10`、`amplitude=0.50`
  2. 第一轮：固定 `amplitude=0.50`，测试 `tx_gain=10 -> 8 -> 6`
  3. 第二轮：固定最小稳定 `tx_gain`，测试 `amplitude=0.50 -> 0.40 -> 0.30`
  4. 第三轮：最终组合重复验证 `3` 次
- 当前推荐单次发射时长：
  - `20 s`

### 4. 文档与模板

- 已更新频谱仪说明文档
- 已生成新的测量草稿、勾选清单和 CSV 模板
- 记录字段增加：
  - `频谱仪结果`：`明显可见 / 勉强可见 / 不可见`
  - `稳定性`：`稳定 / 边缘 / 不稳定`

## 当前推荐命令

### 基准确认

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
  --config configs/tx_b210_visible_spectrum.yaml \
  --tx-gain 10 \
  --amplitude 0.50 \
  --qt-preview \
  --duration 20
```

### 连续发射并同时观察 QT 频谱

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
  --config configs/tx_b210_visible_spectrum.yaml \
  --qt-preview
```

## 今日结论

- 这套链路已经具备后续做“稳定频谱参数选型”的条件
- 当前更重要的是找到“最低稳定可见”的组合，而不是继续追求更高功率
- `10 / 0.50` 适合作为当天基准点，但不应默认视为最终长期参数

## 后续待办

- 完成一轮稳定频谱参数扫描并填写模板
- 记录主瓣带宽测量结果
- 选出最低稳定可见组合和最稳定组合
- 视结果决定是否更新可见谱配置
