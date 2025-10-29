#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复数据库中的图片URL
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import create_tables, DatabaseManager, Property
from utils.database import PropertyService
import csv

def fix_image_urls():
    """修复数据库中的图片URL"""
    try:
        # 创建数据库
        create_tables()
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        db = db_manager.get_session()
        
        # 读取CSV
        print("[INFO] Reading properties.csv...")
        with open('properties.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            properties = list(csv_reader)
        
        print(f"[INFO] Found {len(properties)} properties in CSV")
        
        # 更新数据库
        updated_count = 0
        for prop in properties:
            url = prop.get('url', '')
            image_url = prop.get('image_url', '')
            
            # 检查并修复URL中的错误
            if image_url and '# 可选' in image_url:
                # 修复URL
                image_url = image_url.replace('https://# 可选/', 'https://')
                print(f"[FIX] Fixed URL: {image_url}")
            
            # 查找现有房产
            existing = db.query(Property).filter(Property.url == url).first()
            if existing:
                # 更新图片URL
                existing.image_url = image_url
                updated_count += 1
                print(f"[UPDATE] Property ID {existing.id}: {image_url}")
        
        # 提交更改
        db.commit()
        print(f"[SUCCESS] Updated {updated_count} properties")
        
        db_manager.close_session(db)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to fix image URLs: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("修复数据库图片URL工具")
    print("=" * 60)
    print()
    
    fix_image_urls()
    
    print()
    print("完成！请重新启动后端API服务器并测试。")



