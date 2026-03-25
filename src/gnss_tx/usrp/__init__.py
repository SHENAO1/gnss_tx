"""USRP 相关公共接口导出。

该模块作为 `gnss_tx.usrp` 子包入口，统一重导出 B210 下沉层与
发射控制层的常用常量、配置类型和辅助函数，便于外部以稳定路径导入。
"""

from gnss_tx.usrp.b210_sink import HAVE_UHD, create_b210_sink
from gnss_tx.usrp.tx_controller import (
    GPS_CA_CHIP_RATE,  # GPS L1 C/A 码片速率（chips/s），用于采样率换算。
    SPECTRUM_ANALYZER_MAX_DC_V,  # 频谱仪输入端允许的最大直流电压上限。
    SPECTRUM_ANALYZER_MAX_INPUT_DBM,  # 频谱仪输入端允许的最大射频功率上限。
    TxRuntimeConfig,  # 发射运行配置数据类，集中管理 TX 参数并做校验。
    apply_overrides,  # 在基础配置上应用运行时覆盖项并保持字段联动一致。
    build_tx_top_block,  # 按配置构建完整 GNU Radio 发射 top block。
    format_config_report,  # 生成运行配置文本报告（用于启动前核对）。
    format_lab_table_summary,  # 生成实验表格填写摘要。
    format_observation_checklist,  # 生成频谱仪观测步骤清单与安全提示。
    format_uhd_tx_sample_rate_report,  # 输出请求/实际采样率及偏差报告。
    is_b210_available,  # 检测当前环境是否发现可用 UHD/B210 设备。
    load_tx_runtime_config,  # 从 YAML 加载配置并补齐默认联动字段。
    read_uhd_sink_sample_rate,  # 从 UHD sink 读回当前采样率（失败返回 None）。
    uhd_find_devices_output,  # 调用 uhd_find_devices 并返回原始输出文本。
)

# 显式声明公共 API，避免 `from ... import *` 时泄露内部符号。
__all__ = [
    "GPS_CA_CHIP_RATE",
    "HAVE_UHD",
    "SPECTRUM_ANALYZER_MAX_DC_V",
    "SPECTRUM_ANALYZER_MAX_INPUT_DBM",
    "TxRuntimeConfig",
    "apply_overrides",
    "build_tx_top_block",
    "create_b210_sink",
    "format_config_report",
    "format_lab_table_summary",
    "format_observation_checklist",
    "format_uhd_tx_sample_rate_report",
    "is_b210_available",
    "load_tx_runtime_config",
    "read_uhd_sink_sample_rate",
    "uhd_find_devices_output",
]
