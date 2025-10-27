# -*- coding: utf-8 -*-
"""Import CSV to database"""
import pymysql
import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import Config

def import_csv():
    try:
        conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        # 清空表
        cursor.execute("TRUNCATE TABLE properties")
        print("[INFO] Cleared existing data")
        
        # 读取CSV
        with open('properties.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            
            for row in reader:
                try:
                    # 修复image_url
                    image_url = row.get('image_url', '')
                    if '# 可选' in image_url:
                        image_url = image_url.replace('https://# 可选/', 'https://')
                    
                    # 提取价格数字
                    price = row.get('price', '')
                    price_numeric = None
                    if price and '£' in price:
                        try:
                            price_clean = price.replace('£', '').replace(',', '').strip()
                            price_numeric = int(price_clean)
                        except:
                            pass
                    
                    # 提取卧室数
                    title = row.get('title', '')
                    bedrooms = None
                    import re
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
                    count += 1
                    
                except Exception as e:
                    print(f"[ERROR] Row failed: {e}")
                    continue
            
            conn.commit()
            print(f"[SUCCESS] Imported {count} properties")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Importing data to database...")
    import_csv()
    print("Done!")

