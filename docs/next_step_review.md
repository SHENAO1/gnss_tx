# 单星可选 PRN 扩频发送平台下一阶段工程体检与整理建议

## 结论摘要

当前仓库已经形成一个可运行的“单星可选 `PRN1~32` 的 GPS L1 C/A”扩频发送实验平台，主链清晰、实验链条基本成形，但配置真源、实验记录和 GNU Radio Companion 镜像入口之间仍然存在语义漂移。经过本次整理，当前最重要的工程判断是：

- Python runtime 仍是权威主线。
- GNU Radio Companion 保留为 Ubuntu 虚拟机里的“可点击运行镜像入口”。
- `tx_b210.yaml`、`tx_b210_visible_spectrum.yaml`、历史 checkpoint 和 `gnss_tx_main.grc` 需要明确区分语义，不能再互相冒充。
- 下一阶段最优先的工作仍然是把“单星可选 PRN”实验平台做稳定、清晰、可验证，而不是扩展完整 GNSS 发射能力。

## 本次基线核查

本报告基于本次仓库内的非破坏性核查与验证命令：

- `env PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - 变更前通过 `32` 项，仅 `test_safe_baseline_profile_is_conservative` 失败。
  - 失败根因是 `configs/tx_b210.yaml` 在当前 worktree 中缺失，不是算法链路失败。
- `env PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --dry-run`
  - 能正常输出运行时配置、观察清单和实验摘要，说明 Python runtime 主链可用。
- `python3 scripts/quick_check.py`
  - 变更前会因 `src` 路径未自动注入而失败。
- `env PYTHONPATH=src python3 scripts/quick_check.py`
  - 能正常运行，说明问题在启动方式不统一，而不是逻辑本身异常。

## 当前真实主链

当前工程的真实主链仍然是：

- [scripts/run_tx.py](../scripts/run_tx.py)
- [src/gnss_tx/usrp/tx_controller.py](../src/gnss_tx/usrp/tx_controller.py)
- [src/gnss_tx/gr/top_block.py](../src/gnss_tx/gr/top_block.py)
- [src/gnss_tx/signal/spreader.py](../src/gnss_tx/signal/spreader.py)
- [src/gnss_tx/nav/nav_bits.py](../src/gnss_tx/nav/nav_bits.py)
- [src/gnss_tx/ca/prn_generator.py](../src/gnss_tx/ca/prn_generator.py)

这条链路的关键特点是：

- Python 侧预生成整周期对齐的扩频 replay buffer。
- GNU Radio 侧循环回放复基带样本。
- UHD sink 将复基带持续送入 B210。
- QT 预览可作为软件侧观察入口。

`run_tx.py --dry-run` 已证明这条路径是当前仓库里最完整、最可验证、最适合作为工程主线的入口。

## GNU Radio Companion 的判断

[flowgraphs/gnss_tx_main.grc](../flowgraphs/gnss_tx_main.grc) 已被整理为：

- Ubuntu 虚拟机内可直接打开、可点击运行的 Companion 主流图。
- Python runtime 发射链的镜像入口。
- 面向 QT 预览、bring-up 和教学演示的辅助入口。

它的边界应写清楚：

- 它不是新的配置真源。
- 它不复制 PRN、nav bit 或 spreader 算法。
- 它继续复用 [grc/blocks/gnss_tx_gps_l1_ca_source.block.yml](../grc/blocks/gnss_tx_gps_l1_ca_source.block.yml) 和 Python 侧 `make_gps_l1_ca_vector_source()`。

当前 Companion 默认值已经固定为：

- `samples_per_chip = 4`
- `samp_rate = 4.092e6`
- `center_freq = 100e6`
- `tx_gain = 0.0`
- `amplitude = 1.0`
- `usrp_addr = "type=b200"`
- `nav_pattern = "1 0 1 1 0 0 1 0"`

这组值的目的不是替代 Python runtime 的安全基线文件，而是保证 Ubuntu 里直接点开 `.grc` 就能持续发射当前已实现的单星扩频 BPSK 复基带，并同时看到 QT 时域和频域预览。

## configs / tests / docs 的语义漂移

### 1. 安全基线配置曾被删失

[configs/tx_b210.yaml](../configs/tx_b210.yaml) 在当前 worktree 中一度缺失，直接导致：

- 测试中的安全基线断言失效。
- 文档中“默认低风险起点”的引用失真。
- 仓库缺少一个明确的 Python runtime 安全起步配置。

本次已经将它恢复为明确的安全基线：

- `tx_gain = 0.0`
- `amplitude = 0.25`

### 2. 当前可见谱配置与历史 checkpoint 已不完全相同

[configs/tx_b210_visible_spectrum.yaml](../configs/tx_b210_visible_spectrum.yaml) 当前 worktree 内配置为：

- `tx_gain = 10.0`
- `amplitude = 1.0`

而历史检查点 [experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md](../experiments/records/2026-03-22/tx_visibility_sweep/2026-03-22_prn1_visible_spectrum_checkpoint.md) 记录的是：

- `tx_gain = 10.0`
- `amplitude = 0.5`

这说明当前“可见谱配置”与“历史可见谱事实”之间仍存在参数漂移，尤其是幅度语义需要继续收敛。

### 3. GRC 默认值与 Python runtime 默认值属于不同层级

Companion 侧当前默认值定为：

- `tx_gain = 0.0`
- `amplitude = 1.0`

这是为了保证 Ubuntu 虚拟机内点击即跑和持续发射，而不是为了和 `tx_b210.yaml` 做数值一致。这里需要统一的不是“所有数字完全相同”，而是“每一组默认值分别服务什么用途”。

### 4. 启动方式此前不统一

此前仓库存在明显的入口不一致问题：

- 直接运行脚本时常需要手工加 `PYTHONPATH=src`。
- 直接跑 `unittest discover` 也会受 `src` 路径影响。

本次已经通过脚本入口 bootstrap、GRC 自定义块导入修复和根目录 `sitecustomize.py` 做了收敛。该问题本质上是“工程启动方式不统一”，不是信号链逻辑错误。

## 模块状态判断

### 已进入主链

- [src/gnss_tx/ca/prn_generator.py](../src/gnss_tx/ca/prn_generator.py)
- [src/gnss_tx/nav/nav_bits.py](../src/gnss_tx/nav/nav_bits.py)
- [src/gnss_tx/signal/spreader.py](../src/gnss_tx/signal/spreader.py)
- [src/gnss_tx/signal/iq_builder.py](../src/gnss_tx/signal/iq_builder.py)
- [src/gnss_tx/gr/top_block.py](../src/gnss_tx/gr/top_block.py)
- [src/gnss_tx/usrp/b210_sink.py](../src/gnss_tx/usrp/b210_sink.py)
- [src/gnss_tx/usrp/tx_controller.py](../src/gnss_tx/usrp/tx_controller.py)
- [src/gnss_tx/utils/io.py](../src/gnss_tx/utils/io.py)
- [scripts/run_tx.py](../scripts/run_tx.py)

### 已有实现但不是主链核心

- [src/gnss_tx/ca/resampler.py](../src/gnss_tx/ca/resampler.py)
- [src/gnss_tx/signal/modulator.py](../src/gnss_tx/signal/modulator.py)
- [flowgraphs/gnss_tx_main.grc](../flowgraphs/gnss_tx_main.grc)
- [scripts/analyze_prn1_spread.py](../scripts/analyze_prn1_spread.py)
- [scripts/plan_tx_visibility_sweep.py](../scripts/plan_tx_visibility_sweep.py)

其中 [flowgraphs/gnss_tx_main.grc](../flowgraphs/gnss_tx_main.grc) 不算空壳，但属于“需要重建和持续校验的镜像入口”。

### 空壳或占位

- [configs/gps_l1_ca.yaml](../configs/gps_l1_ca.yaml)
- [configs/lab_single_tone.yaml](../configs/lab_single_tone.yaml)
- [flowgraphs/single_tone_test.grc](../flowgraphs/single_tone_test.grc)
- [flowgraphs/two_tone_test.grc](../flowgraphs/two_tone_test.grc)
- [scripts/export_iq.py](../scripts/export_iq.py)
- [scripts/generate_nav.py](../scripts/generate_nav.py)
- [src/gnss_tx/nav/subframe_builder.py](../src/gnss_tx/nav/subframe_builder.py)
- [src/gnss_tx/utils/logging.py](../src/gnss_tx/utils/logging.py)
- [src/gnss_tx/utils/timebase.py](../src/gnss_tx/utils/timebase.py)

## experiments 目录说明与使用约定

[experiments](../experiments) 目录现在应承担两类职责：

- 保存阶段性实验事实。
- 保存当天的执行流程、扫描草稿和回填模板。

推荐理解方式如下：

- `checkpoint`
  - 写“已经验证通过的事实”，例如某一天频谱仪上确实看到了宽带包络。
- `draft`
  - 写当天实验计划和待回填内容。
- `checklist`
  - 面向现场执行，避免漏掉步骤。
- `archive`
  - 面向归档，总结当天做了什么、结论是什么、后续做什么。
- `observation_log_template`
  - 面向通用人工记录。

推荐流程：

1. 先跑 `run_tx.py --dry-run`。
2. 先做软件侧预览：
   - Python runtime 适合正式参数化运行。
   - GRC 适合 Ubuntu 里直接点开做 bring-up。
3. 再接频谱仪做 RF 观察。
4. 实验结束后把结果回写到 checkpoint、draft 和 archive。

## 下一阶段最优先的 5 个工程任务

1. 持续维护 [flowgraphs/gnss_tx_main.grc](../flowgraphs/gnss_tx_main.grc)，保证 Ubuntu 虚拟机中点击运行即可持续发射单星扩频 BPSK 复基带。
2. 明确并长期保持三套语义的边界：
   - `tx_b210.yaml` 是安全基线。
   - `tx_b210_visible_spectrum.yaml` 是当前 runtime 可见谱配置。
   - 历史 checkpoint 记录的是当时实验事实。
3. 补齐最小可用的单音校准工件，至少让 `lab_single_tone.yaml` 与实验流程不再断层。
4. 继续补强验证闭环，重点覆盖 replay 边界连续性、配置装载一致性、dry-run 与实验验收步骤。
5. 在单星可选 PRN 实验平台完全站稳后，再评估是否进入真实导航电文、多星和多普勒能力。

## 阶段判断

当前工程最适合继续收敛为“单星可选 PRN 扩频发送实验平台”。在这个阶段，清晰的主线、稳定的 Ubuntu 运行入口、可追溯的实验记录和一致的配置语义，比继续扩充完整 GNSS 功能更重要。
