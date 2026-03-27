# experiments 目录说明

本目录用于记录 `GPS L1 C/A` 发射端实验，并统一按“类别 / 日期 / 主题”归档，避免实验文档继续散落在根目录。

## 目录结构

- `records/YYYY-MM-DD/<topic>/`
  - 实验事实、草稿、归档、执行清单和同主题 CSV。
- `plans/YYYY-MM-DD/<topic>/`
  - 计划类文档，按日期和主题收纳。
- `templates/general/`
  - 可复用的通用模板。

## 当前目录索引

| 路径 | 类型 | 描述 |
|------|------|------|
| `records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md` | checkpoint | PRN1 可见谱历史检查点 |
| `records/2026-03-22/tx_visibility_sweep/2026-03-22_tx_visibility_sweep_draft.md` | draft | 2026-03-22 参数扫描草稿 |
| `records/2026-03-22/tx_visibility_sweep/2026-03-22_task_archive.md` | archive | 2026-03-22 任务归档 |
| `records/2026-03-22/tx_visibility_sweep/tx_visibility_sweep_checklist.md` | checklist | 参数扫描执行清单 |
| `records/2026-03-22/tx_visibility_sweep/tx_visibility_sweep_template.csv` | csv | 参数扫描模板 |
| `records/2026-03-24/dual_usrp_loopback/2026-03-24_dual_usrp_loopback_procedure.md` | procedure | 双 USRP OTA/loopback 操作流程 |
| `templates/general/observation_log_template.md` | template | 通用射频观察记录模板 |
| `plans/2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md` | plan | TX/RX 综合改进路线图 |
| `plans/2026-03-27/ber_loopback_tx/2026-03-27_ber_loopback_tx_plan.md` | plan | 发射端闭环 BER 验证计划 |
| `plans/2026-03-27/tx_power_test/tx_power_test.md` | plan | 发射功率测试与参数确认 |
| `plans/INDEX.md` | index | 计划索引与跨项目入口 |

## 推荐实验流程

1. 先运行 [run_tx.py](/home/shen/projects/gnss_tx/scripts/run_tx.py) 的 `--dry-run`
   - 确认配置装载、实验摘要和设备发现输出合理。
2. 再看软件侧预览
   - Python runtime 适合正式参数化运行和 `--qt-preview`。
   - GRC 适合 Ubuntu 虚拟机里快速 bring-up。
3. 再接频谱仪做 RF 观察
   - 先确认线缆、保护、参考电平和衰减设置。
4. 实验结束后回填文档
   - 历史事实写入 `records/`
   - 后续动作和路线图写入 `plans/`

## Ubuntu 命令行快速入口

```bash
cd ~/projects/gnss_tx
source .venv/bin/activate

# 1) 检查 Python 环境和项目结构
PYTHONPATH=src python3 scripts/quick_check.py

# 2) 先做 dry-run，确认配置、UHD 设备发现和实验摘要
PYTHONPATH=src python3 scripts/run_tx.py \
    --dry-run \
    --config configs/tx_b210.yaml

# 3) 启动当前可见谱扩频发射组合
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30

# 4) 打开 GNU Radio Companion 主流图
bash scripts/run_gnss_tx_grc.sh

# 5) 生成当天参数扫描文档
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py
```

## Python runtime 与 GRC 的分工

- Python runtime
  - 适合 dry-run、正式实验、命令行参数覆盖、终端摘要输出和脚本化扫描。
  - 权威入口是 [scripts/run_tx.py](/home/shen/projects/gnss_tx/scripts/run_tx.py)。
- GNU Radio Companion
  - 适合 Ubuntu 虚拟机里直接点击运行、查看 QT 时域与频域预览、做教学演示和快速 bring-up。
  - Companion 主流图是 [flowgraphs/gnss_tx_main.grc](/home/shen/projects/gnss_tx/flowgraphs/gnss_tx_main.grc)。
  - Companion 是 Python runtime 的镜像入口，不是新的配置真源。

## 跨项目计划参考

| 计划 | 本项目（TX） | 对应项目（RX） |
|------|------------|---------------|
| BER 闭环验证 | `plans/2026-03-27/ber_loopback_tx/2026-03-27_ber_loopback_tx_plan.md` | `GNSS_RX/experiments/plans/2026-03-27/ber_loopback_rx/2026-03-27_ber_loopback_rx_plan.md` |
| TX/RX 综合改进路线图 | `plans/2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md` | `GNSS_RX/experiments/plans/2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md` |

## 安全基线、当前可见谱配置与历史检查点

- 安全基线
  - 配置文件：[tx_b210.yaml](/home/shen/projects/gnss_tx/configs/tx_b210.yaml)
  - 作用：首次低功率 bring-up 和低风险链路确认。
- 当前可见谱配置
  - 配置文件：[tx_b210_visible_spectrum.yaml](/home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml)
  - 作用：当前 runtime 配置里的持续扩频观察组合。
- 历史检查点
  - 文件：[2026-03-22_prn1_visible_spectrum_checkpoint.md](/home/shen/projects/gnss_tx/experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md)
  - 作用：保留当天“PRN1 在频谱仪上可见宽带包络”的实验事实。

不要把这三者混成同一层语义：

- 配置文件描述“当前推荐入口”。
- checkpoint 描述“历史实验事实”。

## 人工维护与脚本生成

- 主要人工维护
  - `records/` 下的 checkpoint、archive、procedure
  - `templates/general/observation_log_template.md`
- 主要由脚本生成或脚本辅助生成
  - 当天 `records/YYYY-MM-DD/tx_visibility_sweep/` 下的 checklist、CSV、draft
  - 生成脚本是 [plan_tx_visibility_sweep.py](/home/shen/projects/gnss_tx/scripts/plan_tx_visibility_sweep.py)

## 每次实验结束后建议回写的内容

- 使用了哪个配置文件和哪些关键参数。
- 使用的 `prn_id` 是多少。
- 发射期间是否稳定看到宽带包络。
- 停止发射后是否消失。
- 是否保存截图，截图文件名是什么。
- 该组合属于安全起点、当前可见谱配置还是历史可见谱事实。
