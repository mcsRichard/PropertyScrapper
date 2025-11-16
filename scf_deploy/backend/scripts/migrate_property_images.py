import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_DIR)

from models.database import engine
from sqlalchemy import text


def column_exists(conn, table_name: str, column_name: str) -> bool:
    q = text(
        """
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = :t AND COLUMN_NAME = :c
        LIMIT 1
        """
    )
    res = conn.execute(q, {"t": table_name, "c": column_name}).first()
    return res is not None


def index_exists(conn, schema: str, table_name: str, index_name: str) -> bool:
    q = text(
        """
        SELECT 1 FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i
        LIMIT 1
        """
    )
    res = conn.execute(q, {"t": table_name, "i": index_name}).first()
    return res is not None


def migrate_property_images_table():
    table = "property_images"
    with engine.begin() as conn:
        # 添加缺失列（逐列检测，避免使用 IF NOT EXISTS）
        add_columns = [
            ("source_url", "VARCHAR(500) NULL"),
            ("cos_key", "VARCHAR(500) NULL"),
            ("image_path", "VARCHAR(500) NULL"),
            ("order_index", "INT DEFAULT 0"),
            ("is_primary", "TINYINT(1) DEFAULT 0"),
            ("width", "INT NULL"),
            ("height", "INT NULL"),
            ("created_at", "DATETIME NULL DEFAULT CURRENT_TIMESTAMP")
        ]
        for col, ddl in add_columns:
            if not column_exists(conn, table, col):
                sql = f"ALTER TABLE {table} ADD COLUMN {col} {ddl};"
                try:
                    conn.exec_driver_sql(sql)
                    print(f"[OK] Added column {col}")
                except Exception as e:
                    print(f"[WARN] Add column {col} failed/skipped: {e}")

        # 修改 property_id 为 NOT NULL（若需要）
        try:
            conn.exec_driver_sql(f"ALTER TABLE {table} MODIFY COLUMN property_id INT NOT NULL;")
        except Exception as e:
            print(f"[WARN] Modify property_id NOT NULL skipped: {e}")

        # 创建索引（存在则跳过）
        indexes = [
            ("uq_property_image_order", "UNIQUE INDEX", "(property_id, order_index)"),
            ("uq_property_image_cos_key", "UNIQUE INDEX", "(cos_key)"),
            ("idx_property_id_created", "INDEX", "(property_id, created_at)"),
            ("idx_property_is_primary", "INDEX", "(is_primary)")
        ]
        for name, kind, cols in indexes:
            if not index_exists(conn, None, table, name):
                sql = f"CREATE {kind} {name} ON {table} {cols};"
                try:
                    conn.exec_driver_sql(sql)
                    print(f"[OK] Created index {name}")
                except Exception as e:
                    print(f"[WARN] Create index {name} failed/skipped: {e}")

    print("[SUCCESS] property_images migration completed (idempotent)")


def main():
    migrate_property_images_table()


if __name__ == '__main__':
    main()


