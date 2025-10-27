# scripts/import_data.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import create_tables, DatabaseManager
from utils.database import PropertyService
import csv
import json

def import_from_csv(csv_file_path):
    """从CSV文件导入数据"""
    try:
        # 初始化数据库
        create_tables()
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        db = db_manager.get_session()
        property_service = PropertyService(db)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        print(f"[INFO] Starting import from {csv_file_path}")
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row_num, row in enumerate(csv_reader, 1):
                try:
                    # 检查是否已存在
                    existing = property_service.get_property_by_url(row.get('url', ''))
                    if existing:
                        print(f"[SKIP] Row {row_num}: Property already exists")
                        skipped_count += 1
                        continue
                    
                    # 创建房产记录
                    property_service.create_property(row)
                    imported_count += 1
                    print(f"[SUCCESS] Row {row_num}: Imported {row.get('title', 'Unknown')}")
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"[ERROR] {error_msg}")
                    skipped_count += 1
        
        print(f"\n[SUMMARY] Import completed:")
        print(f"  - Imported: {imported_count}")
        print(f"  - Skipped: {skipped_count}")
        print(f"  - Errors: {len(errors)}")
        
        if errors:
            print(f"\n[ERRORS]:")
            for error in errors:
                print(f"  - {error}")
        
        db_manager.close_session(db)
        return True
        
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("Usage: python import_data.py <csv_file_path>")
        print("Example: python import_data.py ../properties.csv")
        return
    
    csv_file_path = sys.argv[1]
    
    if not os.path.exists(csv_file_path):
        print(f"[ERROR] File not found: {csv_file_path}")
        return
    
    success = import_from_csv(csv_file_path)
    if success:
        print("[SUCCESS] Data import completed successfully")
    else:
        print("[ERROR] Data import failed")

if __name__ == "__main__":
    main()
