 # GNSS_TX 工程架构分析报告

## 1. 总体功能分析

### 1.1 工程目标

结合 `README.md`、`src/`、`configs/`、`scripts/`、`docs/`、`experiments/` 与现有测试，本工程当前的实际目标可以概括为：

1. 生成 `GPS L1 C/A` 体制下的基带发送样本。
2. 以“单颗卫星、可选 `PRN1~32`”为当前实现对象，支持最基础的扩频发送。
3. 通过 `GNU Radio + UHD + USRP B210` 完成实际射频发射。
4. 通过 `QT 预览 + 频谱仪观察 + 实验清单/模板` 支撑实验室可见谱验证。
5. 围绕“参数是否能在频谱仪上稳定观察到宽带包络”构建实验记录链路。

从工程现状看，它当前并不是一个“完整 GNSS 发射机”，而是一个面向实验验证的 `GNSS/SDR` 发射原型系统，更准确地说，是一个：

`以 GPS L1 C/A 单星可选 PRN 为核心、采用预生成缓冲区循环回放方式、面向 USRP B210 和频谱仪观察的实验型发射链。`

### 1.2 当前已实现的功能模块

当前已经落地的模块能力如下：

- `ca/`
  - 生成 `PRN1~32` 的 GPS L1 C/A 码。
  - 提供按 `samples_per_chip` 做重复采样的基础能力。

- `nav/`
  - 提供 50 bps 导航 bit 的归一化与循环访问。
  - 当前导航信息仅是一个循环 bit pattern，不是真实 GPS 导航电文。

- `signal/`
  - 实现扩频状态机 `GpsL1CaBpskGenerator`。
  - 输出 BPSK 复基带样本。
  - 支持简单复数单音 `IQ` 生成，用于硬件链路校准。

- `gr/`
  - 提供 GNU Radio 源块封装。
  - 提供顶层流图装配 `GpsL1CaTxTopBlock`。
  - 支持 `QT` 时域/频域软件侧预览。
  - 采用“预生成缓冲区 + `vector_source_c` 循环回放”的稳定发送方式。

- `usrp/`
  - 配置 `B210` 发射参数。
  - 校验发送配置合法性。
  - 输出实验摘要、频谱仪观察建议与设备发现信息。
  - 连接 `UHD usrp_sink` 与运行时发送链。

- `scripts/`
  - 发射入口 `run_tx.py`。
  - 扩频链分析脚本 `analyze_prn1_spread.py`。
  - 单音测试 IQ 生成脚本 `generate_test_iq.py`。
  - Windows 绘图脚本 `plot_results_win.py`。
  - 参数扫描模板/实验清单/实验草稿生成脚本 `plan_tx_visibility_sweep.py`。
  - 环境快速检查脚本 `quick_check.py`。

### 1.3 当前未具备的典型 GNSS 发射能力

虽然目录中已经出现若干与完整 GNSS 发射机相关的命名，但当前工程还不具备以下关键能力：

- 真实导航电文与子帧构造。
- 多卫星并发合成。
- 载波 NCO、Doppler、码相位与时间基准控制。
- 星历/历书注入。
- 面向接收机可捕获、可跟踪、可解调、可定位的完整 GNSS 信号生成。

因此，本工程当前的主目标仍应界定为：

`单星可选 PRN 扩频基带发送与实验验证平台，而非完整 GNSS 卫星信号仿真器。`

## 2. 代码结构树

### 2.1 目录结构说明

以下目录树基于当前 workspace 实际内容整理，默认排除：

- `.git/`
- `.venv/`
- `__pycache__/`

同时保留：

- `results/`
- `experiments/`

因为它们已经是当前实验工作流的一部分，而不是无意义缓存。

### 2.2 完整结构树

```text
gnss_tx/
├── README.md                                        # 工程简介、目标与目录说明；但“当前阶段”描述已落后于现状
├── pyproject.toml                                   # Python 包元数据与 setuptools 打包配置
├── configs/
│   ├── gps_l1_ca.yaml                               # 空文件，占位配置；按命名应承载 GPS L1 C/A 信号级参数
│   ├── lab_single_tone.yaml                         # 空文件，占位配置；按命名应承载单音实验配置
│   ├── tx_b210.yaml                                 # 默认 B210 发射配置；注释称安全基线，但当前 tx_gain=10.0
│   └── tx_b210_visible_spectrum.yaml                # 已验证可见谱配置，用于复现实验观察结果
├── docs/
│   ├── spectrum_analyzer_observation.md             # 频谱仪观察说明、排障顺序与实验建议
│   └── gnss_tx_architecture_analysis.md             # 本架构分析报告
├── env/
│   ├── ubuntu/
│   │   ├── requirements.txt                         # Ubuntu 侧依赖说明
│   │   └── setup.sh                                 # Ubuntu 环境初始化脚本
│   └── windows/
│       ├── plot_env_notes.md                        # Windows 绘图环境说明
│       └── plotting_requirements.txt                # Windows 侧绘图依赖
├── experiments/
│   ├── 2026-03-22_prn1_visible_spectrum_checkpoint.md  # PRN1 可见谱实验检查点记录
│   ├── 2026-03-22_task_archive.md                   # 任务归档记录
│   ├── 2026-03-22_tx_visibility_sweep_draft.md      # 参数扫描实验草稿
│   ├── observation_log_template.md                  # 观察记录模板
│   ├── tx_visibility_sweep_checklist.md             # 参数扫描勾选清单
│   └── tx_visibility_sweep_template.csv             # 实验表模板
├── flowgraphs/
│   ├── gnss_tx_main.grc                             # GRC 主流图，描述 PRN1 扩频发送与 QT 预览
│   ├── single_tone_test.grc                         # 空文件，占位 GRC；按命名应为单音测试流图
│   └── two_tone_test.grc                            # 空文件，占位 GRC；按命名应为双音测试流图
├── grc/
│   └── blocks/
│       └── gnss_tx_gps_l1_ca_source.block.yml       # GNU Radio Companion 自定义块定义
├── results/
│   ├── csv/
│   │   ├── prn1_spread_preview.csv                  # 扩频预览数据表
│   │   └── tx_visibility_sweep_template.csv         # 参数扫描模板输出
│   ├── figs/
│   │   ├── prn1_spread_ca_code.png                  # C/A 码图
│   │   ├── prn1_spread_correlation.png              # 相关图
│   │   ├── prn1_spread_samples.png                  # 扩频样本图
│   │   ├── test_iq_spectrum.png                     # 单音频谱图
│   │   └── test_iq_time.png                         # 单音时域图
│   ├── logs/
│   │   └── prn1_spread_analysis.txt                 # 扩频分析文本报告
│   └── npy/
│       ├── prn1_spread_ca_code.npy                  # C/A 码数组
│       ├── prn1_spread_spread_chips.npy             # 扩频 chips
│       ├── prn1_spread_spread_samples.npy           # 扩频样本
│       ├── test_iq_tone.npy                         # 单音 IQ 数据
│       └── test_iq_tone_meta.txt                    # 单音元数据
├── scripts/
│   ├── analyze_prn1_spread.py                       # 扩频链离线分析、导出 CSV/NPY/图像/报告
│   ├── export_iq.py                                 # 空文件，占位脚本；按命名应支持 IQ 导出
│   ├── generate_nav.py                              # 空文件，占位脚本；按命名应支持导航电文生成
│   ├── generate_test_iq.py                          # 生成测试单音 IQ 数据
│   ├── plan_tx_visibility_sweep.py                  # 生成参数扫描 CSV、清单、实验草稿
│   ├── plot_results_win.py                          # Windows 侧结果绘图
│   ├── quick_check.py                               # 工程与环境快速检查
│   └── run_tx.py                                    # 主发射入口脚本
├── src/
│   ├── gnss_tx/
│   │   ├── __init__.py                              # 包版本与工程名
│   │   ├── ca/
│   │   │   ├── __init__.py                          # 导出 C/A 码相关接口
│   │   │   ├── prn_generator.py                     # PRN1 C/A 码生成器
│   │   │   └── resampler.py                         # chip 到 sample 的重复采样
│   │   ├── gr/
│   │   │   ├── __init__.py                          # 导出 GNU Radio 顶层接口
│   │   │   └── top_block.py                         # 源块、缓冲回放、QT 预览、TX top block
│   │   ├── nav/
│   │   │   ├── __init__.py                          # 导出 nav bits 接口
│   │   │   ├── nav_bits.py                          # 50 bps 循环导航 bit 归一化与访问
│   │   │   └── subframe_builder.py                  # 空文件，占位模块；按命名应实现子帧构造
│   │   ├── signal/
│   │   │   ├── __init__.py                          # 导出信号级接口
│   │   │   ├── iq_builder.py                        # 复数单音 IQ 生成
│   │   │   ├── modulator.py                         # chips 到复基带映射
│   │   │   └── spreader.py                          # PRN1 扩频状态机与样本生成核心
│   │   ├── usrp/
│   │   │   ├── __init__.py                          # 导出 USRP 控制层接口
│   │   │   ├── b210_sink.py                         # UHD B210 sink 创建与参数设置
│   │   │   └── tx_controller.py                     # 运行时配置、校验、报告、设备探测、top block 构造
│   │   └── utils/
│   │       ├── __init__.py                          # 当前为空
│   │       ├── io.py                                # YAML 配置加载
│   │       ├── logging.py                           # 空文件，占位模块；按命名应承载日志能力
│   │       └── timebase.py                          # 空文件，占位模块；按命名应承载时基能力
│   └── gnss_tx.egg-info/
│       ├── PKG-INFO                                 # 打包元数据
│       ├── SOURCES.txt                              # 打包文件列表
│       ├── dependency_links.txt                     # setuptools 生成文件
│       └── top_level.txt                            # 顶层包信息
└── tests/
    ├── test_ca_prn.py                               # C/A 码生成测试
    ├── test_gr_block.py                             # GNU Radio source/top block 测试
    ├── test_nav_bits.py                             # nav bit 归一化与循环访问测试
    ├── test_run_tx.py                               # run_tx 干运行与输出测试
    ├── test_spreader.py                             # 扩频状态机与 sample/chip 行为测试
    ├── test_sweep_planner.py                        # sweep 规划脚本输出测试
    ├── test_tx_controller.py                        # 配置校验、摘要输出、派生参数测试
    └── test_tx_profiles.py                          # 配置文件语义测试
```

### 2.3 模块分层理解

从架构分层上看，本工程可以抽象为 5 层：

1. `信号源逻辑层`
   - `ca.prn_generator`
   - `nav.nav_bits`

2. `基带生成层`
   - `signal.spreader`
   - `signal.modulator`
   - `signal.iq_builder`

3. `GNU Radio 装配层`
   - `gr.top_block`

4. `硬件控制与运行时配置层`
   - `usrp.b210_sink`
   - `usrp.tx_controller`

5. `脚本与实验流程层`
   - `scripts/`
   - `docs/`
   - `experiments/`
   - `results/`

## 3. 核心流程梳理

## 3.1 数据流：从输入到 USRP 发射

当前主数据流分为两类：`spread` 模式和 `tone` 模式。

### 3.1.1 spread 模式数据流

`configs/tx_b210*.yaml`
-> `scripts/run_tx.py`
-> `load_tx_runtime_config()`
-> `apply_overrides()`
-> `build_tx_top_block()`
-> `create_b210_sink()`
-> `GpsL1CaTxTopBlock`
-> `build_replay_samples()`
-> `normalize_nav_bits()`
-> `GpsL1CaBpskGenerator`
-> `generate_ca_code(prn_id=1)`
-> 生成一整段导航 pattern 周期对齐的复基带样本
-> `blocks.vector_source_c(..., repeat=True)`
-> `blocks.multiply_const_cc(config.amplitude)`
-> 可选 `qtgui.time_sink_c` / `qtgui.freq_sink_c`
-> `uhd.usrp_sink`
-> `USRP B210`
-> 射频输出

这里有一个非常重要的实现特点：

- 系统不是实时逐 sample 计算后直接送入 USRP。
- 它会先在 Python 中一次性预生成一段完整 replay buffer。
- 这段 buffer 与 `1 ms C/A epoch` 及 `20 ms nav bit epoch` 对齐。
- 随后通过 `vector_source_c` 做循环回放。

这样做的直接目的，是降低发送链的实时计算压力，并避免循环边界打断码相位/bit 相位连续性。

### 3.1.2 tone 模式数据流

`configs/tx_b210*.yaml` 或 CLI 覆盖
-> `scripts/run_tx.py`
-> `load_tx_runtime_config()`
-> `apply_overrides(signal_mode="tone")`
-> `GpsL1CaTxTopBlock`
-> `build_tone_replay_samples()`
-> `generate_complex_tone()`
-> `blocks.vector_source_c(..., repeat=True)`
-> `blocks.multiply_const_cc(config.amplitude)`
-> 可选 `QT` 预览
-> `uhd.usrp_sink`
-> `USRP B210`

tone 模式主要用于：

- 硬件链路校准。
- 频谱仪寻找窄峰。
- 在扩频包络不易观察时，先验证 `B210 -> 同轴 -> 频谱仪` 链路本身是否正常。

## 3.2 各模块调用关系

### 3.2.1 运行时主链

`scripts/run_tx.py` 是整个发送流程的总入口，其职责包括：

- 解析 CLI 参数。
- 读取 YAML 配置。
- 合并命令行覆盖项。
- 打印配置摘要与频谱仪观察建议。
- 发现 UHD 设备。
- 创建 GNU Radio top block。
- 控制发射时长、`QT` 事件循环和退出流程。

### 3.2.2 配置与控制层

`src/gnss_tx/usrp/tx_controller.py` 是运行时总控层，职责包括：

- 定义 `TxRuntimeConfig`。
- 校验参数合法性。
- 在 `samples_per_chip` 与 `sample_rate` 之间做派生。
- 生成实验表格摘要。
- 调用 `create_b210_sink()` 和 `GpsL1CaTxTopBlock`。

可以认为它是：

`配置中心 + 发送装配协调器 + 实验输出接口`

### 3.2.3 GNU Radio 装配层

`src/gnss_tx/gr/top_block.py` 是 GNU Radio 装配层，职责包括：

- 定义 `TxBlockConfig`。
- 预生成 replay samples。
- 构建 `vector_source_c` 循环回放源。
- 连接幅度缩放块。
- 可选连接 `QT` 预览 sink。
- 可选连接 `uhd.usrp_sink`。

这一层并不负责复杂算法，而是负责把“已生成好的基带样本”装配成可运行的流图。

### 3.2.4 信号生成层

`src/gnss_tx/signal/spreader.py` 是当前最核心的信号生成模块，职责包括：

- 管理 `code_phase`、`nav_epoch_in_bit`、`nav_bit_index`、`sample_phase_in_chip`。
- 在样本级推进 PRN 扩频状态。
- 将 `C/A code` 与 `nav bit` 组合成 spread chip。
- 生成复数基带 BPSK 样本。

`src/gnss_tx/signal/iq_builder.py` 则负责最简单的复单音生成。

### 3.2.5 底层信号源逻辑

最底层逻辑由两个模块组成：

- `src/gnss_tx/ca/prn_generator.py`
  - 生成 `PRN1` 的 C/A 码。

- `src/gnss_tx/nav/nav_bits.py`
  - 将输入导航 bit pattern 统一归一化到 `+1/-1` 表示。
  - 提供循环 bit 源。

这两者共同构成当前扩频信号的原始离散逻辑源。

## 3.3 其它辅助流程

### 3.3.1 扩频离线分析链

`scripts/analyze_prn1_spread.py` 的流程为：

1. 读取命令行参数。
2. 生成 `PRN1` C/A 码。
3. 生成一段扩频 chips。
4. 生成一段扩频复基带 samples。
5. 计算一阶相关结果。
6. 输出：
   - `NPY`
   - `CSV`
   - `PNG`
   - 文本报告

它的意义不在于发射，而在于：

- 对基带链路做离线可视化验证。
- 证明扩频状态机的输出结构正确。
- 为后续实验报告提供分析素材。

### 3.3.2 实验规划链

`scripts/plan_tx_visibility_sweep.py` 的流程为：

1. 读取指定配置文件。
2. 构建基准组、`tx_gain` 扫描组、`amplitude` 扫描组、重复性验证组。
3. 输出：
   - CSV 模板
   - Markdown 清单
   - Markdown 实验草稿

这说明当前工程不仅关注“能发”，还已经开始形成：

`可复现实验流程`

但该流程当前仍明显偏人工操作，尚未形成自动化测试闭环。

## 4. 当前实现程度评估

## 4.1 已完成

以下能力已经可以认为“实现完成”：

- `PRN1` 的 GPS L1 C/A 码生成。
- C/A 码基本性质测试。
- 50 bps 循环导航 bit 归一化与访问。
- 基于 `GpsL1CaBpskGenerator` 的扩频状态推进。
- 基于复数样本的 BPSK 基带生成。
- 单音基带生成。
- GNU Radio 侧 `source/top block` 装配。
- `vector_source_c` 缓冲回放发送。
- `QT` 软件侧时域/频域预览。
- `UHD B210 sink` 配置。
- 运行时配置加载、覆盖与参数合法性校验。
- 实验摘要输出与频谱仪观察建议输出。
- 扩频链离线分析脚本。
- 参数 sweep 模板/清单/实验草稿生成。
- 基于 `unittest` 的核心功能测试覆盖。

## 4.2 半完成

以下内容已经有明确实现方向，但仍处在“半完成”状态：

- `GRC` 流图与 Python runtime 双路线并存。
  - `flowgraphs/gnss_tx_main.grc` 已存在。
  - Python 运行时也已经可直接发射。
  - 但两套路线并未完全统一，存在后续分叉风险。

- tone 模式链路已经存在，但工程配套不完整。
  - 核心逻辑可用。
  - 但 `lab_single_tone.yaml` 仍为空。
  - `single_tone_test.grc` 仍为空。

- 实验文档与结果资产已形成体系，但自动化程度有限。
  - 已有 checkpoint、清单、模板、草稿、图像与导出数据。
  - 但数据采集、截图管理、结果回归仍依赖人工。

- 默认发射配置语义不稳定。
  - `tx_b210.yaml` 被描述为“首次低功率安全基线”。
  - 但当前内容与测试预期不一致。

## 4.3 未实现但应存在

从工程命名、目录预留和 GNSS 发射机的系统完整性来看，以下内容应存在但当前未实现：

- `src/gnss_tx/nav/subframe_builder.py`
- `scripts/generate_nav.py`
- `scripts/export_iq.py`
- `src/gnss_tx/utils/logging.py`
- `src/gnss_tx/utils/timebase.py`
- `configs/gps_l1_ca.yaml`
- `configs/lab_single_tone.yaml`
- `flowgraphs/single_tone_test.grc`
- `flowgraphs/two_tone_test.grc`

更深层的系统能力缺失包括：

- 真实 GPS NAV message 生成。
- 子帧拼装与校验。
- 多 PRN 支持。
- 多卫星并发基带合成。
- 码相位、载波、Doppler、时基控制。
- IQ 导出规范与离线回放流程。
- 完整自动化测试与 CI 入口。

## 5. 下一步建议

## 5.1 从工程完善角度

### 建议 1：统一“默认基线配置”的定义

当前最直接需要处理的问题是：

- `configs/tx_b210.yaml` 注释称其为“首次低功率安全基线”。
- 但实际 `tx_gain=10.0`。
- `tests/test_tx_profiles.py` 认为它应为保守基线并期望 `tx_gain=0.0`。

建议尽快在以下三者之间统一语义：

- 配置文件内容
- 测试断言
- 文档描述

否则后续实验人员会误以为“默认配置一定安全”，而测试也会持续失真。

### 建议 2：明确 Python runtime 与 GRC 的主从关系

当前工程同时维护：

- Python 运行链
- `GRC` 主流图

建议尽快确定一条“权威实现路径”：

- 如果以 Python runtime 为主，则将 GRC 定位为展示/原型参考。
- 如果以 GRC 为主，则应保证 Python runtime 与 GRC 参数和逻辑严格同构。

否则后续修改会出现：

- Python 能发、GRC 不一致。
- GRC 更新了、脚本链没有同步。

### 建议 3：清理空壳模块或尽快补齐

当前存在多个空文件，它们会向阅读者传达“能力已经规划”，但实际上并未提供任何功能。建议：

- 若短期不做，移除或在文件内写清楚占位状态。
- 若近期要做，优先补齐最关键的：
  - `subframe_builder.py`
  - `generate_nav.py`
  - `export_iq.py`
  - `lab_single_tone.yaml`

### 建议 4：增加配置 schema 和环境自检

当前已有 `TxRuntimeConfig.validate()`，但还可以进一步增强：

- 配置文件级 schema 校验。
- 必填字段显式化。
- 避免依赖 dataclass 默认值隐式补齐关键实验参数。
- 将 `quick_check.py` 扩展为更完整的环境/依赖/设备检查入口。

### 建议 5：补齐自动化测试与 CI 入口

当前测试覆盖度并不低，但存在两个工程问题：

- 当前环境没有 `pytest`。
- 测试依赖本地手工运行，没有 CI 驱动。

建议：

- 固化标准测试入口。
- 在文档中明确测试命令。
- 在可行时接入 CI。

## 5.2 从 GNSS 发射机角度

### 建议 1：优先实现真实导航电文与子帧构造

当前工程最大的“GNSS 原型”与“GNSS 发射机”差距就在这里：

- 现在的导航层本质是循环 bit pattern。
- 它可以支持扩频实验。
- 但不构成真实 GPS 导航信号。

因此，下一阶段最关键的 GNSS 向演进目标应是：

- 实现 `subframe_builder.py`
- 实现 `generate_nav.py`
- 支持真实导航字、校验与子帧组织

### 建议 2：从“可选单 PRN”扩展到多星合成

当前 `generate_ca_code()` 已支持 `PRN1~32`，单星选择路径与测试已经补齐。后续若继续扩展，更高一层的目标应是：

- 在保持单星链路稳定的前提下设计多星合成接口。
- 明确多星功率分配、码相位与导航 bit 组织方式。
- 为后续多卫星合成铺路。

### 建议 3：引入时基、码相位与 Doppler 控制

真正的 GNSS 发射机必须控制：

- 码相位
- 载波频偏
- 卫星相对运动引起的 Doppler
- 时间对齐

当前这些能力基本未实现，仅有初始码相位/导航 epoch 的简单入口。因此建议将：

- `timebase.py`
- 频率偏移/NCO
- 状态推进模型

作为下一阶段核心架构工作。

### 建议 4：从“可见谱”升级到“可捕获/可相关/可解调”

当前工程已经证明：

- 宽带包络可以发出来。

下一步更高价值的验证目标应依次升级为：

1. 接收端可检测到目标 PRN 相关峰。
2. 码相位可稳定捕获。
3. 导航比特可解调。
4. 最终可支撑接收机级验证。

## 5.3 从实验验证角度

### 建议 1：建立标准实验链路

建议将实验流程固定为：

1. 单音校准
2. 扩频可见谱确认
3. 重复性测试
4. 接收端相关验证

这样可以把“硬件链路问题”和“扩频链问题”分层隔离。

### 建议 2：强化 underflow 与发送稳定性观测

当前文档中已经提到 underflow 排查，但系统没有形成统一记录。建议：

- 在运行脚本中记录是否出现发送 underflow。
- 在实验表格中增加对应字段。
- 将“可见但不稳定”和“完全稳定”明确区分。

### 建议 3：规范截图、参数与结果归档

当前已经有：

- `results/`
- `experiments/`
- sweep 模板

建议继续规范：

- 截图命名规则。
- 每次实验的配置快照。
- 与观察结果绑定的日志记录。

### 建议 4：补齐 IQ 导出与第三方复核

建议尽快补齐 `export_iq.py`，形成：

- 基带导出
- MATLAB/Python/第三方 SDR 工具复核
- 离线相关分析

这样可以在不依赖实时发射的情况下验证信号质量。

## 6. 明显设计问题与隐患

## 6.1 配置、测试、文档语义漂移

这是当前最明显的问题。

`configs/tx_b210.yaml` 的注释表述、测试断言和实际配置值不一致，说明：

- 工程中关于“默认安全基线”的定义已经漂移。
- 当前仓库事实与原设计意图没有保持同步。

这是一个工程治理问题，而不仅仅是参数值问题。

## 6.2 `amplitude` 在默认配置中未显式声明

`tx_b210.yaml` 当前没有显式写出 `amplitude`，而是依赖 `TxRuntimeConfig` 的默认值 `0.25`。这会带来两个问题：

- 实验参数透明度不足。
- 后续若 dataclass 默认值改变，配置文件行为会静默变化。

对于实验工程，这种隐式继承会增加追踪成本。

## 6.3 `continuous` 字段语义偏弱

配置中存在 `continuous` 字段，但在实际运行脚本中：

- 真正决定是否长时间运行的主要是 `duration_s` 与主循环逻辑。
- `continuous` 本身没有形成强语义约束。

这说明该字段目前更像“意图字段”，不是“严格生效字段”。

## 6.4 Python runtime 与 GRC 双实现漂移风险

当前工程同时存在：

- Python 侧 `vector_source_c` replay 方案
- `gnss_tx_main.grc` 中的自定义 source block 路线

两者短期内共存是合理的，但长期会带来：

- 行为不一致
- 参数不一致
- 调试成本增加

如果后续功能继续扩展，这会成为维护隐患。

## 6.5 多个关键模块为空，占位痕迹明显

空模块说明架构方向已经被预想，但没有落地，这本身没有问题。问题在于：

- 这些模块名称都非常关键。
- 读者会自然认为系统已经至少具备骨架实现。
- 实际上它们仍完全空白。

因此需要尽快明确哪些是短期目标，哪些是远期规划。

## 6.6 “导航层”本质仍是循环 bit pattern

当前 `nav_bits.py` 的设计对实验非常有效，因为它足够简单、可控、可重复。但从 GNSS 发射机角度看，其问题也很明确：

- 没有真实导航字结构。
- 没有子帧。
- 没有校验。
- 没有时间语义。

因此当前导航层更准确的定义应是：

`扩频调制辅助比特源`

而不是完整 `GPS NAV` 层。

## 6.7 当前系统支持单星可选 PRN，但仍不是多星平台

当前所有关键链路已经支持：

- `prn_id in [1, 32]`

但系统仍保持“每次只发送一颗卫星”的实验化架构，因此：

- 它是一个单星、可选 PRN、实验化原型。
- 还不能被视作多星 GNSS 发送平台。

## 7. 关键接口说明

当前最值得在技术报告中点名的接口如下：

- `TxRuntimeConfig`
  - 发送运行时配置中心。

- `TxBlockConfig`
  - GNU Radio top block 的装配配置。

- `GpsL1CaBpskGenerator`
  - 当前最核心的扩频样本生成器。

- `generate_ca_code(prn_id)`
  - C/A 码底层生成接口。

- `load_tx_runtime_config(path)`
  - YAML 到运行时配置对象的入口。

- `apply_overrides(config, **overrides)`
  - CLI 覆盖与派生参数重算入口。

- `build_tx_top_block(config)`
  - 运行时发射图构造入口。

- `scripts/run_tx.py`
  - 实际发射总入口。

- `scripts/plan_tx_visibility_sweep.py`
  - 参数扫描实验工作流入口。

## 8. 当前实现状态的验证证据

本报告结论不是纯静态推断，还结合了当前仓库内可执行验证结果。

### 8.1 快速检查

`scripts/quick_check.py` 在当前环境可运行通过，说明：

- `src/gnss_tx`
- `configs`
- `scripts`
- `results`
- `flowgraphs`

这些关键路径已存在，且 Python 环境中的基础依赖至少足以完成最基本检查。

### 8.2 单元测试结果

在当前环境下执行：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

得到结论：

- 共执行 `33` 项测试。
- `32` 项通过。
- `1` 项失败。

失败项为：

- `tests/test_tx_profiles.py::test_safe_baseline_profile_is_conservative`

失败原因不是核心信号逻辑崩溃，而是：

- `configs/tx_b210.yaml` 当前值为 `tx_gain = 10.0`
- 测试却认为其应为安全保守基线并断言 `tx_gain = 0.0`

这进一步证明当前最明显的问题之一是：

`配置文件语义和测试预期已经漂移。`

### 8.3 pytest 不可用

当前环境中直接执行 `pytest` 会失败，原因是：

- `No module named pytest`

这说明：

- 测试体系当前更依赖标准库 `unittest`。
- 工程环境说明和测试入口仍需要进一步统一。

## 9. 综合结论

本工程已经完成了一个清晰可运行的第一阶段目标：

`构建基于 Python + GNU Radio + USRP B210 的 PRN1 GPS L1 C/A 扩频发送原型，并支撑频谱仪可见谱实验。`

它的优势在于：

- 主链路简洁。
- 扩频状态机逻辑清晰。
- 缓冲回放方案适合实验。
- 文档、结果、实验模板已经开始成体系。

它的局限也非常明确：

- 当前只是单 `PRN1` 原型。
- 导航层不是真实 GPS NAV。
- 缺少多卫星、时基、Doppler 和接收机级验证能力。
- 代码中存在若干关键空模块。
- 默认配置语义与测试已出现漂移。

因此，若从系统定位上总结：

`当前工程已经是一套可用的 GNSS 扩频发射实验平台，但还不是完整 GNSS 发射机。`

下一阶段最值得优先投入的方向是：

1. 统一配置、测试、文档语义。
2. 补齐真实导航电文与子帧构造。
3. 扩展多 PRN 与更严格的时间/频率控制。
4. 建立从”可见谱”到”可捕获/可解调”的验证闭环。

---

## 10. 模块实现参考手册

### 10.1 `ca/` — C/A 码生成层

#### `prn_generator.py`

| 符号 | 类型 | 说明 |
|------|------|------|
| `CA_CODE_LENGTH` | `int = 1023` | 每个 C/A 码周期的 chip 数，对应 1 ms 码周期 |
| `generate_ca_code(prn_id)` | `ndarray[int8]` | 生成目标 PRN 的 1023 chip C/A 码，输出 +1/-1 表示 |

实现原理：
- 采用两个 10 级 LFSR（G1、G2），初值全 1。
- G1 反馈多项式：`x^3 ^ x^10`（对应抽头 3、10）。
- G2 反馈多项式：`x^2 ^ x^3 ^ x^6 ^ x^8 ^ x^9 ^ x^10`。
- 当前实现覆盖 GPS L1 C/A `PRN1~32`。
- 不同 PRN 通过各自的 G2 输出抽头组合区分。

#### `resampler.py`

| 符号 | 类型 | 说明 |
|------|------|------|
| `repeat_chips(chips, samples_per_chip)` | `ndarray[int8]` | 将 chip 序列按倍数展开为 sample 序列（`numpy.repeat`） |

---

### 10.2 `nav/` — 导航比特层

#### `nav_bits.py`

| 符号 | 类型 | 说明 |
|------|------|------|
| `NAV_BIT_RATE_BPS` | `int = 50` | GPS L1 C/A 导航电文比特率 |
| `CA_EPOCHS_PER_NAV_BIT` | `int = 20` | 每个导航 bit 覆盖的 1 ms C/A 码周期数 |
| `DEFAULT_NAV_PATTERN` | `tuple` | 默认导航 bit 循环模式 `(1,-1,1,1,-1,-1,1,-1)` |
| `normalize_nav_bits(nav_pattern)` | `ndarray[int8]` | 将 `1/0/+1/-1/字符串` 格式的导航 bit 统一转为 `+1/-1` 表示 |
| `CyclicNavBitSource` | `dataclass` | 不可变循环导航 bit 源，`bit_at(index)` 按索引取 bit（自动循环） |

输入格式兼容：
- `”1 0 1 1 0 0 1 0”` — 空格分隔字符串
- `”10110010”` — 连续字符串
- `[1, -1, 1, 1, -1, -1, 1, -1]` — 整数列表
- `[1, 0, 1, 1, 0, 0, 1, 0]` — 整数列表（0 被归一化为 -1）

#### `subframe_builder.py`

**当前为空文件**，按命名应实现真实 GPS NAV 子帧构造，是后续扩展占位模块。

---

### 10.3 `signal/` — 基带信号生成层

#### `spreader.py`

核心类 `GpsL1CaBpskGenerator`：

```
构造参数：
  prn_id              int     PRN 编号（当前支持 1~32）
  samples_per_chip    int     每 chip 对应的 sample 数
  amplitude           float   输出幅度（建议 ≤ 1.0）
  nav_pattern         list    导航 bit 循环模式
  initial_code_phase  int     初始码相位 [0, 1022]
  initial_nav_epoch   int     初始导航 epoch 偏移 [0, 19]
  initial_nav_bit_index int   初始导航 bit 索引
```

状态机字段（`GeneratorState`）：

| 字段 | 说明 |
|------|------|
| `code_phase` | 当前处于 PRN 周期的第几个 chip [0, 1022] |
| `nav_epoch_in_bit` | 当前导航 bit 内的第几个 1 ms epoch [0, 19] |
| `nav_bit_index` | 当前导航 bit 索引（无上限，循环取模） |
| `sample_phase_in_chip` | 当前 chip 内已输出多少个 sample |

主要方法：

| 方法 | 返回 | 说明 |
|------|------|------|
| `generate_chips(num_chips)` | `ndarray[int8]` | 生成 chip 级序列（chip 对齐，用于离线分析） |
| `generate_samples(num_samples)` | `ndarray[complex64]` | 生成复数基带 sample（支持跨 chip 边界任意截断） |

信号链关系：
```
nav_bit[20ms] × ca_chip[1/1.023MHz] = spread_chip → 展开为 samples_per_chip 个 sample
```

#### `iq_builder.py`

| 函数 | 返回 | 说明 |
|------|------|------|
| `generate_complex_tone(sample_rate, tone_freq, duration_s, amplitude)` | `ndarray[complex64]` | 生成 `A·exp(j2πft/fs)` 复指数基带单音，用于硬件链路校准 |

#### `modulator.py`

| 函数 | 返回 | 说明 |
|------|------|------|
| `chips_to_complex_baseband(chips, amplitude)` | `ndarray[complex64]` | 将 +/-1 chip 序列映射为 complex64（I 支路 BPSK，Q=0） |

---

### 10.4 `gr/` — GNU Radio 装配层

#### `top_block.py`

**`TxBlockConfig`**（frozen dataclass）：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `prn_id` | `1` | PRN 编号 |
| `signal_mode` | `”spread”` | `”spread”` 或 `”tone”` |
| `samples_per_chip` | `4` | chip → sample 展开比 |
| `amplitude` | `0.25` | 最终发射幅度 |
| `nav_pattern` | `”1 0 1 1 0 0 1 0”` | 导航 bit 循环模式 |
| `tone_offset_hz` | `500e3` | 单音相对中心频率的频偏（仅 tone 模式） |
| `tone_buffer_s` | `0.1` | 预生成单音缓冲时长（仅 tone 模式） |
| `center_freq` | `100e6` | 射频中心频率 Hz |
| `sample_rate` | `4.092e6` | 基带采样率 Sps |
| `tx_gain` | `None` | 发射增益 dB（None 则取设备最小增益） |
| `bandwidth` | `None` | 模拟带宽 Hz |
| `antenna` | `”TX/RX”` | B210 天线端口 |
| `usrp_addr` | `”type=b200”` | UHD 设备地址字符串 |
| `enable_qt_preview` | `False` | 是否启用 QT 时域/频域预览窗口 |
| `initial_code_phase` | `0` | 初始码相位 |
| `initial_nav_epoch` | `0` | 初始导航 epoch 偏移 |
| `initial_nav_bit_index` | `0` | 初始导航 bit 索引 |

**`GpsL1CaTxTopBlock`**（`gr.top_block` 子类）：

流图结构（spread 模式）：
```
build_replay_samples() → vector_source_c(repeat=True)
                       → multiply_const_cc(amplitude)
                       → [可选] qtgui.time_sink_c
                       → [可选] qtgui.freq_sink_c
                       → uhd.usrp_sink
```

关键设计：replay buffer 长度 = `len(nav_bits) × 20 × 1023 × samples_per_chip`，
保证回放边界与码相位和导航 bit 相位同时对齐。

**辅助函数**：

| 函数 | 说明 |
|------|------|
| `build_replay_samples(**kwargs)` | 预生成完整 nav pattern 周期对齐的扩频 sample buffer |
| `build_tone_replay_samples(**kwargs)` | 预生成单音 sample buffer |
| `make_gps_l1_ca_vector_source(**kwargs)` | 构造循环 vector source（供外部流图使用） |

---

### 10.5 `usrp/` — 硬件控制与运行时配置层

#### `b210_sink.py`

| 函数 | 说明 |
|------|------|
| `create_b210_sink(config)` | 创建 UHD B210 发射 sink，设置采样率、中心频率、增益、带宽、天线 |

UHD stream 参数：`cpu_format=fc32`（主机侧 complex float），`otw_format=sc16`（USB 线上 16 位整数）。

#### `tx_controller.py`

**`TxRuntimeConfig`**（frozen dataclass）— 运行时参数的完整定义，包含所有 YAML 可配置字段。

关键方法：

| 方法 | 说明 |
|------|------|
| `validate()` | 校验参数合法性，包括 `spread` 模式下 `sample_rate == 1.023e6 × samples_per_chip` |
| `to_block_config()` | 转换为 `TxBlockConfig` 传入 GNU Radio 装配层 |

辅助函数：

| 函数 | 说明 |
|------|------|
| `load_tx_runtime_config(path)` | 从 YAML 加载并校验配置 |
| `apply_overrides(config, **kwargs)` | 合并 CLI 覆盖项并重新派生 `sample_rate`/`bandwidth` |
| `format_config_report(config)` | 打印运行时参数摘要 |
| `format_observation_checklist(config)` | 打印频谱仪观察步骤清单 |
| `format_lab_table_summary(config, device_report)` | 打印实验表格关键字段摘要 |
| `is_b210_available()` | 调用 `uhd_find_devices` 判断是否有 B210 可用 |
| `build_tx_top_block(config)` | 创建 B210 sink 并装配完整发射 top block |

---

### 10.6 `utils/` — 工具层

#### `io.py`

| 函数 | 说明 |
|------|------|
| `load_yaml_file(path)` | 读取 YAML 文件并返回 `dict`，文件为空时返回 `{}`，非 mapping 格式时报错 |

#### `timebase.py` / `logging.py`

**当前为空文件**，占位用，后续分别实现时基控制和统一日志。

---

## 11. 配置文件参数参考

所有配置文件均为 YAML 格式，位于 `configs/`。字段含义如下：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `prn_id` | int | `1` | PRN 编号（当前支持 1~32） |
| `signal_mode` | str | `”spread”` | `”spread”`（扩频）或 `”tone”`（单音校准） |
| `usrp_addr` | str | `”type=b200”` | UHD 设备地址，可用 `”serial=XXXXXXX”` 固定到序列号 |
| `center_freq` | float | `100e6` | 射频中心频率 Hz |
| `samples_per_chip` | int | `4` | 每 chip 的 sample 数；决定 `sample_rate = 1.023e6 × samples_per_chip` |
| `sample_rate` | float | `4.092e6` | 基带采样率 Sps（通常由 `samples_per_chip` 派生，不必手动填） |
| `tx_gain` | float \| null | `null` | 发射增益 dB，`null` 时取设备最小增益 |
| `amplitude` | float | `0.25` | 基带幅度 (0, 1]，乘在 replay buffer 上 |
| `antenna` | str | `”TX/RX”` | B210 天线端口，可选 `”TX/RX”` 或 `”TX/RX2”` 等 |
| `bandwidth` | float \| null | `null` | 模拟带宽 Hz，`null` 时派生自 `sample_rate` |
| `nav_pattern` | str | `”1 0 1 1 0 0 1 0”` | 循环导航 bit 模式，空格分隔，0 等价于 -1 |
| `tone_offset_hz` | float | `500e3` | 单音频偏 Hz（仅 `signal_mode=tone` 生效） |
| `tone_buffer_s` | float | `0.1` | 单音预生成缓冲时长 s（仅 `tone` 模式） |
| `duration_s` | float \| null | `null` | 发射时长 s，`null` 为持续发射直到 Ctrl-C |
| `continuous` | bool | `true` | 持续模式标志（语义上与 `duration_s` 联动） |
| `initial_code_phase` | int | `0` | 初始码相位 chip 偏移 [0, 1022] |
| `initial_nav_epoch` | int | `0` | 初始导航 bit 内 epoch 偏移 [0, 19] |
| `initial_nav_bit_index` | int | `0` | 初始导航 bit 索引 |

**内置配置文件一览**：

| 文件 | 用途 |
|------|------|
| `configs/tx_b210.yaml` | 保守安全基线（`tx_gain=0`, `amplitude=0.25`），用于首次连线 RF 检查 |
| `configs/tx_b210_visible_spectrum.yaml` | 已验证可见谱配置（`tx_gain=10`, `amplitude=1.0`），用于频谱仪观察复现 |
| `configs/tx_b210_sn8003272.yaml` | 固定序列号 + OTA 配置（`center_freq=150MHz`, `tx_gain=20`），双USRP空收场景 |

---

## 12. 脚本命令参考

所有脚本需在项目根目录下运行，并设置 `PYTHONPATH=src`。

### 12.1 环境快速检查

```bash
cd /path/to/gnss_tx
PYTHONPATH=src python3 scripts/quick_check.py
```

输出：Python 版本、numpy 版本、关键路径检查结果。

### 12.2 主发射脚本 `run_tx.py`

```bash
# 基本用法（使用默认配置文件）
PYTHONPATH=src python3 scripts/run_tx.py

# 指定配置文件
PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml

# 干运行（只打印配置，不启动发射）
PYTHONPATH=src python3 scripts/run_tx.py --dry-run

# 指定发射时长 20 秒
PYTHONPATH=src python3 scripts/run_tx.py --duration 20

# 指定中心频率和增益
PYTHONPATH=src python3 scripts/run_tx.py --center-freq 150e6 --tx-gain 20

# 单音校准模式
PYTHONPATH=src python3 scripts/run_tx.py --signal-mode tone --tone-offset-hz 500000

# 启用 QT 软件侧频谱预览（需 GNU Radio Qt GUI）
PYTHONPATH=src python3 scripts/run_tx.py --qt-preview --duration 30

# OTA 双USRP场景：指定发射USRP序列号
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_sn8003272.yaml \
    --tx-gain 20 --amplitude 1.0 --duration 60
```

CLI 参数完整列表：

| 参数 | 说明 |
|------|------|
| `--config FILE` | YAML 配置文件路径（默认 `configs/tx_b210.yaml`） |
| `--center-freq HZ` | 射频中心频率 Hz |
| `--tx-gain DB` | 发射增益 dB |
| `--sample-rate SPS` | 采样率 Sps（通常由 `samples-per-chip` 派生） |
| `--samples-per-chip N` | 每 chip sample 数，自动派生采样率 |
| `--signal-mode {spread,tone}` | 信号模式 |
| `--nav-pattern STR` | 导航 bit 循环模式字符串 |
| `--tone-offset-hz HZ` | 单音频偏 Hz |
| `--duration S` | 发射时长 s |
| `--amplitude A` | 基带幅度 (0, 1] |
| `--qt-preview` | 启用 QT 时域/频域预览 |
| `--dry-run` | 仅打印配置，不启动发射 |

### 12.3 扩频链离线分析 `analyze_prn1_spread.py`

```bash
# 默认参数（40 ms，samples_per_chip=4，PRN1）
PYTHONPATH=src python3 scripts/analyze_prn1_spread.py

# 自定义参数
PYTHONPATH=src python3 scripts/analyze_prn1_spread.py \
    --prn-id 7 \
    --samples-per-chip 4 \
    --num-ms 40 \
    --nav-pattern “1 0 1 1 0 0 1 0” \
    --prefix prn7_spread
```

输出到 `results/`：
- `figs/prn{n}_spread_ca_code.png` — C/A 码波形图
- `figs/prn{n}_spread_samples.png` — 扩频基带样本图
- `figs/prn{n}_spread_correlation.png` — 1 ms 相关峰图
- `npy/prn{n}_spread_ca_code.npy` — C/A 码 numpy 数组
- `npy/prn{n}_spread_spread_chips.npy` — 扩频 chips
- `npy/prn{n}_spread_spread_samples.npy` — 扩频复基带样本
- `csv/prn{n}_spread_preview.csv` — 前 64 chip 对照表
- `logs/prn{n}_spread_analysis.txt` — 文本分析报告

### 12.4 单音测试 IQ 生成 `generate_test_iq.py`

```bash
PYTHONPATH=src python3 scripts/generate_test_iq.py
```

生成 `results/npy/test_iq_tone.npy`（1 MHz 采样率，50 kHz 单音，10 ms 时长）。

### 12.5 参数扫描实验规划 `plan_tx_visibility_sweep.py`

```bash
# 使用默认可见谱配置
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py

# 指定配置文件和输出路径
PYTHONPATH=src python3 scripts/plan_tx_visibility_sweep.py \
    --config configs/tx_b210_visible_spectrum.yaml \
    --csv-output results/csv/sweep_template.csv \
    --checklist-output experiments/sweep_checklist.md
```

生成三份实验文档：
- CSV 参数模板（每组实验一行）
- Markdown 勾选清单（含逐步操作指导）
- Markdown 实验记录草稿（含结果汇总表格）

### 12.6 GNU Radio Companion 启动器 `run_gnss_tx_grc.sh`

```bash
# 在 GRC 界面中打开主流图（默认）
bash scripts/run_gnss_tx_grc.sh

# 直接运行流图（跳过 GRC 界面）
bash scripts/run_gnss_tx_grc.sh --run

# 无显示环境下运行
bash scripts/run_gnss_tx_grc.sh --run --headless
```

### 12.7 单元测试

```bash
# 运行全部测试（使用 unittest）
PYTHONPATH=src python3 -m unittest discover -s tests -v

# 运行单个测试文件
PYTHONPATH=src python3 -m unittest tests/test_spreader.py -v
```
