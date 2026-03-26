# gnss_tx Python 包目录

这个目录是 `gnss_tx` Python 包本体。这里的模块通常不直接单独运行，而是由
`scripts/run_tx.py` 调用，或通过 GNU Radio 的自定义块间接调用。

## 包结构

```
src/gnss_tx/
├── ca/                  # C/A 码生成
├── nav/                 # 导航 bit 处理
├── signal/              # BPSK 扩频与多星叠加
├── gr/                  # GNU Radio 集成
├── usrp/                # USRP 控制与运行时配置
└── utils/               # 基础工具
```

## 子包说明

### `ca/` — C/A 码生成

- `prn_generator.py`：双 LFSR 实现，生成 GPS L1 C/A PRN1~32 码（1023 chip/ms），输出 `int8` 双极性数组（`+1/-1`）
- `resampler.py`：码重采样辅助

核心接口：
```python
from gnss_tx.ca.prn_generator import generate_ca_code
code = generate_ca_code(prn_id=1)  # int8 数组，长 1023
```

### `nav/` — 导航 bit 处理

- `nav_bits.py`：50 bps 循环导航 bit 源（`CyclicNavBitSource`）与归一化工具（`normalize_nav_bits`）
- `subframe_builder.py`：占位文件，待实现真实 GPS NAV 子帧

核心接口：
```python
from gnss_tx.nav.nav_bits import CyclicNavBitSource, normalize_nav_bits
src = CyclicNavBitSource([1, 0, 1, 1, 0])
bit = src.bit_at(index=0)  # 返回 +1 或 -1
```

### `signal/` — BPSK 扩频与多星叠加

- `spreader.py`：有状态 BPSK 扩频生成器（`GpsL1CaBpskGenerator`），维护码相位、导航 bit、采样相位三个时间尺度，`generate_samples(count)` 按需生成 complex64 样本
- `multi_sat_combiner.py`：多星叠加合成，线性叠加 N 颗 PRN，除以 √N 功率归一化，预生成完整导航周期回放缓冲区
- `iq_builder.py`：单音与复基带转换辅助
- `modulator.py`：chip → complex baseband 映射

核心接口：
```python
from gnss_tx.signal.spreader import GpsL1CaBpskGenerator
gen = GpsL1CaBpskGenerator(prn_id=1, samples_per_chip=4)
samples = gen.generate_samples(count=4092)  # complex64

from gnss_tx.signal.multi_sat_combiner import build_multi_sat_replay_samples
buf = build_multi_sat_replay_samples(samples_per_chip=4)  # 32颗PRN叠加
```

### `gr/` — GNU Radio 集成

- `top_block.py`：`GpsL1CaTxTopBlock`，组装 GNU Radio 流图（`vector_source_c` 缓冲回放 + `multiply_const_cc` 幅度缩放 + `uhd.usrp_sink` 发射），可选 QT 时域/频域预览

### `usrp/` — USRP 控制与运行时配置

- `tx_controller.py`：`TxRuntimeConfig`（不可变 dataclass），负责 YAML 加载、参数校验、采样率联动计算（`sample_rate = 1.023 MHz × samples_per_chip`）、CLI 覆盖、实验报告生成
- `b210_sink.py`：创建 UHD USRP sink，读回实际采样率

核心接口：
```python
from gnss_tx.usrp.tx_controller import TxRuntimeConfig, load_tx_runtime_config
config = load_tx_runtime_config("configs/tx_b210_visible_spectrum.yaml")
```

### `utils/` — 基础工具

- `io.py`：YAML 文件加载（`load_yaml_file`）
- `timebase.py`：占位文件，待实现时基管理
- `logging.py`：占位文件，待实现日志模块

## 如何间接运行这些模块

通过 CLI 入口调用整套包：

```bash
cd ~/projects/gnss_tx

# 干运行（不启动硬件）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run

# 单星发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml --duration 30

# 多星发射
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_all32prn.yaml --duration 60
```

## 开发时的快速验证

修改 `src/gnss_tx/` 下的代码后，建议先跑测试：

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
