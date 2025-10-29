# scripts/fix_image_urls.py
"""
修复数据库中错误的图片URL（包含 # 可选 这类无效域名）
"""
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_DIR)

from models.database import engine, DatabaseManager
from utils.database import PropertyService
from sqlalchemy import text
from config import Config

def fix_invalid_image_urls():
    """修复property_images表中包含无效域名的URL"""
    with engine.begin() as conn:
        # 查找所有包含无效域名的记录
        query = text("""
            SELECT id, property_id, image_url, cos_key, order_index
            FROM property_images
            WHERE image_url LIKE '%# 可选%' OR image_url LIKE '%#可选%'
        """)
        results = conn.execute(query).fetchall()
        
        print(f"[INFO] 找到 {len(results)} 条需要修复的记录")
        
        if not results:
            print("[INFO] 没有需要修复的记录")
            return
        
        # 生成正确的COS域名
        cos_domain = Config.COS_DOMAIN.strip() if Config.COS_DOMAIN else ''
        # 如果域名为空或包含注释，使用默认COS域名
        if not cos_domain or '#' in cos_domain or '可选' in cos_domain:
            base_url = f"https://{Config.COS_BUCKET}.cos.{Config.COS_REGION}.myqcloud.com"
        else:
            # 清理域名（去掉https://前缀）
            clean_domain = cos_domain.replace('https://', '').replace('http://', '').strip('/')
            base_url = f"https://{clean_domain}"
        
        fixed_count = 0
        for row in results:
            img_id, prop_id, old_url, cos_key, order_idx = row
            
            # 从image_url或cos_key中提取object_key
            object_key = None
            if cos_key:
                object_key = cos_key
            elif old_url:
                # 从URL中提取object_key（去除无效域名部分）
                parts = old_url.split('/property-images/')
                if len(parts) > 1:
                    object_key = 'property-images/' + parts[1]
                else:
                    # 尝试其他分割方式
                    parts = old_url.split('/')
                    if 'property-images' in parts:
                        idx = parts.index('property-images')
                        object_key = '/'.join(parts[idx:])
            
            if object_key:
                new_url = f"{base_url}/{object_key}"
                # 更新数据库
                update_query = text("""
                    UPDATE property_images
                    SET image_url = :new_url
                    WHERE id = :img_id
                """)
                conn.execute(update_query, {"new_url": new_url, "img_id": img_id})
                fixed_count += 1
                print(f"[OK] 修复记录 ID={img_id}, property_id={prop_id}, order_index={order_idx}")
                print(f"     旧URL: {old_url}")
                print(f"     新URL: {new_url}")
            else:
                print(f"[WARN] 无法提取object_key，跳过记录 ID={img_id}, URL={old_url}")
        
        print(f"\n[SUCCESS] 修复完成，共修复 {fixed_count} 条记录")


def main():
    fix_invalid_image_urls()


if __name__ == '__main__':
    main()

