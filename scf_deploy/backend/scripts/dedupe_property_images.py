# scripts/dedupe_property_images.py
"""
清理数据库中同一房源下的重复图片（基于图片唯一标识）
"""
import os
import sys
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_DIR)

from models.database import engine, DatabaseManager
from utils.database import PropertyService
from sqlalchemy import text

def extract_image_key_from_url(url):
    """提取图片的唯一标识（去掉尺寸参数）"""
    if not url:
        return None
    # Zoopla格式：https://lid.zoocdn.com/u/480/360/xxxxx.jpg
    match = re.search(r'/(\d+)/(\d+)/([^/]+\.(jpg|jpeg|png|webp))', url.lower())
    if match:
        return match.group(3)  # 返回文件名
    # 如果不能匹配，返回文件名部分
    return url.split('/')[-1] if '/' in url else url


def dedupe_images_by_property():
    """清理每个房源下的重复图片"""
    with engine.begin() as conn:
        # 查询所有房源ID
        query = text("SELECT DISTINCT property_id FROM property_images ORDER BY property_id")
        properties = conn.execute(query).fetchall()
        
        print(f"[INFO] 找到 {len(properties)} 个有图片的房源")
        
        total_deleted = 0
        
        for (property_id,) in properties:
            # 查询该房源的所有图片
            query = text("""
                SELECT id, source_url, image_url, cos_key, order_index, is_primary
                FROM property_images
                WHERE property_id = :prop_id
                ORDER BY order_index, id
            """)
            images = conn.execute(query, {"prop_id": property_id}).fetchall()
            
            if len(images) <= 1:
                continue
            
            # 按图片唯一标识分组
            seen_keys = {}
            to_keep = []
            to_delete = []
            
            for img in images:
                img_id, source_url, image_url, cos_key, order_idx, is_primary = img
                
                # 优先使用source_url提取key，其次image_url，最后cos_key
                url_to_check = source_url or image_url or ''
                img_key = extract_image_key_from_url(url_to_check)
                if not img_key and cos_key:
                    # 从cos_key提取文件名
                    img_key = cos_key.split('/')[-1] if '/' in cos_key else cos_key
                
                if not img_key:
                    img_key = f"unknown_{img_id}"
                
                # 如果已经见过这个key，保留第一个（或主图）
                if img_key in seen_keys:
                    existing = seen_keys[img_key]
                    # 如果当前是主图且已存在的不主图，替换
                    if is_primary and not existing[5]:
                        to_delete.append(existing[0])
                        to_keep.append(img)
                        seen_keys[img_key] = img
                    else:
                        to_delete.append(img_id)
                else:
                    seen_keys[img_key] = img
                    to_keep.append(img)
            
            # 删除重复记录
            if to_delete:
                # MySQL的IN子句需要逐个删除或使用特定语法
                for img_id in to_delete:
                    delete_query = text("DELETE FROM property_images WHERE id = :id")
                    conn.execute(delete_query, {"id": img_id})
                total_deleted += len(to_delete)
                print(f"[OK] 房源 {property_id}: 保留 {len(to_keep)} 张，删除 {len(to_delete)} 张重复图片")
        
        print(f"\n[SUCCESS] 清理完成，共删除 {total_deleted} 张重复图片")


def main():
    dedupe_images_by_property()


if __name__ == '__main__':
    main()

