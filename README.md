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

## 当前阶段
阶段 1：目录初始化与 Git 建库
