#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Reimport data to database"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models.database import create_tables, DatabaseManager, Property
from utils.database import PropertyService
import csv

def reimport_data():
    """Reimport data to database"""
    try:
        create_tables()
        db_manager = DatabaseManager()
        db = db_manager.get_session()
        property_service = PropertyService(db)
        
        print("[INFO] Clearing existing properties...")
        db.query(Property).delete()
        db.commit()
        print("[INFO] Cleared")
        
        print("[INFO] Reading properties.csv...")
        with open('properties.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            properties = list(csv_reader)
        
        print(f"[INFO] Found {len(properties)} properties")
        
        imported_count = 0
        for prop in properties:
            try:
                image_url = prop.get('image_url', '')
                if image_url and '# 可选' in image_url:
                    image_url = image_url.replace('https://# 可选/', 'https://')
                    prop['image_url'] = image_url
                
                property_service.create_property(prop)
                imported_count += 1
                
                if imported_count % 5 == 0:
                    print(f"[PROGRESS] {imported_count}/{len(properties)}")
                    
            except Exception as e:
                print(f"[ERROR] {e}")
                continue
        
        print(f"\n[SUCCESS] Imported {imported_count}/{len(properties)} properties")
        db_manager.close_session(db)
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Reimport Data to Database")
    print("=" * 60)
    reimport_data()
    print("\nDone!")



