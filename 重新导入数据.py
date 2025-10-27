#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新导入数据到数据库（包含图片URL）
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import create_tables, DatabaseManager, Property
from utils.database import PropertyService
import csv

def reimport_data():
    """重新导入数据到数据库"""
    try:
        # 创建数据库
        create_tables()
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        db = db_manager.get_session()
        property_service = PropertyService(db)
        
        # 先清空现有数据（可选）
        print("[INFO] Clearing existing properties...")
        db.query(Property).delete()
        db.commit()
        print("[INFO] Cleared existing data")
        
        # 读取CSV
        print("[INFO] Reading properties.csv...")
        with open('properties.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            properties = list(csv_reader)
        
        print(f"[INFO] Found {len(properties)} properties in CSV")
        
        # 导入数据
        imported_count = 0
        for prop in properties:
            try:
                # 修复URL中的错误
                image_url = prop.get('image_url', '')
                if image_url and '# 可选' in image_url:
                    image_url = image_url.replace('https://# 可选/', 'https://')
                    prop['image_url'] = image_url
                    print(f"[FIX] Fixed URL: {image_url[:50]}...")
                
                # 创建房产记录
                property_service.create_property(prop)
                imported_count += 1
                
                if imported_count % 5 == 0:
                    print(f"[PROGRESS] Imported {imported_count}/{len(properties)}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to import property: {e}")
                continue
        
        print(f"\n[SUCCESS] Imported {imported_count}/{len(properties)} properties")
        
        db_manager.close_session(db)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("重新导入数据到数据库")
    print("=" * 60)
    print()
    
    result = reimport_data()
    
    if result:
        print("\n" + "=" * 60)
        print("导入成功！请重新启动后端API服务器。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("导入失败！请检查错误信息。")
        print("=" * 60)

