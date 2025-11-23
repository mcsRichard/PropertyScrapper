# -*- coding: utf-8 -*-
"""
云函数 Web 函数入口文件
用于在腾讯云 SCF 中运行 Flask 应用
"""

import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 导入 Flask 应用创建函数
from app import create_app

# 创建 Flask 应用实例（SCF Web 函数必须暴露 app）
app = create_app()


# Web 函数必须监听 9000 端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9000))
    app.run(host="0.0.0.0", port=port, debug=False)
