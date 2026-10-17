"""运行：python demo_config.py
观察四种场景下程序是否都按预期处理。"""

import logging
from pathlib import Path

from config_loader import (
    load_config, save_config,
    ConfigFormatError, ConfigValidationError, ConfigError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s | %(message)s",
)

base = Path("demo_tmp")
base.mkdir(exist_ok=True)

# 场景1：文件不存在 → 返回默认配置，不崩溃
print("\n=== 场景1：文件不存在 ===")
print(load_config(str(base / "missing.json")))

# 场景2：正常读写 + 目录自动创建
print("\n=== 场景2：保存并正常加载 ===")
save_config(str(base / "nested" / "config.json"),
            {"model": "qwen-max", "temperature": 0.3})
print(load_config(str(base / "nested" / "config.json")))

# 场景3：JSON 损坏
print("\n=== 场景3：JSON格式损坏 ===")
bad = base / "broken.json"
bad.write_text('{"model": "deepseek", ', encoding="utf-8")  # 少右括号
try:
    load_config(str(bad))
except ConfigFormatError as e:
    print(f"已捕获：{e}")

# 场景4：字段值非法（两个子场景）
print("\n=== 场景4：字段非法 ===")
for illegal in [
    {"temperature": "abc"},   # 类型错误
    {"temperature": 5},       # 超范围
    {"timeout": -1},          # 非正数
]:
    f = base / "illegal.json"
    f.write_text(json_dumps := __import__("json").dumps(illegal),
                 encoding="utf-8")
    try:
        load_config(str(f))
    except ConfigValidationError as e:
        print(f"输入 {illegal} → 已捕获：{e}")