# -*- coding: utf-8 -*-
import pymysql
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from config import Config

def check():
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4'
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT id, title, image_url FROM properties WHERE id = 1")
    row = cursor.fetchone()
    
    if row:
        print(f"ID: {row['id']}")
        print(f"Title: {row['title']}")
        print(f"Image URL: {row.get('image_url', 'NULL')}")
        
        if row.get('image_url'):
            print("\nSUCCESS: image_url is not NULL!")
        else:
            print("\nERROR: image_url is NULL")
    else:
        print("No data found")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check()

