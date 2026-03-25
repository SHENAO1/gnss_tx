# experiments 目录说明

本目录用于记录 `PRN1 GPS L1 C/A` 扩频发送实验，不作为泛化的临时文档堆放区。

## 文件类型说明

- `YYYY-MM-DD_*checkpoint*.md`
  - 阶段性实验检查点，记录“某个配置已经被验证通过”的事实。
- `YYYY-MM-DD_*draft*.md`
  - 当天实验草稿，记录计划、待测组合和待回填字段。
- `YYYY-MM-DD_*archive*.md`
  - 当天任务归档，记录做了什么、结论是什么、后续待办是什么。
- `*_checklist.md`
  - 现场执行清单，避免漏步骤和漏记录。
- `observation_log_template.md`
  - 通用人工观察模板。
- `*.csv`
  - 扫描模板或实验表格数据。

## 推荐实验流程

1. 先运行 [run_tx.py](/home/shen/projects/gnss_tx/scripts/run_tx.py) 的 `--dry-run`
   - 先确认配置装载、实验摘要和设备发现输出是否合理。
2. 先做软件侧预览
   - Python runtime：适合正式参数化运行和 `--qt-preview`。
   - GNU Radio Companion：适合 Ubuntu 虚拟机内直接点开 [gnss_tx_main.grc](/home/shen/projects/gnss_tx/flowgraphs/gnss_tx_main.grc) 做快速 bring-up。
3. 再接频谱仪做 RF 观察
   - 先确认线缆、保护、参考电平和衰减设置。
4. 实验结束后回填记录
   - 把已验证组合写入 checkpoint。
   - 把当天过程和结论写入 archive。
   - 把扫描过程补到 draft、checklist 和 CSV。

## Ubuntu 命令行快速入口

以下命令可直接在 Ubuntu 终端执行，建议都在项目根目录下运行：

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

# 5) 生成参数扫描实验清单和 CSV
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py
```

如果当前终端还没有激活虚拟环境，先执行：

```bash
cd ~/projects/gnss_tx
source .venv/bin/activate
```

## Python runtime 与 GRC 的分工

- Python runtime
  - 适合 dry-run、正式实验、命令行参数覆盖、终端摘要输出和脚本化扫描。
  - 权威入口是 [scripts/run_tx.py](/home/shen/projects/gnss_tx/scripts/run_tx.py)。
- GNU Radio Companion
  - 适合 Ubuntu 虚拟机里直接点击运行、查看 QT 时域与频域预览、做教学演示和快速 bring-up。
  - Companion 主流图是 [flowgraphs/gnss_tx_main.grc](/home/shen/projects/gnss_tx/flowgraphs/gnss_tx_main.grc)。
  - Companion 是 Python runtime 的镜像入口，不是新的配置真源。

## 安全基线、当前可见谱配置与历史检查点

- 安全基线
  - 配置文件：[configs/tx_b210.yaml](/home/shen/projects/gnss_tx/configs/tx_b210.yaml)
  - 作用：首次低功率 bring-up 和低风险链路确认。
- 当前可见谱配置
  - 配置文件：[configs/tx_b210_visible_spectrum.yaml](/home/shen/projects/gnss_tx/configs/tx_b210_visible_spectrum.yaml)
  - 作用：当前 runtime 配置里的持续扩频观察组合。
- 历史检查点
  - 文件：[2026-03-22_prn1_visible_spectrum_checkpoint.md](/home/shen/projects/gnss_tx/experiments/2026-03-22_prn1_visible_spectrum_checkpoint.md)
  - 作用：保留当天“频谱仪上可见宽带包络”的实验事实。

不要把这三者混成同一层语义：

- 配置文件描述“当前推荐入口”。
- checkpoint 描述“历史实验事实”。

## 人工维护与脚本生成

- 主要人工维护
  - checkpoint
  - archive
  - `observation_log_template.md`
- 主要由脚本生成或脚本辅助生成
  - `tx_visibility_sweep_checklist.md`
  - `tx_visibility_sweep_template.csv`
  - 日期化的 sweep draft
  - 生成脚本是 [scripts/plan_tx_visibility_sweep.py](/home/shen/projects/gnss_tx/scripts/plan_tx_visibility_sweep.py)

## 命名约定

- 日期前缀文件表示阶段性实验记录，例如 `2026-03-22_*`。
- `checkpoint` 表示“已经确认的事实”。
- `draft` 表示“正在执行或待回填的实验草稿”。
- `archive` 表示“当天工作的归档总结”。

## 每次实验结束后建议回写的内容

- 使用了哪个配置文件和哪些关键参数。
- 发射期间是否稳定看到宽带包络。
- 停止发射后是否消失。
- 是否保存截图，截图文件名是什么。
- 该组合属于安全起点、当前可见谱配置还是历史可见谱事实。
