# PRN1 发射参数试验清单

## 实验前准备
- [ ] 确认 B210 已连接并可被 `uhd_find_devices` 识别
- [ ] 确认使用的配置文件正确
- [ ] 确认配置文件：`configs/tx_b210_visible_spectrum.yaml`
- [ ] 确认频谱仪输入阻抗为 `50 ohm`
- [ ] 确认同轴线连接在 B210 的 `TX/RX` 口
- [ ] 确认已启用前端保护，参考电平和输入衰减已设置

## 固定实验条件
- [ ] `center_freq = 100000000.0`
- [ ] `sample_rate = 4092000.0`
- [ ] `samples_per_chip = 4`
- [ ] `antenna = TX/RX`
- [ ] 使用同一台频谱仪、同一根线缆、同一组基础显示参数

## 推荐频谱仪设置
- [ ] `Center = 100 MHz`
- [ ] `Span = 5 MHz`
- [ ] `RBW = 1 kHz`
- [ ] `VBW = 1 kHz`
- [ ] `Att = 10 dB`
- [ ] `Ref Level = -66 dBm`

## 基准确认：先确认当天已知可见组合
### 组合：tx_gain=10, amplitude=0.50
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain 10 --amplitude 0.50 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 确认停止发射后包络消失
- [ ] 如基准点不稳定，先排查连线、频谱仪设置、underflow 和 `--qt-preview` 软件侧频谱
- [ ] 从终端复制“实验表格参数摘要”到实验表格

## 阶段1：先扫 tx_gain（固定 amplitude = 0.50，顺序 10→8→6）
### 组合：tx_gain=10, amplitude=0.50
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain 10 --amplitude 0.50 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 记录停止发射后是否消失
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 从终端复制“实验表格参数摘要”到实验表格
- [ ] 如有必要，保存截图并记录截图文件名
- [ ] 填写本组备注

### 组合：tx_gain=8, amplitude=0.50
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain 8 --amplitude 0.50 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 记录停止发射后是否消失
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 从终端复制“实验表格参数摘要”到实验表格
- [ ] 如有必要，保存截图并记录截图文件名
- [ ] 填写本组备注

### 组合：tx_gain=6, amplitude=0.50
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain 6 --amplitude 0.50 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 记录停止发射后是否消失
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 从终端复制“实验表格参数摘要”到实验表格
- [ ] 如有必要，保存截图并记录截图文件名
- [ ] 填写本组备注

## 阶段2：再扫 amplitude（固定阶段1选出的最小稳定 tx_gain，顺序 0.50→0.40→0.30）
### 组合：tx_gain=<阶段1选出的最小稳定tx_gain>, amplitude=0.50
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain <阶段1选出的最小稳定tx_gain> --amplitude 0.50 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 记录停止发射后是否消失
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 从终端复制“实验表格参数摘要”到实验表格
- [ ] 如有必要，保存截图并记录截图文件名
- [ ] 填写本组备注

### 组合：tx_gain=<阶段1选出的最小稳定tx_gain>, amplitude=0.40
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain <阶段1选出的最小稳定tx_gain> --amplitude 0.40 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 记录停止发射后是否消失
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 从终端复制“实验表格参数摘要”到实验表格
- [ ] 如有必要，保存截图并记录截图文件名
- [ ] 填写本组备注

### 组合：tx_gain=<阶段1选出的最小稳定tx_gain>, amplitude=0.30
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain <阶段1选出的最小稳定tx_gain> --amplitude 0.30 --duration 20`
- [ ] 观察 20 s 内是否始终能看到宽带包络
- [ ] 记录停止发射后是否消失
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 从终端复制“实验表格参数摘要”到实验表格
- [ ] 如有必要，保存截图并记录截图文件名
- [ ] 填写本组备注

## 阶段3：重复性验证（使用最终选定组合）
### 重复性验证 #1
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain <最终tx_gain> --amplitude <最终amplitude> --duration 20`
- [ ] 确认谱形是否与前两轮一致
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 记录是否存在漂移或偶发消失
- [ ] 如有必要，保存截图并记录截图文件名

### 重复性验证 #2
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain <最终tx_gain> --amplitude <最终amplitude> --duration 20`
- [ ] 确认谱形是否与前两轮一致
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 记录是否存在漂移或偶发消失
- [ ] 如有必要，保存截图并记录截图文件名

### 重复性验证 #3
- [ ] 运行发射命令：`PYTHONPATH=src python3 scripts/run_tx.py --config configs/tx_b210_visible_spectrum.yaml --tx-gain <最终tx_gain> --amplitude <最终amplitude> --duration 20`
- [ ] 确认谱形是否与前两轮一致
- [ ] 记录频谱仪结果：明显可见 / 勉强可见 / 不可见
- [ ] 记录稳定性：稳定 / 边缘 / 不稳定
- [ ] 记录是否存在漂移或偶发消失
- [ ] 如有必要，保存截图并记录截图文件名

## 实验结束后汇总
- [ ] 找出最低稳定可见的参数组合
- [ ] 找出最稳定、最容易复现的参数组合
- [ ] 更新实验记录草稿中的结果汇总
- [ ] 如需固化为新的默认实验配置，再决定是否更新配置文件