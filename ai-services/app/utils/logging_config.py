# app/utils/logging_config.py

import logging
import sys
from datetime import datetime
from typing import Optional

# 日志颜色（用于控制台）
class LogColors:
    """ANSI颜色代码，用于控制台日志高亮"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器"""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.colors = {
            logging.DEBUG: LogColors.BLUE,
            logging.INFO: LogColors.GREEN,
            logging.WARNING: LogColors.YELLOW,
            logging.ERROR: LogColors.RED,
            logging.CRITICAL: LogColors.RED + LogColors.WHITE,
        }
    
    def format(self, record):
        """格式化日志记录，添加颜色"""
        # 添加级别颜色
        level_color = self.colors.get(record.levelno, LogColors.RESET)
        record.levelname = f"{level_color}{record.levelname}{LogColors.RESET}"
        
        # 添加时间戳颜色
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        record.asctime = f"{LogColors.GRAY}{timestamp}{LogColors.RESET}"
        
        # 添加模块名颜色
        record.name = f"{LogColors.CYAN}{record.name}{LogColors.RESET}"
        
        return super().format(record)


class RequestIDFilter(logging.Filter):
    """日志过滤器，添加request_id到日志记录"""
    
    def filter(self, record):
        """为日志记录添加request_id属性"""
        # 如果记录已经有request_id，保留它
        if not hasattr(record, 'request_id'):
            record.request_id = 'N/A'
        return True


class LoggerAdapter(logging.LoggerAdapter):
    """日志适配器，自动添加request_id到extra参数"""
    
    def __init__(self, logger: logging.Logger, extra: Optional[dict] = None):
        super().__init__(logger, extra or {})
    
    def process(self, msg, kwargs):
        """处理日志消息，添加request_id"""
        # 从extra中获取request_id
        request_id = self.extra.get('request_id', 'N/A') if self.extra else 'N/A'
        
        # 如果kwargs中有extra，合并
        if 'extra' in kwargs:
            kwargs['extra']['request_id'] = request_id
        else:
            kwargs['extra'] = {'request_id': request_id}
        
        return msg, kwargs


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_colors: bool = True
) -> None:
    """
    配置统一日志系统
    
    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: 日志文件路径（可选），例如: logs/app.log
        enable_colors: 是否启用颜色输出
    
    Example:
        >>> setup_logging(log_level="DEBUG", log_file="logs/app.log")
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("应用启动成功")
    """
    
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除已有的处理器（避免重复）
    root_logger.handlers.clear()
    
    # 日志格式
    # [时间] [级别] [模块:行号] [请求ID] 消息内容
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] [req_id:%(request_id)s] %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # ============================================================
    # 1. 控制台处理器（带颜色）
    # ============================================================
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    if enable_colors:
        console_formatter = ColoredFormatter(log_format, date_format)
    else:
        console_formatter = logging.Formatter(log_format, date_format)
    
    console_handler.setFormatter(console_formatter)
    
    # 添加request_id过滤器
    console_handler.addFilter(RequestIDFilter())
    
    root_logger.addHandler(console_handler)
    
    # ============================================================
    # 2. 文件处理器（如果指定）
    # ============================================================
    if log_file:
        try:
            # 确保日志目录存在
            import os
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_formatter = logging.Formatter(log_format, date_format)
            file_handler.setFormatter(file_formatter)
            
            # 添加request_id过滤器
            file_handler.addFilter(RequestIDFilter())
            
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            # 如果文件创建失败，记录错误但继续运行
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.WARNING)
            console_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
            console_handler.emit(
                logging.LogRecord(
                    name="logging_config",
                    level=logging.WARNING,
                    pathname="",
                    lineno=0,
                    msg=f"⚠️ 日志文件创建失败: {e}，仅输出到控制台",
                    args=(),
                    exc_info=None
                )
            )
    
    # ============================================================
    # 3. 设置第三方库日志级别（减少噪音）
    # ============================================================
    # 第三方HTTP库
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    # OpenAI SDK
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # FastAPI/Uvicorn 相关
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # SQLAlchemy
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # ============================================================
    # 4. 记录启动信息
    # ============================================================
    logger = logging.getLogger(__name__)
    
    # 创建一条不含request_id的启动日志
    # 使用简单的格式化器避免过滤器干扰
    logger.info(f"✅ 日志系统初始化完成 - 级别: {log_level}")
    if log_file:
        logger.info(f"📁 日志文件: {log_file}")
    
    # 记录系统信息
    import platform
    logger.debug(f"系统: {platform.system()} {platform.release()}")
    logger.debug(f"Python版本: {platform.python_version()}")


def get_logger(name: str) -> logging.Logger:
    """
    获取日志记录器（便捷函数）
    
    Args:
        name: 日志记录器名称，通常使用 __name__
    
    Returns:
        配置好的日志记录器实例
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条日志")
    """
    return logging.getLogger(name)


def get_logger_with_request_id(
    name: str,
    request_id: Optional[str] = None
) -> logging.LoggerAdapter:
    """
    获取带有request_id的日志适配器
    
    Args:
        name: 日志记录器名称
        request_id: 请求ID（可选）
    
    Returns:
        日志适配器，自动为每条日志添加request_id
    
    Example:
        >>> logger = get_logger_with_request_id(__name__, "req-123")
        >>> logger.info("处理请求")  # 自动包含request_id
    """
    logger = logging.getLogger(name)
    return LoggerAdapter(logger, {"request_id": request_id or "N/A"})


def get_logger_from_request(
    name: str,
    request: Optional['fastapi.Request'] = None
) -> logging.LoggerAdapter:
    """
    从FastAPI请求对象获取带有request_id的日志适配器
    
    Args:
        name: 日志记录器名称
        request: FastAPI请求对象
    
    Returns:
        日志适配器
    
    Example:
        >>> @app.get("/test")
        >>> async def test(request: Request):
        ...     logger = get_logger_from_request(__name__, request)
        ...     logger.info("处理请求")  # 自动包含request_id
    """
    logger = logging.getLogger(name)
    
    if request and hasattr(request.state, "request_id"):
        request_id = request.state.request_id
    else:
        request_id = "N/A"
    
    return LoggerAdapter(logger, {"request_id": request_id})


# ============================================================
# 便捷函数 - 快速获取不同级别的日志记录器
# ============================================================

def get_debug_logger(name: str) -> logging.Logger:
    """获取调试日志记录器"""
    logger = get_logger(name)
    logger.setLevel(logging.DEBUG)
    return logger


def get_error_logger(name: str) -> logging.Logger:
    """获取错误日志记录器"""
    logger = get_logger(name)
    logger.setLevel(logging.ERROR)
    return logger


# ============================================================
# 测试函数
# ============================================================

def test_logging():
    """测试日志配置是否正常工作"""
    # 配置日志
    setup_logging(log_level="DEBUG", enable_colors=True)
    
    # 获取日志记录器
    logger = get_logger("test_logger")
    
    # 测试各级别日志
    logger.debug("这是DEBUG日志")
    logger.info("这是INFO日志")
    logger.warning("这是WARNING日志")
    logger.error("这是ERROR日志")
    logger.critical("这是CRITICAL日志")
    
    # 测试带request_id的日志
    logger_with_id = get_logger_with_request_id("test_logger", "test-request-123")
    logger_with_id.info("这是带request_id的日志")
    
    print("\n✅ 日志测试完成！")


if __name__ == "__main__":
    test_logging()