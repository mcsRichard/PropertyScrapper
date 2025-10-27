#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""从CSV导入数据到数据库"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config
import pymysql
import csv
import re

def extract_price_numeric(price_str):
    """提取价格数字"""
    if not price_str:
        return None
    price_clean = re.sub(r'[£,\s]', '', price_str)
    try:
        return int(price_clean)
    except ValueError:
        return None

def extract_property_type(title):
    """从标题提取房产类型"""
    if not title:
        return None
    title_lower = title.lower()
    if 'flat' in title_lower or 'apartment' in title_lower:
        return 'flat'
    elif 'house' in title_lower:
        return 'house'
    elif 'maisonette' in title_lower:
        return 'maisonette'
    elif 'studio' in title_lower:
        return 'studio'
    else:
        return 'other'

def extract_bedrooms(title):
    """从标题提取卧室数量"""
    if not title:
        return None
    match = re.search(r'(\d+)\s*bed', title.lower())
    if match:
        return int(match.group(1))
    return None

def import_csv_to_db(csv_file):
    """从CSV文件导入数据到数据库"""
    try:
        print(f"[INFO] Starting import from {csv_file}")
        
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        imported = 0
        skipped = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    # 检查是否已存在
                    cursor.execute("SELECT id FROM properties WHERE url = %s", (row.get('url'),))
                    if cursor.fetchone():
                        skipped += 1
                        continue
                    
                    # 提取数据
                    price_numeric = extract_price_numeric(row.get('price'))
                    property_type = extract_property_type(row.get('title'))
                    bedrooms = extract_bedrooms(row.get('title'))
                    
                    # 插入数据
                    cursor.execute("""
                        INSERT INTO properties 
                        (title, price, price_numeric, bedrooms, property_type, 
                         description, description_chinese, url, image_url) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        row.get('title'),
                        row.get('price'),
                        price_numeric,
                        bedrooms,
                        property_type,
                        row.get('description'),
                        row.get('description_chinese'),
                        row.get('url'),
                        row.get('image_url')
                    ))
                    
                    imported += 1
                    if imported % 10 == 0:
                        print(f"[INFO] Imported {imported} properties...")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to import row: {e}")
                    skipped += 1
        
        conn.commit()
        print(f"[SUCCESS] Import completed: {imported} imported, {skipped} skipped")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return False

if __name__ == "__main__":
    csv_file = "properties.csv"
    if not os.path.exists(csv_file):
        print(f"[ERROR] File not found: {csv_file}")
        sys.exit(1)
    
    success = import_csv_to_db(csv_file)
    sys.exit(0 if success else 1)
