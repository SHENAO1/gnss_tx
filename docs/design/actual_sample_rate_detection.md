# 实际采样率检测机制说明

## 概述

GNSS TX 发端在启动后会自动检测并显示 USRP 硬件的**实际采样率**，与软件配置中的**请求采样率**进行对比，帮助确认硬件设置是否正确、并量化时钟分频带来的舍入偏差。

---

## 背景：请求采样率 vs 实际采样率

软件向 USRP 设备请求某个采样率（例如 4,092,000 Sps），但 USRP 内部使用**整数分频器**从参考时钟（通常为 200 MHz）派生实际采样率。整数约束导致实际采样率可能与请求值存在微小偏差（通常 < 0.01%）。

```
请求值 = GPS_CA_CHIP_RATE × samples_per_chip
       = 1.023 MHz × 4
       = 4,092,000 Sps

实际值 = USRP 参考时钟 / 整数分频系数
       ≈ 4,092,000 Sps（含微小舍入误差）
```

---

## 实现位置

| 层次 | 文件 | 行号 | 功能 |
|------|------|------|------|
| 硬件初始化 | [src/gnss_tx/usrp/b210_sink.py](../../src/gnss_tx/usrp/b210_sink.py) | 48 | 向 USRP 写入请求采样率 |
| 采样率读取 | [src/gnss_tx/usrp/tx_controller.py](../../src/gnss_tx/usrp/tx_controller.py) | 643–675 | `read_uhd_sink_sample_rate()` |
| 报告格式化 | [src/gnss_tx/usrp/tx_controller.py](../../src/gnss_tx/usrp/tx_controller.py) | 678–736 | `format_uhd_tx_sample_rate_report()` |
| Python 入口调用 | [scripts/run_tx.py](../../scripts/run_tx.py) | 119 | 启动后立即打印报告 |
| GRC 块调用 | [grc/blocks/gnss_tx_usrp_sink.block.yml](../../grc/blocks/gnss_tx_usrp_sink.block.yml) | 72 | 块初始化时打印报告 |

---

## 检测流程

> 流程图详见：[actual_sample_rate_detection.drawio](actual_sample_rate_detection.drawio)

```
tb.start()                              # GNU Radio 流图启动，USRP 开始工作
    │
    └─ format_uhd_tx_sample_rate_report(config.sample_rate, tb.sink_block)
           │
           ├─ 记录请求采样率（来自软件配置）
           │
           └─ read_uhd_sink_sample_rate(sink)
                  │
                  └─ sink.get_samp_rate()   ← GNU Radio UHD 接口
                         │
                         └─ UHD 驱动向 USRP 固件查询实际执行的采样率
```

### 第一步：设置采样率（`b210_sink.py:48`）

```python
sink.set_samp_rate(float(config.sample_rate))
```

创建 `uhd.usrp_sink` 后，立即将请求采样率写入 USRP。UHD 驱动在内部寻找最接近的整数分频系数并应用。

### 第二步：读取实际采样率（`tx_controller.py:643`）

```python
def read_uhd_sink_sample_rate(sink) -> float | None:
    if sink is None:
        return None
    getter = getattr(sink, "get_samp_rate", None)
    if getter is None:
        return None
    try:
        return float(getter())
    except (RuntimeError, TypeError, ValueError):
        return None
```

流图启动（`tb.start()`）后，调用 `sink.get_samp_rate()` 从 UHD 驱动回读硬件实际执行的采样率。使用 `getattr` 做防御性检查，避免在不支持该接口的设备上崩溃。

> **为什么必须在 `tb.start()` 之后读取？**
> GNU Radio 流图启动前，USRP 硬件尚未完成时钟锁定和分频器配置，`get_samp_rate()` 返回的可能是不准确的初始值。

### 第三步：生成对比报告（`tx_controller.py:678`）

```python
def format_uhd_tx_sample_rate_report(requested_sample_rate, sink, *, label):
    requested = float(requested_sample_rate)
    actual = read_uhd_sink_sample_rate(sink)

    # 计算偏差
    delta = actual - requested
    delta_ratio = delta / requested

    # 格式化输出
    lines = [
        f"[INFO] {label} requested sample rate : {requested:.3f} Sps",
        f"[INFO] {label} requested samples/chip: {requested / GPS_CA_CHIP_RATE:.6f}",
        f"[INFO] {label} actual sample rate    : {actual:.3f} Sps",
        f"[INFO] {label} actual samples/chip   : {actual / GPS_CA_CHIP_RATE:.6f}",
        f"[INFO] {label} sample-rate delta     : {delta:+.3f} Sps ({delta_ratio:+.6%})",
    ]
```

---

## 输出示例

启动发端后，终端会打印如下报告：

```
[INFO] Python TX runtime requested sample rate : 4092000.000 Sps (4.092000 Msps)
[INFO] Python TX runtime requested samples/chip: 4.000000
[INFO] Python TX runtime actual sample rate    : 4092100.000 Sps (4.092100 Msps)
[INFO] Python TX runtime actual samples/chip   : 4.000098
[INFO] Python TX runtime sample-rate delta     : +100.000 Sps (+0.002441%)
```

若无法读取实际采样率（如设备不支持），则输出警告：

```
[INFO] Python TX runtime requested sample rate : 4092000.000 Sps (4.092000 Msps)
[INFO] Python TX runtime requested samples/chip: 4.000000
[WARN] Python TX runtime actual sample-rate readback is unavailable.
```

---

## 两种使用场景

### 场景 1：Python 脚本运行（`run_tx.py`）

```python
tb.start()
print(format_uhd_tx_sample_rate_report(
    config.sample_rate,
    tb.sink_block,
    label="Python TX runtime"
))
```

报告打印到标准输出（终端）。

### 场景 2：GNU Radio Companion（GRC）运行

在自定义块 `gnss_tx_usrp_sink.block.yml` 的 `make` 脚本中，块初始化完成后自动调用相同的报告函数，输出到 GRC 的 Console 面板。

---

## 采样率数值的来源与约束

采样率在配置加载时自动派生或验证（`tx_controller.py:210`）：

```python
# 扩频模式：采样率必须严格等于 chip_rate × samples_per_chip
if signal_mode == "spread":
    derived_rate = GPS_CA_CHIP_RATE * samples_per_chip  # = 1.023e6 × N
    assert abs(sample_rate - derived_rate) < 1e-3
```

配置文件中可直接指定 `samples_per_chip`，软件自动计算 `sample_rate`：

```yaml
samples_per_chip: 4
# 自动派生：sample_rate = 1.023e6 × 4 = 4,092,000 Sps
```

---

## GRC 窗口中的采样率标签说明

GRC 流图界面左下角有一个"TX 采样率（配置值）Msps"标签（`gnss_tx_main.grc`），该标签显示的是**配置的请求值**，不是硬件实际值。硬件实际采样率只能通过终端或 GRC Console 的文字报告查看。
