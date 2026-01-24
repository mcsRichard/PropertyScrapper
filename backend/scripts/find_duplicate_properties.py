#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
查找并清理重复房源：按 description_chinese 归一化后分组，相同介绍的视为同一套房。
通常因同一套房用不同 URL 导入多次导致（如不同来源、不同 query 参数）。
例如 AI 搜索 UCL 时，前几条 WC1X 一居室 £2058/£1950 介绍相同，即属此类重复。

用法（在项目根目录执行）:
  python backend/scripts/find_duplicate_properties.py              # 仅报告重复
  python backend/scripts/find_duplicate_properties.py --dry-run    # 同上
  python backend/scripts/find_duplicate_properties.py --delete     # 删除重复，每组保留 id 最小的一条

Windows 控制台若遇编码错误，可先设置: $env:PYTHONIOENCODING="utf-8"
"""
from __future__ import annotations

import os
import re
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import text
from sqlalchemy.orm import Session

from models.database import SessionLocal


def normalize_description(s: str | None) -> str:
    """归一化介绍文本：去首尾空白、规整空白字符，便于比对。"""
    if not s or not isinstance(s, str):
        return ""
    t = s.strip()
    t = re.sub(r"[\s\u3000]+", " ", t)
    return t


def find_duplicate_groups(session: Session) -> list[tuple[str, list[dict]]]:
    """
    按归一化后的 description_chinese 分组，返回 (normalized_desc, [rows])，
    仅包含 size > 1 的组。每条 row 含 id, url, price, price_numeric, title, postcode, bedrooms。
    """
    q = session.execute(
        text("""
            SELECT id, url, price, price_numeric, title, postcode, bedrooms,
                   description_chinese
            FROM properties
            WHERE description_chinese IS NOT NULL AND description_chinese != ''
            ORDER BY id
        """)
    )
    rows = q.fetchall()
    groups: dict[str, list[dict]] = {}
    for r in rows:
        desc = r.description_chinese if hasattr(r, "description_chinese") else (r[7] if len(r) > 7 else None)
        key = normalize_description(desc)
        if not key:
            continue
        row = {
            "id": r.id,
            "url": r.url,
            "price": r.price,
            "price_numeric": getattr(r, "price_numeric", None),
            "title": r.title,
            "postcode": r.postcode,
            "bedrooms": r.bedrooms,
        }
        groups.setdefault(key, []).append(row)
    return [(k, v) for k, v in groups.items() if len(v) > 1]


def report_duplicates(groups: list[tuple[str, list[dict]]]) -> None:
    """打印重复组报告。"""
    if not groups:
        print("[INFO] 未发现重复房源（按 description_chinese 归一化分组）。")
        return
    print(f"[INFO] 发现 {len(groups)} 组重复房源（共 {sum(len(g) for _, g in groups)} 条记录）：\n")
    for i, (desc_key, rows) in enumerate(groups, 1):
        keep = min(rows, key=lambda x: x["id"])
        dupes = [r for r in rows if r["id"] != keep["id"]]
        print(f"--- 第 {i} 组（保留 id={keep['id']}，将删除 {len(dupes)} 条）---")
        _preview = (desc_key[:80] + "...") if len(desc_key) > 80 else desc_key
        print(f"  介绍摘要: {_preview}")
        def _row_line(r):
            t = (r["title"] or "")[:50]
            u = (r["url"] or "")[:60]
            if len(r["title"] or "") > 50:
                t += "..."
            if len(r["url"] or "") > 60:
                u += "..."
            return f"  id={r['id']} | {r['price']} | {t} | {r['postcode']} | {u}"
        print(f"  保留: {_row_line(keep)}")
        for d in dupes:
            print(f"  删除: {_row_line(d)}")
        print()


def delete_duplicates(session: Session, groups: list[tuple[str, list[dict]]]) -> int:
    """
    每组保留 id 最小的一条，删除其余。先删 property_images、更新 user_contact_logs，再删 properties。
    返回删除的房产条数。出错时回滚。
    """
    deleted = 0
    try:
        for _desc_key, rows in groups:
            keep = min(rows, key=lambda x: x["id"])
            keep_id = keep["id"]
            dup_ids = [r["id"] for r in rows if r["id"] != keep_id]
            for pid in dup_ids:
                session.execute(text("DELETE FROM property_images WHERE property_id = :pid"), {"pid": pid})
                session.execute(
                    text("UPDATE user_contact_logs SET property_id = :keep_id WHERE property_id = :pid"),
                    {"keep_id": keep_id, "pid": pid},
                )
                session.execute(text("DELETE FROM properties WHERE id = :pid"), {"pid": pid})
                deleted += 1
        session.commit()
    except Exception:
        session.rollback()
        raise
    return deleted


def main() -> None:
    dry_run = "--delete" not in sys.argv
    if dry_run:
        print("[MODE] 仅报告重复（干跑）。要执行删除请加参数: --delete\n")
    else:
        print("[MODE] 将删除重复房源，每组保留 id 最小的一条。\n")

    session = SessionLocal()
    try:
        groups = find_duplicate_groups(session)
        report_duplicates(groups)
        if not groups:
            return
        if dry_run:
            print("[INFO] 未执行删除。确认无误后请使用: python find_duplicate_properties.py --delete")
            return
        n = delete_duplicates(session, groups)
        print(f"[DONE] 已删除 {n} 条重复房源。")
    finally:
        session.close()


if __name__ == "__main__":
    main()
