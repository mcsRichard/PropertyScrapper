# -*- coding: utf-8 -*-
import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import Config

def fix_csv():
    # 读取CSV
    rows = []
    with open('properties.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"Found {len(rows)} rows")
    
    # 修复URL
    fixed_count = 0
    for row in rows:
        img_url = row.get('image_url', '')
        if img_url and not img_url.startswith('http'):
            # 修复URL - 添加完整的COS域名
            bucket = Config.COS_BUCKET
            region = Config.COS_REGION
            row['image_url'] = f"https://{bucket}.cos.{region}.myqcloud.com/{img_url.replace('https://', '')}"
            fixed_count += 1
            print(f"Fixed: {row['image_url'][:80]}")
    
    # 写回CSV
    if fixed_count > 0:
        with open('properties.csv', 'w', newline='', encoding='utf-8') as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
        
        print(f"\nFixed {fixed_count} URLs in CSV")
    
    # 重新导入到数据库
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
    print("Cleared database")
    
    for row in rows:
        try:
            image_url = row.get('image_url', '')
            if '# 可选' in image_url:
                image_url = image_url.replace('https://# 可选/', 'https://')
            
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
    print(f"Re-imported {len(rows)} properties to database")
    
    cursor.close()
    conn.close()
    
    print("\nDone!")

if __name__ == "__main__":
    fix_csv()



