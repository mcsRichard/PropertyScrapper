#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""使用原生SQL初始化数据库"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from config import Config
import pymysql

def init_database():
    """初始化数据库表"""
    try:
        print("[INFO] Connecting to database...")
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4'
        )
        
        print("[INFO] Database connected!")
        
        with connection.cursor() as cursor:
            # 创建properties表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    price VARCHAR(50) NOT NULL,
                    price_numeric INT,
                    area VARCHAR(100),
                    bedrooms INT,
                    bathrooms INT,
                    property_type VARCHAR(100),
                    location VARCHAR(255),
                    postcode VARCHAR(20),
                    description TEXT,
                    description_chinese TEXT,
                    url VARCHAR(500) UNIQUE,
                    image_url VARCHAR(500),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_title (title),
                    INDEX idx_price (price_numeric),
                    INDEX idx_bedrooms (bedrooms),
                    INDEX idx_property_type (property_type),
                    INDEX idx_location (location),
                    INDEX idx_postcode (postcode),
                    INDEX idx_url (url)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 创建property_images表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS property_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    property_id INT,
                    image_url VARCHAR(500),
                    image_path VARCHAR(500),
                    is_primary TINYINT(1) DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_property_id (property_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            
            # 创建locations表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) UNIQUE,
                    region VARCHAR(100),
                    postcode VARCHAR(20),
                    coordinates VARCHAR(50),
                    INDEX idx_name (name),
                    INDEX idx_region (region),
                    INDEX idx_postcode (postcode)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
        
        connection.commit()
        print("[SUCCESS] Database tables created successfully!")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
