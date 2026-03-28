# 发射端实验计划：闭环 BER 验证（发端视角）

> 创建时间：2026-03-27
> 2026-03-28 更新：已按 `tx_power_test` 结果修正执行基线，并补入 truth JSON 导出流程
> 对应接收端计划：`/home/shen/projects/GNSS_RX/experiments/plans/2026-03-28/ber_loopback_rx/2026-03-28_ber_loopback_rx_plan.md`
> 状态：`[~]` truth 导出与发射基线已实现，待配合 RX tracked BER 做 30 s / 250 s / 1 h 验证
> 里程碑目标：Milestone 1 — 射频线直连闭环 BER 验证

---

## 一、当前发端职责

TX 当前不再是主矛盾。发端侧的任务已经收敛到三件事：

1. 保持 `configs/tx_b210_cable_loopback.yaml` 的稳定发射基线。
2. 在每轮 BER 实验前导出 truth JSON，作为 RX 的参考真值契约。
3. 为 30 s、250 s 和 1 h 提供稳定的发射覆盖窗口。

当前不建议再在 TX 端继续改导航生成逻辑。

---

## 二、当前稳定基线

| 项目 | 当前基线 | 说明 |
|------|----------|------|
| TX 设备 | `serial=193982` | 当前固定 TX |
| 中心频率 | `100 MHz` | 与 RX 对齐 |
| `tx_gain` | `40 dB` 先试，必要时升到 `45/50 dB` | `50 dB` 为当前安全上限内正式基线 |
| `amplitude` | `1.0` | 满幅发射 |
| `nav_pattern` | `"1 0 1 1 0 0 1 0"` | truth JSON 与 RX 均以此为准 |
| 连接方式 | `B210 TX(TX/RX) -> 同轴线 -> B210 RX(RX2)` | 当前默认无衰减器直连 |

---

## 三、已知 bit 真值与 truth JSON

当前 `DEFAULT_NAV_PATTERN` 定义在 `src/gnss_tx/nav/nav_bits.py`：

```python
DEFAULT_NAV_PATTERN = (1, -1, 1, 1, -1, -1, 1, -1)
```

对应 0/1 表示：

```text
1 0 1 1 0 0 1 0
```

### 3.1 truth JSON 导出

当前 TX 已支持通过 `run_tx.py` 直接导出供 RX 使用的 truth JSON，字段包括：

- `nav_bits_pattern_pm1`
- `nav_bits_pattern_01`
- `initial_code_phase`
- `initial_nav_epoch`
- `initial_nav_bit_index`
- `samples_per_chip`
- `sample_rate`
- `epochs_per_bit`
- `prn_id`

推荐命令：

```bash
cd /home/shen/projects/gnss_tx
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --dry-run \
    --export-truth-json /mnt/hgfs/GongXiangDocument/GNSS_RX_matlab/tx_truth.json
```

完成标志：

- [ ] dry-run 输出参数正确
- [ ] `tx_truth.json` 已导出到宿主机共享目录
- [ ] truth JSON 内容与 dry-run 摘要一致

---

## 四、安全边界

根据 `tx_power_test` 的 100 MHz 实测结果，当前继续使用：

```text
P_tx(total) ≈ tx_gain - 66 dBm
P_rx ≈ tx_gain - 67 dBm
```

常用档位估算：

```text
tx_gain=40 -> P_rx ≈ -27 dBm
tx_gain=45 -> P_rx ≈ -22 dBm
tx_gain=50 -> P_rx ≈ -17 dBm
```

结论：

- `40 dB`：当前优先试探档
- `45 dB`：中间过渡档
- `50 dB`：当前正式兜底档

禁止项：

- [ ] 无衰减器直连时把 `tx_gain` 拉到 `60 dB` 及以上
- [ ] 在 BER 尚未收敛时频繁改 `nav_pattern`
- [ ] 在没有重新导出 truth JSON 的情况下改初始 bit/epoch 偏移

---

## 五、推荐执行顺序

### Step 0：干运行 + 导出 truth

```bash
cd /home/shen/projects/gnss_tx
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --dry-run \
    --export-truth-json /mnt/hgfs/GongXiangDocument/GNSS_RX_matlab/tx_truth.json
```

### Step 1：30 s 配合实验

```bash
cd /home/shen/projects/gnss_tx
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --duration 60
```

目标：

- [ ] 覆盖 RX 的 30 s 回归窗口
- [ ] 无持续 underflow

### Step 2：250 s 配合实验

```bash
cd /home/shen/projects/gnss_tx
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --duration 300
```

目标：

- [ ] 覆盖 RX 的 250 s 采集窗口
- [ ] 记录本轮实际使用的 `tx_gain`

### Step 3：1 h 配合实验

1 h 阶段默认继续保持 TX 配置不变，重点是配合 RX 的两类采集方式：

- `chunked IQ`
- `Full 1h Raw IQ`

每次长时实验开始前，都建议重新执行一次 truth JSON 导出。

---

## 六、需要回填给 RX 的字段

实验后回填：

- `usrp_addr / serial`
- `center_freq`
- `tx_gain`
- `amplitude`
- `nav_pattern`
- `initial_nav_bit_index`
- `initial_nav_epoch`
- truth JSON 路径
- 是否出现 underflow

---

## 七、当前默认命令

```bash
# 干运行 + 导出 truth
cd /home/shen/projects/gnss_tx
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --dry-run \
    --export-truth-json /mnt/hgfs/GongXiangDocument/GNSS_RX_matlab/tx_truth.json

# 30 s 配合发射
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --duration 60

# 250 s 配合发射
env PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 40 \
    --amplitude 1.0 \
    --duration 300
```
