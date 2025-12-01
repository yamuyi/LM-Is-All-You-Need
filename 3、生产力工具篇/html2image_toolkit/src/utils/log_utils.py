from loguru import logger
import os
from pathlib import Path

# 日志目录
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 配置日志
logger.add(
    LOG_DIR / "app.log",
    rotation="500 MB",  # 日志文件大小限制
    retention="7 days",  # 日志保留时间
    compression="zip",  # 压缩旧日志
    encoding="utf-8",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
)

# 导出logger实例
__all__ = ["logger"]