#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化数据库表"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import create_tables

def init_database():
    """初始化数据库"""
    try:
        print("[INFO] Initializing database...")
        create_tables()
        print("[SUCCESS] Database initialized successfully!")
        return True
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
