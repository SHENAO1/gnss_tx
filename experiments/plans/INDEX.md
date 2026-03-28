# Plans Index — gnss_tx 发射端

本文件是 `gnss_tx/experiments/plans/` 目录下计划文档的汇总索引，同时记录当前执行主线与跨项目关联。

---

## 进行中

| 文件 | 创建日期 | 描述 | 状态 |
|------|---------|------|------|
| [2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md](2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md) | 2026-03-26 | TX/RX 综合改进路线图（跨项目） | 持续更新 |
| [2026-03-28/ber_loopback_tx/2026-03-28_ber_loopback_tx_plan.md](2026-03-28/ber_loopback_tx/2026-03-28_ber_loopback_tx_plan.md) | 2026-03-27 | 当前 BER 发端主计划：稳定发射基线 + truth JSON 导出 + 长时实验配合 | `[~]` 当前执行主线 |

---

## 已完成 / 归档

| 文件 | 创建日期 | 描述 | 状态 |
|------|---------|------|------|
| [2026-03-27/tx_power_test/tx_power_test.md](2026-03-27/tx_power_test/tx_power_test.md) | 2026-03-27 | BER 前置的发射功率测试与安全确认 | `[x]` 已完成，结论已固化到后续 BER 基线 |

---

## 跨项目计划

| 计划名称 | 发射端（本项目） | 接收端（GNSS_RX） |
|---------|---------------|----------------|
| Milestone 1：BER 闭环验证 | [2026-03-28_ber_loopback_tx_plan.md](2026-03-28/ber_loopback_tx/2026-03-28_ber_loopback_tx_plan.md) | [2026-03-28_ber_loopback_rx_plan.md](../../GNSS_RX/experiments/plans/2026-03-28/ber_loopback_rx/2026-03-28_ber_loopback_rx_plan.md) |
| TX/RX 综合改进路线图 | [2026-03-26_tx_rx_improvement_plan.md](2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md) | [2026-03-26_tx_rx_improvement_plan.md](../../GNSS_RX/experiments/plans/2026-03-26/tx_rx_improvement/2026-03-26_tx_rx_improvement_plan.md) |

> 相对路径假设两个项目同级放置于 `~/projects/` 下。

---

## 更新日志

- **2026-03-28**：BER 发端文档已更新为 truth JSON 导出 + 稳定发射基线 + 长时实验配合的当前代码状态
- **2026-03-27**：新增 BER 闭环验证计划与发射功率测试文档，并统一收纳到 `plans/2026-03-27/<topic>/`
- **2026-03-26**：TX/RX 综合改进路线图收纳到 `plans/2026-03-26/tx_rx_improvement/`
