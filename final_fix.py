# -*- coding: utf-8 -*-
import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import Config

def fix():
    # 读取并修复CSV
    rows = []
    with open('properties.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Found {len(rows)} rows")
    
    # 正确的COS域名
    bucket = Config.COS_BUCKET
    region = Config.COS_REGION
    base_url = f"https://{bucket}.cos.{region}.myqcloud.com"
    
    # 修复所有URL
    for row in rows:
        img_url = row.get('image_url', '')
        
        # 移除错误的前缀
        if 'https://# 可选/' in img_url:
            img_url = img_url.replace('https://# 可选/', '')
        
        # 组合完整的URL
        if img_url and not img_url.startswith('http'):
            row['image_url'] = f"{base_url}/{img_url}"
        elif img_url and not img_url.startswith('https://'):
            row['image_url'] = f"{base_url}/{img_url}"
    
    # 写回CSV
    with open('properties.csv', 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"Fixed CSV")
    
    # 导入到数据库
    import pymysql
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    cursor.execute("TRUNCATE TABLE properties")
    
    for row in rows:
        try:
            image_url = row.get('image_url', '')
            price = row.get('price', '')
            price_numeric = None
            if price and '£' in price:
                try:
                    price_numeric = int(price.replace('£', '').replace(',', '').strip())
                except:
                    pass
            
            import re
            title = row.get('title', '')
            bedrooms = None
            match = re.search(r'(\d+)\s*bed', title.lower())
            if match:
                bedrooms = int(match.group(1))
            
            sql = """INSERT INTO properties (title, price, price_numeric, bedrooms, 
                     description, description_chinese, url, image_url) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            cursor.execute(sql, (
                row.get('title'),
                row.get('price'),
                price_numeric,
                bedrooms,
                row.get('description'),
                row.get('description_chinese'),
                row.get('url'),
                image_url
            ))
        except Exception as e:
            print(f"Error: {e}")
            continue
    
    conn.commit()
    print(f"Imported {len(rows)} properties")
    
    cursor.close()
    conn.close()
    
    print("Done!")

if __name__ == "__main__":
    fix()


