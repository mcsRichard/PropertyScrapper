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

# 创建 Flask 应用实例
# Web 函数需要这个 app 对象
app = create_app()


def main():
    """
    本地 / Web 函数启动入口
    在 Web 函数“启动命令”里填：python index.py
    """
    port = int(os.environ.get("PORT", os.environ.get("SCF_WEB_PORT", 9000)))
    # 在 Web 函数中，必须监听 0.0.0.0，并使用平台提供的端口
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
