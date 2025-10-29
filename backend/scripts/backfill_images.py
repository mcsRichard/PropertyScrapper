import os
import sys
import time
from typing import List

# 将项目根目录与 backend 目录加入路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_DIR)

from models.database import DatabaseManager
from utils.database import PropertyService
from utils.cos_uploader import create_cos_uploader
from scripts.migrate_property_images import migrate_property_images_table

# 复用顶层 Scrapper 的详情页图片提取逻辑
SCRAPPER_PATH = os.path.join(PROJECT_ROOT, 'Scrapper.py')
if os.path.exists(SCRAPPER_PATH):
    import importlib.util
    spec = importlib.util.spec_from_file_location('scrapper_module', SCRAPPER_PATH)
    scrapper_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scrapper_module)  # type: ignore
    fetch_all_images_for_property = getattr(scrapper_module, 'fetch_all_images_for_property', None)
else:
    fetch_all_images_for_property = None


def backfill_images(limit_per_property: int = 30, sleep_between_requests: float = 0.2, dry_run: bool = False):
    # 先执行一次幂等迁移，避免缺列错误
    try:
        migrate_property_images_table()
    except Exception as e:
        print(f"[WARN] 数据库迁移执行出现问题（将继续尝试回填）: {e}")
    dbm = DatabaseManager()
    db = dbm.get_session()
    property_service = PropertyService(db)

    # 初始化 COS 上传器
    try:
        from config import Config
        cos_uploader = create_cos_uploader(Config())
    except Exception as e:
        print(f"[ERROR] 初始化COS失败: {e}")
        dbm.close_session(db)
        return

    # 读取所有房源（按创建时间逆序）
    try:
        from models.database import Property
        properties = (
            db.query(Property)
            .order_by(Property.created_at.desc())
            .all()
        )
    except Exception as e:
        print(f"[ERROR] 读取房源失败: {e}")
        dbm.close_session(db)
        return

    print(f"[INFO] 待回填房源数量: {len(properties)}")

    processed = 0
    for p in properties:
        processed += 1
        if not p.url:
            continue
        print(f"\n[PROPERTY] #{processed} id={p.id} url={p.url}")

        if not fetch_all_images_for_property:
            print("[WARN] 未找到详情页图片抓取函数，跳过")
            continue

        try:
            src_urls: List[str] = fetch_all_images_for_property(p.url)  # type: ignore
        except Exception as e:
            print(f"[ERROR] 抓取图片失败: {e}")
            continue

        if not src_urls:
            print("[INFO] 未发现图片，跳过")
            continue

        # 限制单房源最大图片数
        src_urls = src_urls[:limit_per_property]
        print(f"[INFO] 发现图片 {len(src_urls)} 张，开始上传并入库（幂等）")

        for idx, src in enumerate(src_urls):
            try:
                # 上传到 COS（幂等）
                cos_url = None
                if not dry_run:
                    cos_url = cos_uploader.upload_image_from_url(src, object_key=None, key_prefix='property-images', referer=p.url)

                # 写入 DB（幂等 upsert）
                if not dry_run:
                    property_service.upsert_property_image(
                        property_id=p.id,
                        image_data={
                            'source_url': src,
                            'image_url': cos_url or src,
                            'cos_key': None,  # 由上传器决定；若需要可反推解析
                            'order_index': idx,  # 从0开始
                            'is_primary': idx == 0
                        }
                    )
                print(f"[OK] 第{idx}张 已处理: {src}")
            except Exception as e:
                print(f"[ERROR] 第{idx}张 处理失败: {e}")

            time.sleep(sleep_between_requests)

    dbm.close_session(db)
    print("\n[SUCCESS] 回填完成")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='回填房源多图到 COS 和 property_images')
    parser.add_argument('--max-per-property', type=int, default=30, help='每个房源最多处理的图片数')
    parser.add_argument('--sleep', type=float, default=0.2, help='每张图片之间的休眠秒数')
    parser.add_argument('--dry-run', action='store_true', help='仅打印不落库/上传')
    args = parser.parse_args()

    backfill_images(limit_per_property=args.max_per_property, sleep_between_requests=args.sleep, dry_run=args.dry_run)


if __name__ == '__main__':
    main()


