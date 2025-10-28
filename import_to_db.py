# -*- coding: utf-8 -*-
"""Import CSV to database"""
import pymysql
import csv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import Config

def import_csv(filename='properties.csv', clear_table=False):
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
        
        # 根据参数决定是否清空表
        if clear_table:
            cursor.execute("TRUNCATE TABLE properties")
            print("[INFO] Cleared existing data")
        
        # 读取CSV
        with open(filename, 'r', encoding='utf-8') as f:
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
                    
                    # 获取listing_type，默认为for_sale
                    listing_type = row.get('listing_type', 'for_sale')
                    
                    sql = """INSERT INTO properties (title, price, price_numeric, bedrooms, 
                             listing_type, description, description_chinese, url, image_url) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    
                    cursor.execute(sql, (
                        row.get('title'),
                        row.get('price'),
                        price_numeric,
                        bedrooms,
                        listing_type,
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
    import argparse
    
    parser = argparse.ArgumentParser(description='Import CSV to database')
    parser.add_argument('--file', type=str, default='properties.csv',
                        help='CSV file to import')
    parser.add_argument('--clear', action='store_true',
                        help='Clear existing data before import')
    parser.add_argument('--append', action='store_true',
                        help='Append data without clearing (default behavior)')
    
    args = parser.parse_args()
    
    print(f"Importing data from {args.file}...")
    
    # 如果指定了--clear，清空表；否则追加数据
    clear_table = args.clear and not args.append
    
    import_csv(args.file, clear_table=clear_table)
    print("Done!")


