# gnss_tx 测试目录

本目录存放 gnss_tx 的 Python 单元测试。修改 `src/` 或 `scripts/` 后，建议至少跑一遍这里的测试。

---

## 一次跑完整套测试

```bash
cd ~/projects/gnss_tx
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

---

## 按文件运行

```bash
cd ~/projects/gnss_tx

PYTHONPATH=src python3 -m unittest tests.test_ca_prn -v
PYTHONPATH=src python3 -m unittest tests.test_spreader -v
PYTHONPATH=src python3 -m unittest tests.test_nav_bits -v
PYTHONPATH=src python3 -m unittest tests.test_multi_sat_combiner -v
PYTHONPATH=src python3 -m unittest tests.test_tx_controller -v
PYTHONPATH=src python3 -m unittest tests.test_run_tx -v
PYTHONPATH=src python3 -m unittest tests.test_gr_block -v
PYTHONPATH=src python3 -m unittest tests.test_sweep_planner -v
PYTHONPATH=src python3 -m unittest tests.test_tx_profiles -v
```

---

## 测试覆盖范围

| 测试文件 | 覆盖范围 |
|----------|----------|
| `test_ca_prn.py` | C/A 码生成正确性（PRN1~32 LFSR 实现、1023 chip 长度、双极性输出） |
| `test_spreader.py` | BPSK 有状态生成器（码相位/导航bit/采样相位三个时间尺度、跨边界连续性） |
| `test_nav_bits.py` | 导航 bit 归一化（1/0 → +1/-1）与循环无限访问 |
| `test_multi_sat_combiner.py` | 多星叠加：单星等效、32星功率归一化（约1.0）、峰值幅度约束（< 2.0） |
| `test_tx_controller.py` | 运行时配置加载、参数校验、采样率联动（1.023 MHz × samples_per_chip）、实验报告格式 |
| `test_run_tx.py` | `run_tx.py` CLI 参数解析与 dry-run 行为 |
| `test_gr_block.py` | GNU Radio TopBlock 组装（需 gnuradio 可导入，否则跳过） |
| `test_sweep_planner.py` | 参数扫描规划：CSV / Markdown 清单生成 |
| `test_tx_profiles.py` | 配置文件加载与字段合法性（`tx_b210.yaml`、`tx_b210_visible_spectrum.yaml`、`tx_b210_all32prn.yaml`、`tx_b210_sn8003272.yaml`） |

---

## 何时跑测试

- 改了 `src/gnss_tx/ca/`（C/A 码生成、重采样）
- 改了 `src/gnss_tx/signal/`（BPSK 扩频、多星叠加）
- 改了 `src/gnss_tx/nav/`（导航 bit 归一化）
- 改了 `src/gnss_tx/usrp/tx_controller.py`（配置加载、校验）
- 改了 `scripts/run_tx.py`（CLI 行为）
- 改了 `configs/*.yaml`（配置字段）
- 提交前快速确认无回归
