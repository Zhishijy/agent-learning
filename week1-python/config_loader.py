"""健壮的JSON配置加载器。

设计要点：
- 每种故障对应具体异常类型，禁止裸 except
- 加载和校验分离：load 负责"读到"，validate 负责"读对了"
- 损坏的配置绝不静默使用默认值，而是显式报错让调用方决策
- 全程 logging，不 print
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "timeout": 30,
}


class ConfigError(Exception):
    """配置相关错误的统一父类，调用方可以一次 catch 全部配置问题。"""


class ConfigFormatError(ConfigError):
    """文件存在，但内容不是合法JSON。"""


class ConfigValidationError(ConfigError):
    """JSON合法，但字段值不符合要求。"""


def validate_config(cfg: dict[str, Any]) -> None:
    """校验配置内容，有问题直接抛 ConfigValidationError。"""
    # 1. 类型必须是 dict（防止有人把配置写成一个列表或数字）
    if not isinstance(cfg, dict):
        raise ConfigValidationError(
            f"配置顶层必须是对象，实际是 {type(cfg).__name__}"
        )

    # 2. temperature：存在才校验，缺了用默认值补
    if "temperature" in cfg:
        t = cfg["temperature"]
        if not isinstance(t, (int, float)) or isinstance(t, bool):
            # 注意 bool 是 int 的子类，必须单独排除，否则 True 会蒙混过关
            raise ConfigValidationError(
                f"temperature 必须是数字，实际是 {t!r} ({type(t).__name__})"
            )
        if not 0 <= t <= 2:
            raise ConfigValidationError(
                f"temperature 合法范围为 0-2，实际为 {t}"
            )

    # 3. timeout：必须是正整数
    if "timeout" in cfg:
        to = cfg["timeout"]
        if not isinstance(to, int) or isinstance(to, bool) or to <= 0:
            raise ConfigValidationError(
                f"timeout 必须是正整数，实际为 {to!r}"
            )

    # 4. model：必须是非空字符串
    if "model" in cfg:
        m = cfg["model"]
        if not isinstance(m, str) or not m.strip():
            raise ConfigValidationError("model 必须是非空字符串")


def load_config(path: str) -> dict[str, Any]:
    """加载配置：文件不存在时返回默认配置；内容损坏时抛异常。"""
    p = Path(path)

    if not p.exists():
        logger.warning("配置文件 %s 不存在，使用默认配置", p)
        return dict(DEFAULT_CONFIG)  # 返回副本，防止外部改坏默认值

    try:
        raw = p.read_text(encoding="utf-8")
    except OSError as e:
        # 权限不足、文件被占用等系统级错误
        raise ConfigError(f"读取配置文件失败 {p}: {e}") from e

    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError as e:
        # 不吞掉错误：损坏的配置继续跑下去会造成更难查的问题
        raise ConfigFormatError(
            f"配置文件格式损坏（不是合法JSON）：{p}，第{e.lineno}行第{e.colno}列"
        ) from e  # from e：保留原始错误链，日志里能看到根因

    validate_config(cfg)

    # 缺省字段用默认值补齐，用户只需写想改的项
    merged = {**DEFAULT_CONFIG, **cfg}
    logger.info("配置加载成功：%s", merged)
    return merged


def save_config(path: str, cfg: dict[str, Any]) -> None:
    """保存配置，父目录不存在时自动创建。"""
    validate_config(cfg)  # 写入前先校验，脏数据不落盘

    p = Path(path)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(cfg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as e:
        raise ConfigError(f"保存配置文件失败 {p}: {e}") from e

    logger.info("配置已保存到 %s", p)