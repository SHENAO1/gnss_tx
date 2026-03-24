# gnss_tx

基于 Ubuntu + Python + GNU Radio + USRP B210 的 GNSS 发射工程。

## 工程目标
- 生成 GNSS 基带信号
- 支持导航电文生成与 C/A 码扩频
- 通过 GNU Radio / USRP B210 完成发射
- 在实验中记录频谱、参数与观测结果
- 在 Windows 主机侧完成绘图、报告与结果整理

## 开发原则
- Ubuntu 虚拟机中的仓库是唯一真源
- Git 仓库只保留一份
- Windows 主机负责绘图、文档、结果分析
- 不采用手动复制代码的方式同步

## 目录说明
- `src/gnss_tx/`：核心源码
- `flowgraphs/`：GNU Radio Companion 工程
- `scripts/`：运行与辅助脚本
- `configs/`：参数配置
- `data/`：输入数据
- `results/`：运行结果
- `experiments/`：实验记录
- `docs/`：设计文档与报告
- `env/`：环境配置说明

## 开发工作流

- Git 分支职责、提交流程与提测门槛见 `docs/git_workflow.md`

## GNU Radio 一键启动

### 启动方式

| 命令 | 说明 |
|------|------|
| `./scripts/run_gnss_tx_grc.sh` | 用 GRC 打开主流图（可视化编辑，推荐） |
| `./scripts/run_gnss_tx_grc.sh --companion` | 同上（显式指定） |
| `./scripts/run_gnss_tx_grc.sh --run` | 直接运行主流图（跳过 GRC 界面） |
| `./scripts/run_gnss_tx_grc.sh --run --headless` | 无显示环境下直接运行 |

### 为什么必须通过脚本打开 GRC

本项目使用了两个自定义 GRC block：

- `gnss_tx_gps_l1_ca_source`（位于 `grc/blocks/`）
- `gnss_tx_usrp_sink`（位于 `grc/blocks/`）

GRC 需要通过环境变量 `GRC_BLOCKS_PATH` 才能找到这些 block 的定义文件（`.block.yml`）。
脚本会在启动前自动设置该变量：

```
GRC_BLOCKS_PATH=/usr/share/gnuradio/grc/blocks:/path/to/project/grc/blocks
```

**直接双击 `.grc` 文件或裸调 `gnuradio-companion` 会导致自定义 block 显示为未知，无法运行。**

### 在 GRC 界面内点击运行按钮

通过脚本打开 GRC 后，可以直接点击右上角运行按钮（▶）运行流图，无需切回终端再执行 `--run`。

> **注意**：GRC 点击运行时会将生成的 Python 文件写到项目根目录（而非 `flowgraphs/`），
> block 模板中的路径检测逻辑已处理该情况，会向上逐级查找包含 `src/gnss_tx/` 的目录。
> 如果看到 `ModuleNotFoundError: gnss_tx`，请确认是通过脚本启动的 GRC，而非直接启动。

## 当前阶段
阶段 1：目录初始化与 Git 建库
