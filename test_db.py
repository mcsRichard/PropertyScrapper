#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试数据库连接"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config
import pymysql

def test_connection():
    """测试数据库连接"""
    try:
        print("[INFO] Testing database connection...")
        print(f"[INFO] Host: {Config.DB_HOST}")
        print(f"[INFO] Port: {Config.DB_PORT}")
        print(f"[INFO] User: {Config.DB_USER}")
        print(f"[INFO] Database: {Config.DB_NAME}")
        
        # 尝试连接数据库
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )
        
        print("[SUCCESS] Database connection successful!")
        
        # 关闭连接
        connection.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
