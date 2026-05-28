# -*- coding: utf-8 -*-
"""
PythonAnywhere WSGI 入口
将此文件配置到 PythonAnywhere 的 WSGI 配置中即可。
"""

import os
import sys

# 确保项目根目录在 Python 路径中
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

# PythonAnywhere 模式：避免后台定时任务冲突
os.environ.setdefault("PA_MODE", "1")

from web.app import app  # noqa: E402
