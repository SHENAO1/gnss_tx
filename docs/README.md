# GNSS_TX 文档目录

这里存放发射端的设计说明、工程架构文档和操作指南。文档本身不直接执行代码，但每篇文档都对应一组可以复现的入口命令或操作流程。

## 文档索引

- `introduction_guide.md`
  向他人介绍发射端工程的讲解导引，包含系统总览和 TX 信号生成原理两个部分，配合 Draw.io 图表使用。
- `gnss_tx_architecture_analysis.md`
  工程架构完整分析报告，含模块树、已实现能力边界和工程定位说明。
- `next_step_review.md`
  当前工程状态体检与下一阶段工程任务建议，适合在每个里程碑结束后回顾。
- `spectrum_analyzer_observation.md`
  频谱仪使用配置指南，含字段语义说明、推荐设置、单音校准排障和成功标志。
- `git_workflow.md`
  Git 分支职责与提交约定，含 GRC 生成文件管理和合并到 main 的条件。
- `design/actual_sample_rate_detection.md`
  采样率检测机制说明：USRP 硬件实际采样率 vs 软件请求采样率的检测与报告流程。
- `gnss_tx_signal_chain.drawio`
  发射端信号链架构图（DrawIO 格式）。
- `design/actual_sample_rate_detection.drawio`
  采样率检测流程图（DrawIO 格式）。

## 按入口命令复现

先看实现架构，再做配置自检：

```bash
cd ~/projects/gnss_tx
source .venv/bin/activate

# .venv 需通过 `bash env/ubuntu/setup.sh` 或
# `python3 -m venv --system-site-packages .venv` 创建

# 检查 Python 环境和项目结构
PYTHONPATH=src python3 scripts/quick_check.py

# dry-run：确认配置、UHD 设备发现和实验摘要
PYTHONPATH=src python3 scripts/run_tx.py \
    --dry-run \
    --config configs/tx_b210.yaml
```

启动当前可见谱扩频发射：

```bash
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --duration 30
```

## 阅读顺序建议

1. 先看 `gnss_tx_architecture_analysis.md`，了解工程整体结构和模块边界。
2. 再看 `next_step_review.md`，掌握当前工程状态和近期优先任务。
3. 开始实验前看 `spectrum_analyzer_observation.md`，确认频谱仪配置和安全基线。
4. 需要提交代码时参考 `git_workflow.md`。
5. 需要细节时回到 `design/` 子目录。
