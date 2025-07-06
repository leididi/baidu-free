"""
日志中间件 - 基于loguru的统一日志管理
提供项目统一的日志配置和接口
"""

import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional


class LoggerMiddleware:
    """日志中间件类"""

    def __init__(
        self,
        enable_file_logging: bool = False,
        log_dir: str = "logs",
        console_level: str = "INFO",
        file_level: str = "INFO",
    ):
        """
        初始化日志中间件

        Args:
            enable_file_logging: 是否启用文件日志，默认True
            log_dir: 日志文件目录，默认"logs"
            console_level: 控制台日志级别，默认"INFO"
            file_level: 文件日志级别，默认"INFO"
        """
        self._logger = logger
        self._is_configured = False
        self._enable_file_logging = enable_file_logging
        self._log_dir = log_dir
        self._console_level = console_level
        self._file_level = file_level
        self._setup_default_config()

    def _setup_default_config(self):
        """设置默认日志配置"""
        if self._is_configured:
            return

        # 移除默认的控制台输出
        self._logger.remove()

        # 控制台输出配置
        self._logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>",
            level=self._console_level,
            colorize=True,
        )

        # 文件日志配置（可选）
        if self._enable_file_logging:
            self._setup_file_logging()

        self._is_configured = True
        init_msg = f"日志中间件初始化完成 - 文件日志: {'启用' if self._enable_file_logging else '禁用'}"
        self._logger.info(init_msg)

    def _setup_file_logging(self):
        """设置文件日志配置"""
        # 创建日志目录
        log_dir = Path(self._log_dir)
        log_dir.mkdir(exist_ok=True)

        # 文件输出配置 - 普通日志
        self._logger.add(
            f"{self._log_dir}/app.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=self._file_level,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
        )

        # 文件输出配置 - 错误日志
        self._logger.add(
            f"{self._log_dir}/error.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level="ERROR",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
        )

    def get_logger(self, name: Optional[str] = None):
        """
        获取logger实例

        Args:
            name: logger名称，用于标识不同模块

        Returns:
            logger实例
        """
        if name:
            return self._logger.bind(name=name)
        return self._logger

    def set_level(self, console_level: Optional[str] = None, file_level: Optional[str] = None):
        """
        设置日志级别

        Args:
            console_level: 控制台日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            file_level: 文件日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if console_level:
            self._console_level = console_level
        if file_level:
            self._file_level = file_level

        # 重新配置所有handler
        self._logger.remove()
        self._is_configured = False
        self._setup_default_config()
        self._logger.info(f"日志级别已更新 - 控制台: {self._console_level}, 文件: {self._file_level}")

    def enable_file_logging(self, log_dir: str = "logs"):
        """
        启用文件日志

        Args:
            log_dir: 日志文件目录
        """
        if not self._enable_file_logging:
            self._enable_file_logging = True
            self._log_dir = log_dir
            self._setup_file_logging()
            self._logger.info(f"文件日志已启用，目录: {log_dir}")

    def disable_file_logging(self):
        """禁用文件日志"""
        if self._enable_file_logging:
            self._enable_file_logging = False
            # 重新配置，只保留控制台输出
            self._logger.remove()
            self._is_configured = False
            self._setup_default_config()
            self._logger.info("文件日志已禁用")

    def add_file_handler(
        self,
        file_path: str,
        level: str = "INFO",
        rotation: str = "10 MB",
        retention: str = "7 days",
    ):
        """
        添加自定义文件日志处理器

        Args:
            file_path: 日志文件路径
            level: 日志级别
            rotation: 日志轮转大小
            retention: 日志保留时间
        """
        # 确保目录存在
        file_dir = Path(file_path).parent
        file_dir.mkdir(parents=True, exist_ok=True)

        self._logger.add(
            file_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=level,
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8",
        )
        self._logger.info(f"添加自定义文件日志处理器: {file_path}")

    def get_config_info(self) -> dict:
        """
        获取当前配置信息

        Returns:
            配置信息字典
        """
        return {
            "enable_file_logging": self._enable_file_logging,
            "log_dir": self._log_dir,
            "console_level": self._console_level,
            "file_level": self._file_level,
            "is_configured": self._is_configured,
        }


# 全局日志中间件实例
_logger_middleware = None


def get_logger_middleware(**kwargs) -> LoggerMiddleware:
    """
    获取日志中间件实例（单例模式）

    Args:
        **kwargs: 传递给LoggerMiddleware的参数
                 enable_file_logging: 是否启用文件日志，默认True
                 log_dir: 日志文件目录，默认"logs"
                 console_level: 控制台日志级别，默认"INFO"
                 file_level: 文件日志级别，默认"INFO"

    Returns:
        LoggerMiddleware实例
    """
    global _logger_middleware
    if _logger_middleware is None:
        # 从环境变量读取配置
        enable_file_logging = kwargs.get(
            "enable_file_logging",
            os.getenv("LOG_ENABLE_FILE", "false").lower() == "true",
        )
        log_dir = kwargs.get("log_dir", os.getenv("LOG_DIR", "logs"))
        console_level = kwargs.get("console_level", os.getenv("LOG_CONSOLE_LEVEL", "INFO"))
        file_level = kwargs.get("file_level", os.getenv("LOG_FILE_LEVEL", "INFO"))

        _logger_middleware = LoggerMiddleware(
            enable_file_logging=enable_file_logging,
            log_dir=log_dir,
            console_level=console_level,
            file_level=file_level,
        )
    return _logger_middleware


def get_logger(name: Optional[str] = None):
    """
    获取logger实例的便捷函数

    Args:
        name: logger名称

    Returns:
        logger实例
    """
    middleware = get_logger_middleware()
    return middleware.get_logger(name)


def configure_logger(
    enable_file_logging: bool = False,
    log_dir: str = "logs",
    console_level: str = "INFO",
    file_level: str = "INFO",
):
    """
    配置日志中间件的便捷函数

    Args:
        enable_file_logging: 是否启用文件日志
        log_dir: 日志文件目录
        console_level: 控制台日志级别
        file_level: 文件日志级别
    """
    global _logger_middleware
    _logger_middleware = LoggerMiddleware(
        enable_file_logging=enable_file_logging,
        log_dir=log_dir,
        console_level=console_level,
        file_level=file_level,
    )
    return _logger_middleware


# 为了兼容现有代码，提供直接的logger实例
logger = get_logger()
