# -*- coding: utf-8 -*-
"""Add listing_type column to properties table"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
import pymysql

def add_listing_type_column():
    """Add listing_type column to properties table"""
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
        
        # Check if column exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'properties' 
            AND COLUMN_NAME = 'listing_type'
        """, (Config.DB_NAME,))
        
        exists = cursor.fetchone()[0] > 0
        
        if exists:
            print("[INFO] listing_type column already exists")
        else:
            # Add the column
            print("[INFO] Adding listing_type column...")
            cursor.execute("""
                ALTER TABLE properties 
                ADD COLUMN listing_type VARCHAR(20) DEFAULT 'for_sale' 
                AFTER property_type
            """)
            
            # Add index
            print("[INFO] Adding index for listing_type...")
            cursor.execute("""
                CREATE INDEX idx_listing_type ON properties(listing_type)
            """)
            
            conn.commit()
            print("[SUCCESS] Added listing_type column and index")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"[ERROR] Failed to add listing_type column: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Adding listing_type column to properties table...")
    add_listing_type_column()
    print("Done!")

