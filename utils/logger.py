#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志工具模块
"""

import logging
import os
from datetime import datetime

# 全局标志，确保只初始化一次
_logger_initialized = False

def setup_logger(name='tidewatch', level=logging.INFO):
    """设置日志配置"""
    global _logger_initialized

    # 如果已经初始化过，直接返回
    if _logger_initialized:
        return logging.getLogger(name)

    # 获取根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # 避免重复添加handler
    if root_logger.handlers:
        _logger_initialized = True
        return logging.getLogger(name)

    # 创建formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 只创建控制台handler，不写文件（避免触发热重载）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # 添加handler到根logger
    root_logger.addHandler(console_handler)

    _logger_initialized = True
    return logging.getLogger(name)

# 创建默认logger
logger = setup_logger()

def get_logger(name=None):
    """获取logger实例"""
    if name:
        return logging.getLogger(name)
    return logger