# Plans Index — gnss_tx 发射端

本文件是 `gnss_tx/experiments/plans/` 目录下所有计划文档的汇总索引，同时记录跨项目计划关联和开发进展日志。

---

## 进行中

| 文件 | 创建日期 | 描述 | 状态 |
|------|---------|------|------|
| [2026-03-27/2026-03-27_ber_loopback_tx_plan.md](2026-03-27/2026-03-27_ber_loopback_tx_plan.md) | 2026-03-27 | Milestone 1 射频线直连闭环 BER 验证（发端视角） | `[ ]` 待执行 |

---

## 已完成 / 归档

_暂无_

---

## 跨项目计划（Cross-project）

以下计划需要 TX 和 RX 两端协作执行，点击可跳转到对应项目文档：

| 计划名称 | 发射端（本项目） | 接收端（GNSS_RX） |
|---------|---------------|----------------|
| Milestone 1：BER 闭环验证 | [2026-03-27_ber_loopback_tx_plan.md](2026-03-27/2026-03-27_ber_loopback_tx_plan.md) | [2026-03-27_ber_loopback_rx_plan.md](../../GNSS_RX/experiments/plans/2026-03-27/2026-03-27_ber_loopback_rx_plan.md) |
| TX/RX 综合改进路线图 | — | [2026-03-26_tx_rx_improvement_plan.md](../../GNSS_RX/experiments/plans/2026-03-26_tx_rx_improvement_plan.md) |

> **相对路径说明**：上表中 GNSS_RX 路径假设两个项目同级放置于 `~/projects/` 下。

---

## 更新日志

- **2026-03-27**：新建 `2026-03-27_ber_loopback_tx_plan.md`（发端闭环 BER 验证计划，对应 GNSS_RX 接收端计划）；发端代码无需修改，直接使用现有配置
