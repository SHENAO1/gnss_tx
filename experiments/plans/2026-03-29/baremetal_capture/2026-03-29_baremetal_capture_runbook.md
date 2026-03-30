# 裸机 Ubuntu 线缆回环采集手册

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
git clone https://github.com/SHENAO1/GNSS_RX.git GNSS_RX
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

**gnss_tx 环境**（使用项目自带安装脚本）：

```bash
cd ~/projects/gnss_tx
bash env/ubuntu/setup.sh
# 脚本会创建 .venv，安装 requirements.txt，并以 editable 模式安装项目包
```

**GNSS_RX 环境**：

```bash
cd ~/projects/GNSS_RX
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pyyaml numpy
deactivate
```

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

接线之前先用 dry-run 确认配置无误：

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
PYTHONPATH=src python3 scripts/record_rx.py \
    --config configs/rx_baremetal.yaml --dry-run
```

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

---

## Step 10 — 主力机 MATLAB 导入

在主力机（Windows/Linux）上：

1. 将移动硬盘中的 `GNSS_RX_Data_baremetal/` 拷贝到本地 MATLAB 可访问路径
2. 编辑 `GNSS_RX/matlab/gnss_rx_user_paths.m`，将 `root_data_dir` 指向新路径
3. 在 MATLAB 中运行 `run_capture_analysis`
4. 验证输出结果：BER = 0.00e+00，tracked_match = 100%

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
