# -*- coding: utf-8 -*-
"""
云函数Web函数入口文件
用于在云函数中运行Flask应用
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 导入Flask应用创建函数
from app import create_app

# 创建Flask应用实例
app = create_app()

# Web函数需要这个app对象
# 云函数会自动处理HTTP请求并转发给Flask应用

