#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理错误的邮编数据
将所有postcode设置为空，然后重新运行update_location_postcode.py来正确提取
"""

import sys
import os

# 添加backend目录到路径
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)
os.chdir(backend_path)

from models.database import Property, DatabaseManager
from sqlalchemy import or_, and_

def main():
    """清理错误的邮编"""
    db_manager = DatabaseManager()
    db = db_manager.get_session()
    
    try:
        # 查找所有有postcode但可能不准确的记录
        # 如果postcode不是标题的一部分，可能不准确
        all_properties = db.query(Property).filter(
            Property.postcode.isnot(None),
            Property.postcode != ''
        ).all()
        
        print(f"[INFO] 找到 {len(all_properties)} 条有postcode的记录")
        print(f"[INFO] 检查postcode是否在标题中...\n")
        
        cleared_count = 0
        kept_count = 0
        
        for idx, prop in enumerate(all_properties, 1):
            title = (prop.title or '').upper()
            postcode = (prop.postcode or '').upper()
            
            # 检查postcode是否在标题中
            # 提取postcode的前缀部分（如果完整邮编，取前3-4个字符）
            postcode_prefix = postcode.split()[0] if ' ' in postcode else postcode[:3]
            
            # 检查标题中是否包含这个邮编
            title_has_postcode = postcode_prefix in title or postcode in title
            
            if not title_has_postcode:
                print(f"[{idx}/{len(all_properties)}] ID: {prop.id}")
                print(f"  标题: {prop.title[:60] if prop.title else 'N/A'}...")
                print(f"  当前postcode: {prop.postcode}")
                print(f"  ❌ 邮编不在标题中，清空")
                prop.postcode = None
                cleared_count += 1
            else:
                kept_count += 1
                if idx % 10 == 0:
                    print(f"[{idx}/{len(all_properties)}] 检查中... (保留: {kept_count}, 清空: {cleared_count})")
        
        if cleared_count > 0:
            db.commit()
            print(f"\n[SUCCESS] 清理完成！")
            print(f"  - 清空错误邮编: {cleared_count} 条")
            print(f"  - 保留正确邮编: {kept_count} 条")
            print(f"\n[提示] 现在可以运行 update_location_postcode.py 重新提取邮编")
        else:
            print(f"\n[INFO] 所有邮编看起来都是正确的（在标题中能找到）")
        
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()




