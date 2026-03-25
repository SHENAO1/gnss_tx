# GNSS_TX Git 与开发工作流

本文件用于固定当前仓库的 Git 管理方式、生成文件约定与提交流程。

## 1. 分支职责

- `main`
  - 只保存可复现、已验证的稳定版本。
  - 不直接承载实验性开发。
- `feat/single-sat-selectable-prn`
  - 当前 GNSS TX 主开发分支。
  - 单星可选 `PRN1~32` 的发射链、GRC、USRP 相关日常开发统一落在这里。
- `feat/prn1-tx-spectrum`
  - 历史固定 PRN1 开发分支。
  - 作为本轮可选 PRN 改造前的演进背景保留，不再作为当前主线。
- `backup/2026-03-25-prn1-fixed-single-sat`
  - 固定 PRN1 发送版本的留档分支。
  - 用于回看“改造前可捕获的 PRN1 基线”。
- `backup/YYYY-MM-DD-*`
  - 只用于保存阶段快照、实验前备份或高风险改动前的存档。
  - 推送到远端后默认冻结，不继续作为日常开发主线。
- 短命开发分支
  - 从 `feat/single-sat-selectable-prn` 切出，例如 `feat/grc-launcher-refine`、`fix/usrp-runtime-check`。
  - 完成后尽快回合到 `feat/single-sat-selectable-prn`。

## 2. 提交约定

- 正式开发提交统一使用：`feat:`、`fix:`、`docs:`、`test:`、`chore:`。
- `wip:` 仅允许出现在 `backup/*` 快照分支。
- 文档、实验记录、运行链行为变化尽量拆分提交，不要混在同一个 commit 中。

## 3. GRC 与生成文件约定

- `flowgraphs/gnss_tx_main.grc` 是主流图的唯一源文件。
- `flowgraphs/gnss_tx_main.py` 与根目录 `gnss_tx_main.py` 视为受控衍生物，当前阶段继续纳入版本控制。
- 只要 `flowgraphs/*.grc` 或 `grc/blocks/*.block.yml` 发生变化，同一提交内必须同步更新对应生成文件。
- 如果两个生成 Python 文件内容不一致，不应提交。

## 4. 提交前最低验证

### 普通 Python 逻辑改动

```bash
python3 -m unittest discover -s tests
env PYTHONPATH=src python3 scripts/quick_check.py
```

### 涉及 GRC / 自定义 block / USRP 运行链改动

```bash
python3 -m unittest discover -s tests
env PYTHONPATH=src python3 scripts/quick_check.py
env GRC_BLOCKS_PATH=/usr/share/gnuradio/grc/blocks:$PWD/grc/blocks grcc flowgraphs/gnss_tx_main.grc
python3 scripts/run_tx.py --dry-run --config configs/tx_b210.yaml
```

- 如硬件可用，可额外做一次短时 B210 smoke test。
- 与硬件发射链相关的提交，应在 commit 描述、实验记录或 PR 描述中写明至少一条验证命令或验证结论。

## 5. 推荐日常流程

1. 日常开发从 `feat/single-sat-selectable-prn` 或其短命子分支开始。
2. 修改 `.grc` 或 block 模板后，立即同步更新生成 Python 文件。
3. 运行最低验证命令。
4. 使用正式前缀提交。
5. 完成一个清晰阶段后推送远端。
6. 只有在需要保留快照时，才新建并推送 `backup/*` 分支。

## 6. 合并到 main 的条件

- 软件测试通过。
- GRC 编译通过。
- 关键运行脚本可用。
- 至少保留一条最近的硬件验证记录或实验记录，能够追溯当前状态。
