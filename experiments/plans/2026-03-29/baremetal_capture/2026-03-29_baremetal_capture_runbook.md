# 裸机 Ubuntu 线缆回环采集手册

> **注意**：本文件中代码块内的绝对路径（`/home/shen/...`）均为原始记录机器的路径。
> 在其他机器上复现时，请将 `/home/shen` 替换为实际 `$HOME`，并按实际数据目录调整。
>
> 创建时间：2026-03-29
> 目的：规避 VMware vCPU 抢占导致的 underflow/overflow，在裸机上获取有效 BER 基线
> 关联根因分析：[2026-03-29_underflow_overflow_root_cause_analysis.md](../ber_loopback_tx/2026-03-29_underflow_overflow_root_cause_analysis.md)
> 关联联合手册：[2026-03-28_ber_loopback_joint_runbook.md](../ber_loopback_tx/2026-03-28_ber_loopback_joint_runbook.md)
> 适用场景：闲置笔记本（裸机 Ubuntu），两块 B210 线缆直连，数据经移动硬盘转移至主力机 MATLAB

---

## 背景

2026-03-29 根因分析确认，VMware Hypervisor 的周期性 vCPU 抢占是 TX underflow / RX overflow 的首要原因。在同一次 vCPU 冻结中，TX 进程喂不上样本（underflow）与 RX 进程读不出样本（overflow）同步发生，两端时间戳误差仅在几百毫秒以内。

裸机运行彻底消除 Hypervisor 调度抖动，是获得真实有效 BER 基线的必要条件。

**预期结果**：采集全程零 `U`（TX underflow）、零 `O`（RX overflow），MATLAB 分析得到 BER = 0.00e+00。

---

## 冻结基线

与 VMware 环境保持完全一致，不改动任何信号参数：

| 参数 | 值 |
|------|----|
| TX 设备 | `serial=193982` |
| RX 设备 | `serial=8003272` |
| 中心频率 | 100 MHz |
| 采样率 | 4.092 Msps |
| TX 配置 | `configs/tx_b210_cable_loopback.yaml` |
| RX 配置 | `GNSS_RX/configs/rx_baremetal.yaml` |
| nav pattern | `1 0 1 1 0 0 1 0` |
| 采集时长 | 300 s（≈ 15,000 bit） |
| TX 增益 | 50 dB |

---

## Step 0 — 系统依赖安装

在笔记本 Ubuntu 终端执行：

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y gnuradio python3-gnuradio uhd-host python3-pip python3-venv git
```

下载 USRP 固件镜像（**必须执行，缺少固件 B210 无法枚举**）：

```bash
sudo uhd_images_downloader
```

验证 UHD 安装（此时不必插入 B210）：

```bash
uhd_find_devices
# 预期输出：No UHD Devices Found（正常，尚未插硬件）
```

---

## Step 1 — 代码转移

### 方式 A：Git clone（笔记本有网，推荐）

```bash
mkdir -p ~/projects
cd ~/projects
git clone --branch feat/prn-subset-tx https://github.com/SHENAO1/gnss_tx.git gnss_tx
git clone --branch feat/multi-prn-rx https://github.com/SHENAO1/GNSS_RX.git GNSS_RX
```

### 方式 B：移动硬盘拷贝（无网环境）

在主力机上，将两个项目目录完整拷贝到移动硬盘，然后在笔记本上：

```bash
# 挂载移动硬盘后
mkdir -p ~/projects
cp -r /media/$USER/<drive_name>/gnss_tx ~/projects/
cp -r /media/$USER/<drive_name>/GNSS_RX ~/projects/
```

---

## Step 2 — Python 虚拟环境

**gnss_tx 环境**（必须让虚拟环境继承系统 GNU Radio / UHD 包）：

```bash
cd ~/projects/gnss_tx

# 如果之前已经创建过普通 .venv，先删除后重建
rm -rf .venv
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r env/ubuntu/requirements.txt
pip install -e .

# 验证当前 .venv 能看到系统安装的 GNU Radio UHD 绑定
python3 -c "from gnuradio import uhd; print(uhd.__file__)"
deactivate
```

判断标准：

- 正确结果：命令成功返回，并打印出类似 `/usr/lib/python3/dist-packages/gnuradio/uhd/__init__.py` 的路径
- 错误结果：出现 `ModuleNotFoundError: No module named 'gnuradio'` 或 `ImportError: cannot import name 'uhd' from 'gnuradio'`
- `deactivate` 正常情况下不会有任何输出，这也是正常现象

正确输出示例：

```text
/usr/lib/python3/dist-packages/gnuradio/uhd/__init__.py
```

错误输出示例：

```text
Traceback (most recent call last):
  ...
ModuleNotFoundError: No module named 'gnuradio'
```

> 说明：Ubuntu 通过 `apt install python3-gnuradio uhd-host` 安装的 GNU Radio / UHD Python 绑定位于系统 `site-packages`。这里必须使用 `--system-site-packages` 创建 `gnss_tx/.venv`，否则 `scripts/run_tx.py` 会在创建 B210 sink 时报告 `RuntimeError: GNU Radio UHD bindings are not available.`
>
> 当前 `env/ubuntu/setup.sh` 已同步改为 `python3 -m venv --clear --system-site-packages .venv`，亦可直接使用该脚本完成 `gnss_tx` 环境搭建。

**GNSS_RX 环境**（真实 USRP 采集同样必须让虚拟环境继承系统 GNU Radio / UHD 包）：

```bash
cd ~/projects/GNSS_RX

# 推荐：直接使用项目自带安装脚本
bash env/ubuntu/setup.sh

# 或手动：
# rm -rf .venv
# python3 -m venv --system-site-packages .venv
# source .venv/bin/activate
# pip install --upgrade pip
# pip install -r env/ubuntu/requirements.txt
# pip install -e .
#
# 验证当前 .venv 能看到系统安装的 GNU Radio UHD 绑定
# python3 -c "from gnuradio import uhd; print(uhd.__file__)"
# deactivate
```

判断标准：

- 正确结果：命令成功返回，并打印出类似 `/usr/lib/python3/dist-packages/gnuradio/uhd/__init__.py` 的路径
- 错误结果：出现 `ModuleNotFoundError: No module named 'gnuradio'` 或 `ImportError: cannot import name 'uhd' from 'gnuradio'`
- `deactivate` 正常情况下不会有任何输出，这也是正常现象

> 说明：`GNSS_RX/scripts/record_rx.py` 也会导入 `from gnuradio import uhd`。因此 RX 不能只装 `numpy + pyyaml`；若使用普通 `venv`，真实采集时会因为看不到系统 GNU Radio/UHD 绑定而失败。

---

## Step 3 — 硬件验证

将两块 B210 通过 USB 3.0 接口插入笔记本：

```bash
# 确认两块 B210 均被枚举
uhd_find_devices
```

预期输出中应包含：
```
serial: 193982   ← TX B210
serial: 8003272  ← RX B210
```

判断重点：

- `uhd_find_devices` 能同时列出 `serial=193982` 和 `serial=8003272`，说明两块 B210 都已被 UHD 正常枚举
- `product: B210`、`type: b200` 属于正常识别结果
- `lsusb -t` 中两台设备显示为 `5000M`，说明当前工作在 USB 3.x 链路上，满足本实验带宽需求
- 若两台 B210 出现在同一个 root hub / xHCI controller 下，这是裸机笔记本上的常见情况，只要仍为 `5000M` 即可继续实验
- `Driver=[none]` 对 B210 属于正常现象；UHD 通常通过用户态 `libusb` 访问设备，这里不显示专用内核驱动并不表示异常

通过示例特征：

```text
uhd_find_devices
  serial: 193982
  serial: 8003272

lsusb -t
  Port 002 ... 5000M
  Port 003 ... 5000M
```

需要停下来排查的情况：

- `uhd_find_devices` 只看到一台设备，或完全看不到设备
- `lsusb -t` 中 B210 只显示为 `480M`，说明掉到了 USB 2.0
- `uhd_find_devices` 报错或无法区分两台设备 serial
- 后续 `TX/RX dry-run` 仍提示找不到 UHD 设备或 GNU Radio/UHD 绑定

检查 USB 拓扑（了解是否共享 Controller）：

```bash
lsusb -t
```

> 说明：笔记本若只有一个 xhci controller，两块 B210 会在同一 Bus 下。这在裸机上不是问题——USB 带宽本身充裕（两路合计 ~65 MB/s，USB 3.0 上限约 300 MB/s），裸机无 vCPU 抢占，实时性由硬件保证。

---

## Step 4 — 配置说明

RX 线缆回环配置已为裸机环境新建了 `GNSS_RX/configs/rx_baremetal.yaml`，与 `rx_cable_loopback.yaml` 唯一的区别是 `output_base_dir` 指向本地目录（而非 VMware 共享目录）：

```yaml
output_base_dir: "/home/shen/GNSS_RX_Data"
```

其余所有参数（serial、center_freq、sample_rate、duration_s、nav_pattern 等）与 VMware 基线完全一致。

> 若笔记本用户名不是 `shen`，通过 CLI 覆盖：
> ```bash
> PYTHONPATH=src python3 scripts/record_rx.py \
>     --config configs/rx_baremetal.yaml \
>     --output-base-dir /home/<your_user>/GNSS_RX_Data
> ```

---

## Step 5 — 干运行验证

接线之前先确认 TX / RX 虚拟环境和 dry-run 都正常：

**TX 环境预检**：
```bash
cd ~/projects/gnss_tx
source .venv/bin/activate
python3 -c "from gnuradio import uhd; print(uhd.__file__)"
```

若这里报 `ModuleNotFoundError`，说明 `gnss_tx/.venv` 不是按 Step 2 的 `--system-site-packages` 方式创建的，需要回到 Step 2 重建。

**TX dry-run**：
```bash
cd ~/projects/gnss_tx
source .venv/bin/activate
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 50 --amplitude 1.0 --dry-run
```

**RX dry-run**：
```bash
cd ~/projects/GNSS_RX
source .venv/bin/activate
python3 -c "from gnuradio import uhd; print(uhd.__file__)"
PYTHONPATH=src python3 scripts/record_rx.py \
    --config configs/rx_baremetal.yaml --dry-run
```

若这里报 `ModuleNotFoundError`，说明 `GNSS_RX/.venv` 不是按 Step 2 的 `--system-site-packages` 方式创建的，需要回到 Step 2 重建。

确认 RX 输出路径中 `output_base_dir` 显示为本地目录，无任何配置报错后再进行下一步。

---

## Step 6 — 线缆接线

```
TX B210 (serial=193982)  TX/RX 端口
              │
         [推荐 20~30 dB 固定衰减器]
              │
         [同轴线缆]
              │
RX B210 (serial=8003272) RX2 端口
```

> **功率参考**：`tx_gain=50` 无衰减器时 P_rx ≈ −17 dBm，`rx_gain_db=20` 安全可用。
> 若有 20 dB 衰减器，P_rx ≈ −37 dBm，可适当提高 `rx_gain_db` 以补偿。

---

## Step 7 — 联机采集

打开两个终端，按顺序执行：

> 注意：终端 1 必须使用 Step 2 中按 `--system-site-packages` 重建后的 `~/projects/gnss_tx/.venv`。若误用了普通 `venv`，会再次报 `GNU Radio UHD bindings are not available.`

**终端 1 — 先启动 TX（duration 多给 60 s 裕量）**：

```bash
cd ~/projects/gnss_tx && source .venv/bin/activate
PYTHONPATH=src python3 scripts/run_tx.py \
    --config configs/tx_b210_cable_loopback.yaml \
    --tx-gain 50 --amplitude 1.0 --duration 360
```

**终端 2 — TX 启动约 5 秒后启动 RX**：

```bash
cd ~/projects/GNSS_RX && source .venv/bin/activate
PYTHONPATH=src python3 scripts/record_rx.py \
    --config configs/rx_baremetal.yaml
```

---

## Step 8 — 采集结果验证

RX 采集完成后（约 300 s），检查输出文件：

```bash
ls -lh ~/GNSS_RX_Data/2026/2026_03_*/*/
```

预期看到一对 `.sc16` + `.json` 文件。文件大小参考：

```
300 s × 4,092,000 sps × 4 B/sample ≈ 4.9 GB（.sc16 文件）
```

**关键验收条件**：回看两个终端的输出，确认：
- TX 终端：全程无 `U` 字符（即零 underflow）
- RX 终端：全程无 `O` 字符（即零 overflow）

只有满足此条件的采集数据才计入有效 BER 样本。

---

## Step 9 — 数据转移至移动硬盘

```bash
# 插入移动硬盘，确认挂载点
lsblk
ls /media/$USER/

# 拷贝采集数据（含 .sc16 和 .json）
cp -r ~/GNSS_RX_Data/ /media/$USER/<drive_name>/GNSS_RX_Data_baremetal/

# 确保写盘完成再拔出硬盘
sync
```

若移动硬盘目录名包含空格（例如本机实测挂载名为 `Seagate Basic`），命令必须加引号。当前这台机器可直接使用：

```bash
cp -r ~/GNSS_RX_Data/ "/media/$USER/Seagate Basic/GNSS_RX_Data_baremetal/"
sync
```

也可以先确认目标目录存在，再执行复制：

```bash
ls "/media/$USER/Seagate Basic"
cp -r ~/GNSS_RX_Data/ "/media/$USER/Seagate Basic/GNSS_RX_Data_baremetal/"
sync
```

> 注意：`<drive_name>` 是占位符，不能原样输入。若直接写成 `/media/$USER/<drive_name>/...`，shell 会把 `<` 解析为重定向符号，从而报 `bash: drive_name: 没有那个文件或目录`。

---

## Step 10 — 主力机 MATLAB 导入

在主力机（Windows/Linux）上：

1. 将移动硬盘中的 `GNSS_RX_Data_baremetal/` 拷贝到本地 MATLAB 可访问路径
2. 编辑 `GNSS_RX/matlab/gnss_rx_user_paths.m`，将 `GNSS_RX_DATA_DIR` 指向新路径
3. 在 MATLAB 中运行 `run_capture_analysis`
4. 验证输出结果：BER = 0.00e+00，tracked_match = 100%

通用步骤说明：

- 建议先将 `GNSS_RX_Data_baremetal/` 整个目录从移动硬盘复制到 Windows 本地 SSD，再启动 MATLAB；不建议直接从移动硬盘分析大体积 `.sc16` 文件
- 复制时保持原有目录层级不变，例如 `2026/2026_03_30/<stem>/` 这一层级应完整保留
- MATLAB 代码目录与数据目录建议分开管理：前者用于运行脚本，后者专门存放 `.sc16 + .json` 采集文件
- `run_capture_analysis()` 在不传参时，会从 `gnss_rx_user_paths.m` 指定的数据根目录中自动查找“最新一组完整采集文件对”

本机示例目录规划（Windows 主力机）：

```text
C:\VMwareVirtualMachines\GongXiangDocument\
├── GNSS_RX_matlab\
└── GNSS_RX_Data_baremetal\
```

说明：

- `GNSS_RX_matlab`：MATLAB 工作区 / 部署镜像目录
- `GNSS_RX_Data_baremetal`：本次裸机采集数据导入后的本地数据根目录
- 若移动硬盘中已经包含 `GNSS_RX_Data_baremetal/`，直接整体复制到 `C:\VMwareVirtualMachines\GongXiangDocument\` 下即可

`gnss_rx_user_paths.m` 配置示例：

- 若 `gnss_rx_user_paths.m` 不存在，先从 `gnss_rx_user_paths.m.example` 复制生成
- 修改位置：`C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab\gnss_rx_user_paths.m`

```matlab
GNSS_RX_DATA_DIR = 'C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_Data_baremetal';
```

MATLAB 启动与运行示例：

```matlab
cd('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab')
result = run_capture_analysis();
```

说明：

- 不传参时，MATLAB 会从 `GNSS_RX_DATA_DIR` 指向的根目录中自动分析“最新采集”
- 若希望强制分析本次裸机采集，可显式传入 stem 路径：

```matlab
result = run_capture_analysis( ...
  'C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_Data_baremetal\2026\2026_03_30\20260330_025519_rawiq_sc16_zeroif_prn1_spread_sr4092000_cf100000000_dur300p0s\20260330_025519_rawiq_sc16_zeroif_prn1_spread_sr4092000_cf100000000_dur300p0s');
```

检查要点：

- `GNSS_RX_DATA_DIR` 已指向 `GNSS_RX_Data_baremetal`
- 目标目录下 `.sc16` 与 `.json` 文件同名成对存在
- MATLAB 成功生成 `analysis/<stem>/` 目录
- 输出包含 `analysis_summary.json`、`analysis_summary.mat` 和 PNG 图
- 最终验收目标仍为 `BER = 0.00e+00`、`tracked_match = 100%`

若希望将移动硬盘直接连接到 Windows 主力机并原地分析，也可以使用“移动硬盘直读”方式：

- 适用场景：临时验证结果、避免先复制 4.6 GB 以上的大文件到本地 SSD
- 注意事项：分析过程中不要拔出移动硬盘；若盘符变化（例如不再是 `F:`），需同步修改路径
- 性能建议：可直接运行，但稳定性和速度通常仍不如先复制到本地 SSD

按本机当前实测挂载，移动硬盘数据根目录可写为：

```text
F:\GNSS_RX_Data_baremetal
```

当前这次裸机采集的 stem 路径可写为：

```text
F:\GNSS_RX_Data_baremetal\2026\2026_03_30\20260330_025519_rawiq_sc16_zeroif_prn1_spread_sr4092000_cf100000000_dur300p0s\20260330_025519_rawiq_sc16_zeroif_prn1_spread_sr4092000_cf100000000_dur300p0s
```

若希望 MATLAB 默认从移动硬盘中自动分析“最新采集”，可将 `gnss_rx_user_paths.m` 改为：

```matlab
GNSS_RX_DATA_DIR = 'F:\GNSS_RX_Data_baremetal';
```

然后在 MATLAB 中运行：

```matlab
cd('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab')
result = run_capture_analysis();
```

若只想强制分析本次移动硬盘中的裸机采集，可直接传入显式 stem 路径：

```matlab
cd('C:\VMwareVirtualMachines\GongXiangDocument\GNSS_RX_matlab')
result = run_capture_analysis( ...
  'F:\GNSS_RX_Data_baremetal\2026\2026_03_30\20260330_025519_rawiq_sc16_zeroif_prn1_spread_sr4092000_cf100000000_dur300p0s\20260330_025519_rawiq_sc16_zeroif_prn1_spread_sr4092000_cf100000000_dur300p0s');
```

---

## 验收清单

- [ ] `uhd_find_devices` 枚举到两块 B210（serial=193982 + serial=8003272）
- [ ] TX dry-run 无报错
- [ ] RX dry-run 无报错，`output_base_dir` 指向本地路径
- [ ] TX 终端全程无 `U`（underflow）
- [ ] RX 终端全程无 `O`（overflow）
- [ ] `.sc16` 文件大小约 4.9 GB，`.json` 文件存在且可读
- [ ] 数据已拷贝到移动硬盘并执行 `sync`
- [ ] MATLAB：BER = 0.00e+00，tracked_match = 100%
