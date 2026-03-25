"""
GNSS TX 发射控制器模块

这个模块负责管理 GPS 信号发射的所有参数配置和硬件控制。主要功能包括：
1. 定义发射信号的运行时配置（采样率、频率、增益等）
2. 加载和验证 YAML 配置文件
3. 与 USRP B210 设备通信
4. 生成调试和实验报告
5. 构建 GNU Radio 发射链

核心类是 TxRuntimeConfig，用 @dataclass 装饰器定义发射参数的数据结构。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from pathlib import Path
import subprocess
from typing import Any

from gnss_tx.ca.prn_generator import SUPPORTED_PRN_IDS
from gnss_tx.gr.top_block import GpsL1CaTxTopBlock, TxBlockConfig
from gnss_tx.usrp.b210_sink import create_b210_sink
from gnss_tx.utils.io import load_yaml_file

# ============================================================================
# 常量定义 - 系统级的硬编码参数
# ============================================================================

# GPS L1 C/A 码的芯片率（码的重复速率）：每秒 102.3 万个码元
# 这个值决定了信号的基础时间尺度
GPS_CA_CHIP_RATE = 1.023e6

# 频谱分析仪的最大安全输入功率（以 dBm 为单位）
# 超过这个值会损伤设备，所以发射增益不能太大
SPECTRUM_ANALYZER_MAX_INPUT_DBM = 30.0

# 频谱分析仪的最大安全直流电压（以伏特为单位）
# 用于保护高阻抗输入通道
SPECTRUM_ANALYZER_MAX_DC_V = 50.0

# 频谱分析仪的默认观测频率范围（带宽）
# 从宽到窄依次尝试，帮助用户快速找到信号
DEFAULT_OBSERVATION_SPANS_HZ = (20e6, 10e6, 5e6, 2e6)


@dataclass(frozen=True)
class TxRuntimeConfig:
    """
    GPS L1 C/A 信号发射的运行时配置类
    
    使用 @dataclass(frozen=True) 装饰器，意味着：
    - 自动生成 __init__、__repr__ 等方法
    - 创建后不能修改属性（不可变对象，便于调试和缓存）
    
    属性分为五大类：
    1. 导航参数：定位信号的身份（PRN ID、导航数据模式）
    2. 信号模式：两种信号类型（扩频或单音）
    3. RF参数：硬件无线电相关（中心频率、增益、天线）
    4. 时序参数：码相位和导航初始化状态
    5. 运行控制：发射时长、实时预览等
    """
    
    # ========== 导航和模式参数 ==========
    # PRN ID（卫星伪随机码号，当前支持 GPS L1 C/A PRN1~32）
    prn_id: int = 1
    
    # 信号类型：
    #   "spread" - 扩频模式，真实的 GPS C/A 码信号（复杂，接近实际GPS信号）
    #   "tone"   - 单音模式，简单的单频正弦波（用于测试硬件和信号链）
    signal_mode: str = "spread"
    
    # ========== USRP 硬件参数 ==========
    # USRP 设备地址字符串
    # "type=b200" 表示连接第一个发现的 B200 设备
    # 可以用 "serial=<serial_number>" 指定具体设备
    usrp_addr: str = "type=b200"
    
    # 射频中心频率（单位：Hz）
    # GPS L1 C/A 码通常在 1575.42 MHz，但实验中可能使用不同频率
    # 例如 100 MHz 用于实验室环境或软件无线电开发
    center_freq: float = 100e6
    
    # ========== 采样和时序参数 ==========
    # 数字基带采样率（单位：样本/秒，即 Sps）
    # 这是 USRP DAC（数模转换器）的时钟速率
    # 对于扩频模式，必须严格等于 GPS_CA_CHIP_RATE * samples_per_chip
    # 例如：1.023e6 * 4 = 4.092e6 Sps
    sample_rate: float = 4.092e6
    
    # 每个码元（chip）对应的数字样本数（离散化程度）
    # 当从码片级跳转到采样级时，每个码片扩展为这么多个样本
    # 更高的值 = 更高的精度但计算量更大
    # 例如：samples_per_chip=4 意味着 1 chip 分成 4 个数字样本
    samples_per_chip: int = 4
    
    # ========== 功率和信号幅度 ==========
    # USRP TX 增益（单位：dB，通常 0-89）
    # None 表示使用设备默认值
    # 更高的增益 = 更强的信号功率输出
    # 前置警告：初始测试从最小增益开始！
    tx_gain: float | None = None
    
    # 基带信号幅度（0~1 范围）
    # 0.25 表示满幅的 25%，对应数字信号的量化范围
    # 小于 1.0 是为了防止数字化过程中的削波失真
    amplitude: float = 0.25
    
    # ========== 天线和带宽 ==========
    # USRP B210 天线选择（对于发射）
    # "TX/RX" 是双向天线（既能发也能收）
    antenna: str = "TX/RX"
    
    # 模拟前端带宽滤波器的宽度（单位：Hz）
    # None 表示自动设置为与采样率相同
    # 用于降低带外噪声和干扰
    bandwidth: float | None = None
    
    # ========== GPS 导航数据参数 ==========
    # 导航比特序列（以空格分隔的二进制串）
    # GPS 导航信息按每个 C/A 周期传输一个比特
    # 此处是示例数据："1 0 1 1 0 0 1 0"
    nav_pattern: str = "1 0 1 1 0 0 1 0"
    
    # ========== 单音模式参数（signal_mode=="tone" 时使用）==========
    # 相对于中心频率的单音偏移量（单位：Hz）
    # 例如 500 kHz 意味着实际发射频率 = center_freq + 500 kHz
    tone_offset_hz: float = 500e3
    
    # 单音缓冲时长（单位：秒）
    # 下载到 USRP 内存的单音信号片段有多长
    # 更长的缓冲 = 更长的连续发射时间
    tone_buffer_s: float = 0.1
    
    # ========== 用户界面和反馈 ==========
    # 是否启用 GNU Radio QT 图形界面
    # True 会显示实时信号频谱和波形，便于可视化调试
    # False 则以纯命令行模式运行（无 GUI 开销）
    enable_qt_preview: bool = False
    
    # ========== 运行时间控制 ==========
    # 发射持续时长（单位：秒）
    # None 表示连续发射（直到用户中止）
    # 设置具体值会限制发射时间，便于安全测试
    duration_s: float | None = None
    
    # 是否连续发射
    # True：无限期运行直到中止
    # False：受 duration_s 限制（在设置 duration_s 时自动变为 False）
    continuous: bool = True
    
    # ========== 初始同步参数 ==========
    # 初始码相位：从 PRN 周期中的哪个码元位置开始发射
    # 0 表示从周期起点开始
    # 用于与接收机同步或模拟不同的信号捕获场景
    initial_code_phase: int = 0
    
    # 初始导航 bit 内部的 C/A epoch 偏移
    # 调整导航比特流中的起始位置
    initial_nav_epoch: int = 0
    
    # 初始导航比特索引（从 nav_pattern 中的哪个比特开始）
    initial_nav_bit_index: int = 0

    def validate(self) -> "TxRuntimeConfig":
        """
        验证配置参数的有效性和一致性
        
        检查列表：
        1. 信号模式是否合法（只支持 "spread" 和 "tone"）
        2. PRN ID 是否在当前支持范围内（GPS L1 C/A PRN1~32）
        3. 采样和时序参数是否合理（> 0）
        4. 频率和增益是否在物理合理范围
        5. 幅度是否在正常的信号范围内
        6. 对于扩频模式，采样率必须严格等于 GPS_CA_CHIP_RATE * samples_per_chip
           否则码片到采样的时间对应关系会失真
        7. 对于单音模式，单音偏移必须在 ±sample_rate/2 范围内（奈奎斯特定理）
        
        返回：
            self - 如果所有验证通过
            
        抛出：
            ValueError - 参数无效
            ValueError - 参数无效（如 PRN 超出支持范围）
        """
        if self.signal_mode not in {"spread", "tone"}:
            raise ValueError("signal_mode must be one of: spread, tone.")
        if self.prn_id not in SUPPORTED_PRN_IDS:
            raise ValueError(
                f"prn_id must be in the supported GPS L1 C/A range "
                f"{SUPPORTED_PRN_IDS[0]}..{SUPPORTED_PRN_IDS[-1]}."
            )
        if self.samples_per_chip <= 0:
            raise ValueError("samples_per_chip must be > 0.")
        if self.center_freq <= 0:
            raise ValueError("center_freq must be > 0.")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be > 0.")
        if not 0.0 < self.amplitude <= 1.0:
            raise ValueError("amplitude must be in the range (0, 1].")
        if self.duration_s is not None and self.duration_s <= 0:
            raise ValueError("duration_s must be > 0 when provided.")
        if self.tone_buffer_s <= 0:
            raise ValueError("tone_buffer_s must be > 0.")
        if abs(self.tone_offset_hz) >= (self.sample_rate / 2.0):
            raise ValueError("tone_offset_hz must lie strictly within +/- sample_rate/2.")

        if self.signal_mode == "spread":
            # 扩频模式中，数字 sample 速率必须与 chip 速率严格匹配，
            # 否则 bit -> chip -> sample 的时间对应关系会失真。
            derived_rate = GPS_CA_CHIP_RATE * self.samples_per_chip
            if abs(self.sample_rate - derived_rate) > 1e-6:
                raise ValueError(
                    f"sample_rate must equal 1.023e6 * samples_per_chip ({derived_rate})."
                )
        return self

    def to_block_config(self) -> TxBlockConfig:
        """
        将运行时配置转换为 GNU Radio 块配置
        
        这个方法将 Python 数据类转换为 GNU Radio 流图块所需的格式。
        GNU Radio 块有自己的配置数据结构 TxBlockConfig，需要所有参数都被显式传递。
        
        返回：
            TxBlockConfig - GNU Radio 块的配置对象
        """
        return TxBlockConfig(
            prn_id=self.prn_id,
            signal_mode=self.signal_mode,
            samples_per_chip=self.samples_per_chip,
            amplitude=self.amplitude,
            nav_pattern=self.nav_pattern,
            tone_offset_hz=self.tone_offset_hz,
            tone_buffer_s=self.tone_buffer_s,
            center_freq=self.center_freq,
            sample_rate=self.sample_rate,
            tx_gain=self.tx_gain,
            bandwidth=self.bandwidth,
            antenna=self.antenna,
            usrp_addr=self.usrp_addr,
            enable_qt_preview=self.enable_qt_preview,
            initial_code_phase=self.initial_code_phase,
            initial_nav_epoch=self.initial_nav_epoch,
            initial_nav_bit_index=self.initial_nav_bit_index,
        )




# ============================================================================
# 配置加载和管理函数
# ============================================================================

def load_tx_runtime_config(path: str | Path) -> TxRuntimeConfig:
    """
    从 YAML 配置文件加载 TX 运行时配置
    
    工作流程：
    1. 读取 YAML 文件并解析为 Python 字典
    2. 智能派生缺失的参数：
       - 如果未提供 sample_rate 但提供了 samples_per_chip，
         则自动计算 sample_rate = GPS_CA_CHIP_RATE * samples_per_chip
       - 如果未提供 bandwidth，则自动设置为 sample_rate（全频带宽度）
    3. 创建 TxRuntimeConfig 对象并验证所有参数
    
    参数：
        path: YAML 配置文件的路径（可以是字符串或 Path 对象）
        
    返回：
        TxRuntimeConfig - 已验证的配置对象
        
    示例 YAML 文件：
        prn_id: 1
        signal_mode: spread
        samples_per_chip: 4    # sample_rate 会自动派生
        center_freq: 100e6
        tx_gain: 50
        amplitude: 0.25
    """
    raw = load_yaml_file(path)
    
    # 自动派生采样率（如果只提供了 samples_per_chip）
    if "sample_rate" not in raw and "samples_per_chip" in raw:
        raw["sample_rate"] = GPS_CA_CHIP_RATE * int(raw["samples_per_chip"])
    
    # 自动派生带宽（如果只提供了 sample_rate）
    if "bandwidth" not in raw and "sample_rate" in raw:
        raw["bandwidth"] = float(raw["sample_rate"])
    
    # 创建配置对象并验证
    return TxRuntimeConfig(**raw).validate()


def apply_overrides(config: TxRuntimeConfig, **overrides: Any) -> TxRuntimeConfig:
    """
    应用参数覆盖到已有配置
    
    用途：
    - 在命令行或程序运行时向基础配置添加或修改参数
    - 自动处理关联参数的更新和一致性
    
    工作原理：
    1. 收集所有非 None 的覆盖参数（None 表示"不修改"）
    2. 使用 dataclass.replace() 创建新的配置副本
    3. 自动处理关联参数：
       - 若更改 samples_per_chip，需要更新 sample_rate
       - 若更改 sample_rate，需要更新 bandwidth
       - 若设置 duration_s（有值），则 continuous 变为 False
    4. 验证最终配置
    
    参数：
        config: 基础配置对象（不会被修改）
        **overrides: 要覆盖的参数字典（关键字参数）
        
    返回：
        TxRuntimeConfig - 新的已验证配置对象
        
    示例：
        base_config = load_tx_runtime_config("base.yaml")
        # 覆盖采样率和发射增益
        new_config = apply_overrides(base_config, sample_rate=2e6, tx_gain=60)
        # 如果只修改 samples_per_chip，sample_rate 会自动更新
        new_config = apply_overrides(base_config, samples_per_chip=2)
    """
    # 第一步：筛选出所有非 None 的覆盖参数
    effective: dict[str, Any] = {}
    for key, value in overrides.items():
        if value is not None:
            effective[key] = value

    # 第二步：应用覆盖参数
    candidate = replace(config, **effective)
    
    # 第三步：处理派生参数——保持参数之间的一致性
    # 若用户只改变了 samples_per_chip（没有直接改 sample_rate），
    # 则需要自动更新 sample_rate
    if "sample_rate" not in effective and "samples_per_chip" in effective:
        candidate = replace(candidate, sample_rate=GPS_CA_CHIP_RATE * candidate.samples_per_chip)
    
    # 若改变了采样相关参数（samples_per_chip 或 sample_rate），
    # 则需要更新 bandwidth 保持一致
    if "bandwidth" not in effective and (
        "sample_rate" in effective or "samples_per_chip" in effective
    ):
        candidate = replace(candidate, bandwidth=candidate.sample_rate)
    
    # 若指定了有限的发射时长，则自动关闭连续模式
    if "duration_s" in effective:
        candidate = replace(candidate, continuous=False)

    return candidate.validate()


# ============================================================================
# 报告和格式化函数
# ============================================================================

def format_config_report(config: TxRuntimeConfig) -> str:
    """
    生成详细的配置参数报告（文本格式）
    
    用途：
    - 调试时显示完整的运行时配置
    - 记录实验日志
    - 确认设置正确性
    
    返回：
        多行字符串，包含所有配置参数和安全提醒
        
    示例输出：
        ============================================================
        GNSS TX Runtime Config
        ============================================================
        prn_id=1
        signal_mode=spread
        ... （所有参数）
        spectrum_analyzer_max_input=-30 dBm
        safety_reminder: start with minimum TX gain and low amplitude...
    """
    lines = [
        "=" * 60,
        "GNSS TX Runtime Config",
        "=" * 60,
    ]
    # 自动遍历所有数据类字段并格式化输出
    for key, value in asdict(config).items():
        lines.append(f"{key}={value}")
    lines.extend(
        [
            "",
            f"Spectrum analyzer max input: {SPECTRUM_ANALYZER_MAX_INPUT_DBM} dBm",
            f"Spectrum analyzer max DC   : {SPECTRUM_ANALYZER_MAX_DC_V} V",
            "Safety reminder            : start with minimum TX gain and low amplitude before connecting the analyzer.",
        ]
    )
    return "\n".join(lines)


def format_observation_checklist(config: TxRuntimeConfig) -> str:
    """
    生成频谱分析仪观测检查清单（用户友好的中英文混合）
    
    用途：
    - 指导用户如何安全和正确地使用频谱仪观测 GPS 发射信号
    - 11 步操作流程，从设备安全到信号捕获
    
    特点：
    - 根据配置自动填入具体的频率、时长等参数
    - 对扩频和单音模式提供不同的预期波形描述
    - 强调安全操作顺序和风险提醒
    
    返回：
        多行字符串，包含 11 步操作清单和安全限制
        
    注意事项：
    - 这是为了保护昂贵的频谱分析仪免受过度功率损害
    - 总是从最小增益和衰减开始
    - 循序渐进地增加功率
    """
    center_mhz = config.center_freq / 1e6
    sample_rate_mhz = config.sample_rate / 1e6
    span_labels = ", ".join(f"{span / 1e6:.0f} MHz" for span in DEFAULT_OBSERVATION_SPANS_HZ)
    
    # 根据信号类型计算期望的波形描述
    expected_waveform = (
        f"single calibration tone near {center_mhz + config.tone_offset_hz / 1e6:.3f} MHz"
        if config.signal_mode == "tone"
        else "continuous spread-spectrum signal, not a single-tone spike"
    )
    
    # 根据是否设置了时长来决定持续时间描述
    duration_text = (
        f"{config.duration_s:.1f} s"
        if config.duration_s is not None
        else "a short fixed-duration run is recommended for the first RF check"
    )

    lines = [
        "=" * 60,
        "Spectrum Analyzer Observation Checklist",
        "=" * 60,
        "1. Keep the transmitter stopped while configuring the analyzer.",
        "2. Configure the analyzer input for 50 ohm and keep front-end protection enabled.",
        "3. Start with a high reference level and input attenuation before connecting the cable.",
        f"4. Connect B210 port {config.antenna} to the analyzer with a coax cable.",
        f"5. Set analyzer center frequency to {center_mhz:.3f} MHz.",
        f"6. Use a wide span first ({span_labels}); then narrow once the signal is found.",
        "7. Start with wider RBW/VBW; reduce RBW only after the signal is clearly visible.",
        f"8. Expected TX waveform: {expected_waveform}.",
        f"9. Expected occupied bandwidth scale: on the order of the chip-rate sample stream ({sample_rate_mhz:.3f} Msps playback).",
        f"10. Run a first transmit capture for {duration_text}.",
        "11. Success criterion: the wideband signal appears during TX and disappears after TX stops.",
        "",
        f"Analyzer safety limits: {SPECTRUM_ANALYZER_MAX_INPUT_DBM} dBm max input, {SPECTRUM_ANALYZER_MAX_DC_V} V DC max.",
        "Do not increase tx_gain or amplitude until the first low-power observation is confirmed safe.",
    ]
    return "\n".join(lines)


def extract_uhd_device_field(device_report: str, field_name: str) -> str:
    """
    从 UHD 设备报告中提取特定字段的值
    
    工作原理：
    - UHD（USRP Hardware Driver）命令返回格式化的设备报告
    - 每行可能包含 "field_name: value" 的结构
    - 此函数按行搜索并提取匹配字段的值
    
    参数：
        device_report: 来自 uhd_find_devices 命令的字符串输出
        field_name: 要查找的字段名（例如 "serial"、"product"）
        
    返回：
        字段的值（字符串），若未找到则返回空字符串 ""
        
    示例：
        report = "serial: 30A74E9\\nproduct: B200"
        extract_uhd_device_field(report, "serial")  # 返回 "30A74E9"
    """
    prefix = f"{field_name}:"
    for line in device_report.splitlines():
        stripped = line.strip()
        if stripped.startswith(prefix):
            # 提取冒号后面的部分（去掉多余的空白）
            return stripped.split(":", maxsplit=1)[1].strip()
    return ""


def _signal_center_frequency_hz(config: TxRuntimeConfig) -> float:
    """
    计算实际的 RF 信号中心频率
    
    逻辑：
    - 对于 tone 模式：中心频率 + 单音偏移
    - 对于 spread 模式：就是配置中的中心频率
    
    这是一个私有函数（以下划线开头），仅供 format_lab_table_summary 使用
    """
    if config.signal_mode == "tone":
        return config.center_freq + config.tone_offset_hz
    return config.center_freq


def _signal_offset_frequency_hz(config: TxRuntimeConfig) -> float:
    """
    计算基带信号的偏移频率
    
    逻辑：
    - 对于 tone 模式：返回单音偏移
    - 对于 spread 模式：返回 0（没有额外偏移）
    
    这是一个私有函数，用于实验报告
    """
    if config.signal_mode == "tone":
        return config.tone_offset_hz
    return 0.0


def _signal_generation_label(config: TxRuntimeConfig) -> str:
    """
    生成中文标签描述信号生成方式
    
    返回：
    - "单音缓冲回放" for tone 模式
    - "PRN{n} C/A 扩频缓冲回放" for spread 模式
    
    这是一个私有函数，用于中文实验表格
    """
    if config.signal_mode == "tone":
        return "单音缓冲回放"
    return f"PRN{config.prn_id} C/A 扩频缓冲回放"


def format_lab_table_summary(config: TxRuntimeConfig, device_report: str = "") -> str:
    """
    生成中文实验表格参数摘要
    
    用途：
    - 为实验报告生成标准化的参数列表
    - 便于与 Excel/PDF 实验文档集成
    - 包含从配置提取的关键参数和硬件信息
    
    参数：
        config: 发射配置对象
        device_report: UHD 设备报告字符串（可选，用于提取 serial 号）
        
    返回：
        格式化的中文参数摘要（每行一个参数）
        
    包含的参数示例：
    - 发送信号类型（扩频/单音）
    - GNU Radio 流图和频谱显示状态
    - 采样率、射频中心频率、发射增益
    - USRP serial 号
    - 信号观测频率和基带偏移
    - 幅度和归一化状态
    """
    # 尝试从设备报告中提取 serial 号，如果失败则用配置中的地址
    serial = extract_uhd_device_field(device_report, "serial") or config.usrp_addr
    
    # 根据预览开关生成状态描述
    gr_flowgraph_field = "QT 预览开启" if config.enable_qt_preview else "不输出"
    gr_spectrum_field = "QT 频谱预览开启" if config.enable_qt_preview else "不输出"
    
    lines = [
        "=" * 60,
        "实验表格参数摘要",
        "=" * 60,
        f"发送信号类型={'扩频' if config.signal_mode == 'spread' else '单音'}",
        f"GNU Radio流图={gr_flowgraph_field}",
        f"GNU Radio频谱={gr_spectrum_field}",
        "频谱仪结果=手工填写",
        f"采样率={config.sample_rate}",
        f"射频中心频率={config.center_freq}",
        f"发射增益={config.tx_gain}",
        f"带宽={config.bandwidth}",
        f"serial={serial}",
        f"信号观测频率={_signal_center_frequency_hz(config)}",
        f"基带偏移频率={_signal_offset_frequency_hz(config)}",
        f"幅度={config.amplitude}",
        "是否归一化=是",
        "是否直流偏置=否",
        f"生成方式={_signal_generation_label(config)}",
    ]
    return "\n".join(lines)


# ============================================================================
# 硬件检测和交互函数
# ============================================================================

def uhd_find_devices_output() -> str:
    """
    执行 UHD 设备查找命令获取硬件信息
    
    工作原理：
    - 调用外部命令行工具 "uhd_find_devices"
    - 该工具扫描系统中所有连接的 USRP 设备
    - 收集 stdout 和 stderr（check=False 表示即使失败也继续）
    
    返回：
        命令的标准输出和错误输出拼接而成的字符串
        （包含设备列表、serial 号、型号等信息）
        
    常见输出格式：
        -- Device 0
        Device Address:
            		serial: 30A74E9
        			product: B200
    """
    completed = subprocess.run(
        ["uhd_find_devices"],
        check=False,
        capture_output=True,
        text=True,
    )
    return (completed.stdout + completed.stderr).strip()


def is_b210_available() -> bool:
    """
    检查系统中是否有可用的 B210 USRP 设备
    
    检查逻辑：
    1. 调用 uhd_find_devices_output() 获取设备列表
    2. 检查是否包含 "no uhd devices found"（小写，表示无设备）
    3. 检查是否至少包含一个 "device"（表示找到了某个设备）
    
    返回：
        True - 至少有一个 USRP 设备可用
        False - 没有找到任何设备
        
    用途：
    - 在启动 TX 前进行健康检查
    - 避免在没有硬件的情况下尝试初始化
    """
    output = uhd_find_devices_output()
    lowered = output.lower()
    return "no uhd devices found" not in lowered and "device" in lowered


def read_uhd_sink_sample_rate(sink) -> float | None:
    """
    从 USRP TX sink 对象读取实际采样率
    
    工作流程：
    1. 检查 sink 对象是否为 None（设备未初始化）
    2. 检查是否有 get_samp_rate() 方法（不同设备可能不支持）
    3. 尝试调用方法并转换为浮点数
    4. 捕获运行时错误（设备不支持此操作）
    
    参数：
        sink: USRP TX sink 对象（来自 GNU Radio）
        
    返回：
        float - 实际采样率（单位：样本/秒）
        None - 如果无法读取（设备不支持或未初始化）
        
    用途：
    - 验证 USRP 是否正确设置了采样率
    - 检测时钟漂移或硬件问题
    - 生成调试报告
    """
    if sink is None:
        return None

    getter = getattr(sink, "get_samp_rate", None)
    if getter is None:
        return None

    try:
        return float(getter())
    except (RuntimeError, TypeError, ValueError):
        return None


def format_uhd_tx_sample_rate_report(
    requested_sample_rate: float,
    sink,
    *,
    label: str = "USRP TX channel 0",
) -> str:
    """
    生成 USRP TX 采样率的详细对比报告
    
    用途：
    - 诊断采样率设置是否成功
    - 检测硬件与软件配置的不匹配
    - 显示实际采样率偏差（δ 和百分比）
    
    工作原理：
    1. 记录请求的采样率和对应的 samples_per_chip 值
    2. 尝试从硬件读取实际采样率
    3. 计算差值和百分比偏差
    4. 生成人类可读的报告
    
    参数：
        requested_sample_rate: 请求的采样率（Sps）
        sink: USRP TX sink 对象
        label: 报告中的标签（例如 "USRP TX channel 0"）
        
    返回：
        多行字符串，包含请求值、实际值和偏差分析
        
    示例输出：
        [INFO] USRP TX channel 0 requested sample rate : 4092000.000 Sps (4.092000 Msps)
        [INFO] USRP TX channel 0 actual sample rate    : 4092100.000 Sps (4.092100 Msps)
        [INFO] USRP TX channel 0 sample-rate delta     : +100.000 Sps (+0.002441%)
    """
    requested = float(requested_sample_rate)
    actual = read_uhd_sink_sample_rate(sink)
    requested_samples_per_chip = requested / GPS_CA_CHIP_RATE

    lines = [
        f"[INFO] {label} requested sample rate : {requested:.3f} Sps ({requested / 1e6:.6f} Msps)",
        f"[INFO] {label} requested samples/chip: {requested_samples_per_chip:.6f}",
    ]
    
    # 若无法读取实际采样率，输出警告
    if actual is None:
        lines.append(f"[WARN] {label} actual sample-rate readback is unavailable.")
        return "\n".join(lines)

    # 计算实际值与请求值的差异
    actual_samples_per_chip = actual / GPS_CA_CHIP_RATE
    delta = actual - requested
    delta_ratio = delta / requested if requested else 0.0
    lines.extend(
        [
            f"[INFO] {label} actual sample rate    : {actual:.3f} Sps ({actual / 1e6:.6f} Msps)",
            f"[INFO] {label} actual samples/chip   : {actual_samples_per_chip:.6f}",
            f"[INFO] {label} sample-rate delta     : {delta:+.3f} Sps ({delta_ratio:+.6%})",
        ]
    )
    return "\n".join(lines)


# ============================================================================
# 高级集成函数
# ============================================================================

def build_tx_top_block(config: TxRuntimeConfig) -> GpsL1CaTxTopBlock:
    """
    构建完整的 GNU Radio TX 发射链
    
    这是整个 TX 系统的关键集成点。
    
    工作流程：
    1. 将 TxRuntimeConfig 转换为 GNU Radio 块配置（TxBlockConfig）
    2. 创建 USRP B210 硬件 sink（模拟转换器和射频输出）
    3. 创建 GpsL1CaTxTopBlock（GNU Radio 流图顶层）
       - 包含信号生成（PRN 序列扩频或单音）
       - 导航数据编码
       - 采样率转换
       - 与硬件 sink 的连接
    
    返回：
        GpsL1CaTxTopBlock - 完整的 GNU Radio 流图对象
                          （准备好调用 start() 和 stop()）
        
    注意：
    - sink 创建时已建立硬件连接，可能开始初始化 USRP
    - 在调用此函数前，确保 USRP 已连接和识别
    - 返回的对象是可运行的流图，但尚未启动
    
    典型用法：
        config = load_tx_runtime_config("tx_config.yaml")
        top_block = build_tx_top_block(config)
        top_block.start()  # 开始发射
        # ... 运行一段时间 ...
        top_block.stop()   # 停止发射
    """
    # 先构造硬件 sink，再把 GNU Radio replay source 与其连接成完整发送链。
    sink = create_b210_sink(config.to_block_config())
    return GpsL1CaTxTopBlock(config=config.to_block_config(), sink_block=sink)


__all__ = [
    "DEFAULT_OBSERVATION_SPANS_HZ",
    "GPS_CA_CHIP_RATE",
    "SPECTRUM_ANALYZER_MAX_DC_V",
    "SPECTRUM_ANALYZER_MAX_INPUT_DBM",
    "TxRuntimeConfig",
    "apply_overrides",
    "build_tx_top_block",
    "extract_uhd_device_field",
    "format_config_report",
    "format_lab_table_summary",
    "format_observation_checklist",
    "format_uhd_tx_sample_rate_report",
    "is_b210_available",
    "load_tx_runtime_config",
    "read_uhd_sink_sample_rate",
    "uhd_find_devices_output",
]
