#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量替换kline_manager.py中的print语句
"""

import re

# 读取文件
with open('C:\\Users\\86158\\Desktop\\Tidewatch\\services\\kline_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换print语句
# 替换带有时间戳的print
content = re.sub(
    r'print\(f"\[{datetime\.now\(\)\.strftime\('%H:%M:%S'\)}\] (.*)"\)',
    r'logger.info(r"\1")',
    content
)

# 替换其他print语句
content = re.sub(
    r'print\(f"(.*)"\)',
    r'logger.info(r"\1")',
    content
)

content = re.sub(
    r'print\("(.*)"\)',
    r'logger.info("\1")',
    content
)

# 写回文件
with open('C:\\Users\\86158\\Desktop\\Tidewatch\\services\\kline_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("替换完成")