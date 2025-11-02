#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库中location和postcode字段的脚本
从title、description或url中提取邮编和地点信息
"""

import sys
import os
import re

# 添加backend目录到路径
backend_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, backend_path)

# 设置工作目录到backend
os.chdir(backend_path)

from models.database import Property, DatabaseManager
from sqlalchemy import or_, func

def extract_postcode(text):
    """从文本中提取英国邮编"""
    if not text:
        return None
    
    # 英国邮编格式：字母+数字+字母（如 N10 1AB, SW7 3AZ）
    # 匹配格式：1-2字母 + 1-2数字 + 空格（可选） + 1数字 + 2字母
    patterns = [
        r'\b([A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2})\b',  # 完整邮编 N10 1AB, SW7 3AZ
        r'\b([A-Z]{1,2}\d{1,2})\b',  # 邮编前缀 N10, SW7
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.upper())
        if match:
            postcode = match.group(1).strip()
            # 标准化：如果有空格，保持；如果没有，不添加
            return postcode
    
    return None

def extract_location(text):
    """从文本中提取地点名称"""
    if not text:
        return None
    
    # 常见伦敦地区名称（可以扩展）
    london_areas = [
        'London', 'Muswell Hill', 'Hampstead', 'Camden', 'Greenwich',
        'Shoreditch', 'Battersea', 'Clapham', 'Fulham', 'Notting Hill',
        'Paddington', 'Marylebone', 'Covent Garden', 'Canary Wharf',
        'Docklands', 'Kensington', 'Chelsea', 'Westminster', 'Islington'
    ]
    
    text_upper = text.upper()
    for area in london_areas:
        if area.upper() in text_upper:
            return area
    
    # 尝试从标题中提取第一个地名（通常是街道名或地区名）
    # 标题格式通常是："Property in [Location]" 或 "Street, Location"
    patterns = [
        r'in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # "in Location"
        r',\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # ", Location"
        r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:London|UK)',  # "Location London"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            location = match.group(1).strip()
            if len(location) > 2:  # 过滤掉太短的匹配
                return location
    
    return None

def fix_property_location_postcode(property_obj):
    """修复单个房产的location和postcode"""
    updated = False
    
    # 优先从postcode字段提取（可能已经有值但格式不对）
    if not property_obj.postcode or property_obj.postcode == '':
        # 尝试从title中提取
        postcode = extract_postcode(property_obj.title or '')
        if not postcode:
            # 尝试从description中提取
            postcode = extract_postcode(property_obj.description or '')
        if not postcode:
            # 尝试从url中提取（Zoopla URL可能包含邮编信息）
            postcode = extract_postcode(property_obj.url or '')
        
        if postcode:
            property_obj.postcode = postcode
            updated = True
    
    # 优先从location字段提取
    if not property_obj.location or property_obj.location == '':
        # 尝试从title中提取
        location = extract_location(property_obj.title or '')
        if not location:
            # 尝试从description中提取
            location = extract_location(property_obj.description or '')
        
        if location:
            property_obj.location = location
            updated = True
    
    return updated

def main():
    """主函数：修复所有房产的location和postcode"""
    db_manager = DatabaseManager()
    db = db_manager.get_session()
    
    try:
        # 获取所有location或postcode为空的房产
        properties = db.query(Property).filter(
            or_(
                Property.location.is_(None),
                Property.location == '',
                Property.postcode.is_(None),
                Property.postcode == ''
            )
        ).all()
        
        print(f"[INFO] 找到 {len(properties)} 条需要修复的房产记录")
        
        updated_count = 0
        postcode_count = 0
        location_count = 0
        
        for idx, prop in enumerate(properties, 1):
            print(f"\n[处理 {idx}/{len(properties)}] ID: {prop.id}, Title: {prop.title[:50] if prop.title else 'N/A'}...")
            
            old_postcode = prop.postcode
            old_location = prop.location
            
            updated = fix_property_location_postcode(prop)
            
            if updated:
                updated_count += 1
                if prop.postcode != old_postcode:
                    postcode_count += 1
                    print(f"  ✅ Postcode: {old_postcode} -> {prop.postcode}")
                if prop.location != old_location:
                    location_count += 1
                    print(f"  ✅ Location: {old_location} -> {prop.location}")
            else:
                print(f"  ⚠️ 未找到location或postcode")
        
        # 提交更改
        if updated_count > 0:
            db.commit()
            print(f"\n[SUCCESS] 修复完成！")
            print(f"  - 总更新数: {updated_count}")
            print(f"  - Postcode更新数: {postcode_count}")
            print(f"  - Location更新数: {location_count}")
        else:
            print(f"\n[INFO] 没有需要修复的记录")
        
        # 统计修复后的数据
        total_properties = db.query(Property).count()
        properties_with_postcode = db.query(Property).filter(
            Property.postcode.isnot(None),
            Property.postcode != ''
        ).count()
        properties_with_location = db.query(Property).filter(
            Property.location.isnot(None),
            Property.location != ''
        ).count()
        
        print(f"\n[统计] 修复后的数据:")
        print(f"  - 总房产数: {total_properties}")
        print(f"  - 有postcode的: {properties_with_postcode} ({properties_with_postcode*100/total_properties:.1f}%)")
        print(f"  - 有location的: {properties_with_location} ({properties_with_location*100/total_properties:.1f}%)")
        
    except Exception as e:
        print(f"[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()

