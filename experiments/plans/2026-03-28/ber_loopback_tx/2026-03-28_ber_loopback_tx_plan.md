# 发射端实验计划：闭环 BER 验证（发端视角）

> 创建时间：2026-03-27
> 2026-03-28 更新：已按 `tx_power_test` 实测结果修正为今日执行基线
> 对应接收端计划：`/home/shen/projects/GNSS_RX/experiments/plans/2026-03-27/ber_loopback_rx/2026-03-27_ber_loopback_rx_plan.md`
> 状态：`[~]` 配置与步骤已对齐，待执行硬件闭环
> 里程碑目标：Milestone 1 — 射频线直连闭环 BER 验证

---

## 一、当前结论

`tx_power_test` 已完成，今天的发端侧不再重复功率摸底。后续所有 BER 相关实验统一采用以下安全基线：

| 项目 | 固定值 | 说明 |
|------|--------|------|
| TX 设备 | `serial=193982` | 2026-03-27 实测表明该机在 100 MHz 的输出比另一台低约 9 dB，更适合作 TX |
| 中心频率 | `100 MHz` | 继续沿用当前调试频点 |
| `tx_gain` | `50 dB` | 无衰减器射频线直连推荐值 |
| `amplitude` | `1.0` | 满幅发射，避免额外数字动态范围损失 |
| `nav_pattern` | `"1 0 1 1 0 0 1 0"` | 与收端 BER 参考序列一致 |
| 连接方式 | `B210 TX(TX/RX) -> 同轴线 -> B210 RX(RX2)` | 本计划默认无衰减器直连 |

**结论：发端无需修改代码，统一使用 `configs/tx_b210_cable_loopback.yaml` 即可。**

---

## 二、已知 bit 序列说明

当前 `DEFAULT_NAV_PATTERN` 定义在 `src/gnss_tx/nav/nav_bits.py`：

```python
DEFAULT_NAV_PATTERN = (1, -1, 1, 1, -1, -1, 1, -1)
```

换算为 0/1 表示：`1, 0, 1, 1, 0, 0, 1, 0`

- 循环周期：8 bit
- 导航速率：50 bps
- 每个 bit 时长：20 ms
- 一个完整循环时长：160 ms
- 今日正式 BER 目标：采集 250 s，约 12,500 bit

---

## 三、安全边界

### 3.1 今日默认安全公式

根据 `2026-03-27/tx_power_test/tx_power_test.md` 的 100 MHz 实测结果：

```text
P_tx(total) ≈ tx_gain - 66 dBm
P_rx ≈ tx_gain - 67 dBm    （按 1 dB 线缆损耗估算）
```

代入今日默认值 `tx_gain=50`：

```text
P_tx ≈ -16 dBm
P_rx ≈ -17 dBm
```

这比保守安全阈值 `-10 dBm` 低约 7 dB，满足无衰减器直连要求。

### 3.2 明确禁止项

- 禁止沿用旧公式 `tx_gain - 79.75 dBm` 来估算 100 MHz 输出功率
- 禁止在无衰减器直连时把 `tx_gain` 提到 `60 dB` 及以上
- 禁止把 `serial=8003272` 按 `serial=193982` 的公式直接复用为 TX

---

## 四、今日执行步骤

### Step 0：配置核对

确认 `configs/tx_b210_cable_loopback.yaml` 满足以下参数：

- `usrp_addr: "serial=193982"`
- `center_freq: 100000000.0`
- `tx_gain: 50.0`
- `amplitude: 1.0`
- `nav_pattern: "1 0 1 1 0 0 1 0"`

### Step 1：干运行检查

```bash
cd /home/shen/projects/gnss_tx
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --dry-run
```

完成标志：
- [ ] 参数摘要正确
- [ ] 设备序列号与今日基线一致
- [ ] `nav_pattern` 与收端参考序列一致

### Step 2：30 秒短时闭环验证

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --duration 60
```

收端在 TX 启动后约 3 秒内开始 30 秒采集，用于阶段 1 链路验证。

完成标志：
- [ ] TX 运行正常
- [ ] 无持续 underflow（`U`）报警
- [ ] 收端成功完成短时采集

### Step 3：250 秒正式 BER 采集

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --duration 300
```

收端执行 250 秒正式采集，目标恢复比特数 `>= 10^4`。

完成标志：
- [ ] TX 持续运行覆盖收端整段采集窗口
- [ ] 记录实际发射时长
- [ ] 记录实际使用配置与是否出现 underflow

---

## 五、发端需回填给收端的记录

实验完成后，将以下字段回填到收端实验记录：

- `usrp_addr / serial`
- `center_freq`
- `tx_gain`
- `amplitude`
- `nav_pattern`
- 实际 TX 启动和结束时间
- 是否出现 underflow

---

## 六、附：今日默认启动命令

```bash
# 干运行
cd /home/shen/projects/gnss_tx
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --dry-run

# 正式发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --duration 300
```
