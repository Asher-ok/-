#!/usr/bin/env python3
import sys
import uuid
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.database import engine
from scripts.seed_invoice_items_from_images import build_seed_groups


def normalize_item_code(code: str | None, reference_code: str | None = None) -> str | None:
    if not code:
        return None
    normalized = str(code).strip()
    if normalized.endswith("...") and reference_code:
        base = normalized[:-3].strip()
        base_parts = [p for p in base.split("_") if p]
        ref_parts = [p for p in str(reference_code).strip().split("_") if p]
        if len(base_parts) >= 2 and len(ref_parts) >= len(base_parts):
            return "_".join(base_parts + ref_parts[len(base_parts) :])
        return base
    return normalized


def ensure_tables(conn):
    conn.execute(text("PRAGMA foreign_keys=ON"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_service_level1 (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_service_level2 (
            id TEXT PRIMARY KEY,
            level1_id TEXT NOT NULL,
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(level1_id) REFERENCES invoice_service_level1(id)
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_svc_l2_l1_name ON invoice_service_level2(level1_id, name)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l2_l1 ON invoice_service_level2(level1_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l2_active ON invoice_service_level2(is_active)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_service_level3 (
            id TEXT PRIMARY KEY,
            level1_id TEXT NOT NULL,
            level2_id TEXT,
            name TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(level1_id) REFERENCES invoice_service_level1(id),
            FOREIGN KEY(level2_id) REFERENCES invoice_service_level2(id)
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_svc_l3_key ON invoice_service_level3(level1_id, level2_id, name)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l3_l1 ON invoice_service_level3(level1_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l3_l2 ON invoice_service_level3(level2_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_l3_active ON invoice_service_level3(is_active)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_service_codes (
            id TEXT PRIMARY KEY,
            level3_id TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            price NUMERIC,
            unit TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(level3_id) REFERENCES invoice_service_level3(id)
        )
    """))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_code_l3 ON invoice_service_codes(level3_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_svc_code_active ON invoice_service_codes(is_active)"))


def get_or_create_level1(conn, name: str, sort_order: int) -> str:
    row = conn.execute(
        text("SELECT id FROM invoice_service_level1 WHERE name = :name LIMIT 1"),
        {"name": name},
    ).fetchone()
    if row:
        conn.execute(
            text("""
                UPDATE invoice_service_level1
                SET sort_order = :sort_order, is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {"id": row[0], "sort_order": sort_order},
        )
        return row[0]

    new_id = str(uuid.uuid4())
    conn.execute(
        text("""
            INSERT INTO invoice_service_level1 (id, name, sort_order, is_active, created_at)
            VALUES (:id, :name, :sort_order, 1, CURRENT_TIMESTAMP)
        """),
        {"id": new_id, "name": name, "sort_order": sort_order},
    )
    return new_id


def get_or_create_level2(conn, level1_id: str, name: str, sort_order: int) -> str:
    row = conn.execute(
        text("""
            SELECT id
            FROM invoice_service_level2
            WHERE level1_id = :level1_id AND name = :name
            LIMIT 1
        """),
        {"level1_id": level1_id, "name": name},
    ).fetchone()
    if row:
        conn.execute(
            text("""
                UPDATE invoice_service_level2
                SET sort_order = :sort_order, is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {"id": row[0], "sort_order": sort_order},
        )
        return row[0]

    new_id = str(uuid.uuid4())
    conn.execute(
        text("""
            INSERT INTO invoice_service_level2 (id, level1_id, name, sort_order, is_active, created_at)
            VALUES (:id, :level1_id, :name, :sort_order, 1, CURRENT_TIMESTAMP)
        """),
        {"id": new_id, "level1_id": level1_id, "name": name, "sort_order": sort_order},
    )
    return new_id


def get_or_create_level3(conn, level1_id: str, level2_id: str | None, name: str, sort_order: int) -> str:
    row = conn.execute(
        text("""
            SELECT id
            FROM invoice_service_level3
            WHERE level1_id = :level1_id
              AND ((level2_id = :level2_id) OR (level2_id IS NULL AND :level2_id IS NULL))
              AND name = :name
            LIMIT 1
        """),
        {"level1_id": level1_id, "level2_id": level2_id, "name": name},
    ).fetchone()
    if row:
        conn.execute(
            text("""
                UPDATE invoice_service_level3
                SET sort_order = :sort_order, is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {"id": row[0], "sort_order": sort_order},
        )
        return row[0]

    new_id = str(uuid.uuid4())
    conn.execute(
        text("""
            INSERT INTO invoice_service_level3 (id, level1_id, level2_id, name, sort_order, is_active, created_at)
            VALUES (:id, :level1_id, :level2_id, :name, :sort_order, 1, CURRENT_TIMESTAMP)
        """),
        {"id": new_id, "level1_id": level1_id, "level2_id": level2_id, "name": name, "sort_order": sort_order},
    )
    return new_id


def upsert_code(conn, level3_id: str, code: str, price: Decimal | None, unit: str | None):
    row = conn.execute(
        text("SELECT id FROM invoice_service_codes WHERE code = :code LIMIT 1"),
        {"code": code},
    ).fetchone()

    if row:
        conn.execute(
            text("""
                UPDATE invoice_service_codes
                SET
                    level3_id = :level3_id,
                    price = :price,
                    unit = :unit,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {
                "id": row[0],
                "level3_id": level3_id,
                "price": str(price) if price is not None else None,
                "unit": unit,
            },
        )
        return

    conn.execute(
        text("""
            INSERT INTO invoice_service_codes (
                id, level3_id, code, price, unit, is_active, created_at
            ) VALUES (
                :id, :level3_id, :code, :price, :unit, 1, CURRENT_TIMESTAMP
            )
        """),
        {
            "id": str(uuid.uuid4()),
            "level3_id": level3_id,
            "code": code,
            "price": str(price) if price is not None else None,
            "unit": unit,
        },
    )


def seed():
    groups = build_seed_groups()

    with engine.begin() as conn:
        ensure_tables(conn)

        l1_map: dict[str, str] = {}
        l2_map: dict[tuple[str, str], str] = {}
        l3_map: dict[tuple[str, str | None, str], str] = {}

        code_count = 0
        for l1_idx, group in enumerate(groups, start=1):
            path = group.get("path") or []
            if not path:
                continue

            level1_name = str(path[0]).strip()
            l1_id = l1_map.get(level1_name)
            if not l1_id:
                l1_id = get_or_create_level1(conn, level1_name, l1_idx)
                l1_map[level1_name] = l1_id

            level2_id = None
            level2_name = None
            if len(path) >= 2:
                level2_name = str(path[1]).strip()
                l2_key = (l1_id, level2_name)
                level2_id = l2_map.get(l2_key)
                if not level2_id:
                    level2_id = get_or_create_level2(conn, l1_id, level2_name, sort_order=1)
                    l2_map[l2_key] = level2_id

            last_code = None
            for l3_idx, row in enumerate(group.get("rows") or [], start=1):
                item_code, item_name, price, unit = row
                item_name = str(item_name).strip()

                l3_key = (l1_id, level2_id, item_name)
                l3_id = l3_map.get(l3_key)
                if not l3_id:
                    l3_id = get_or_create_level3(conn, l1_id, level2_id, item_name, l3_idx)
                    l3_map[l3_key] = l3_id

                code_full = normalize_item_code(str(item_code).strip(), last_code)
                if not code_full:
                    continue
                upsert_code(conn, l3_id, code_full, price, unit)
                last_code = code_full
                code_count += 1

        l1_total = conn.execute(text("SELECT COUNT(1) FROM invoice_service_level1")).fetchone()[0]
        l2_total = conn.execute(text("SELECT COUNT(1) FROM invoice_service_level2")).fetchone()[0]
        l3_total = conn.execute(text("SELECT COUNT(1) FROM invoice_service_level3")).fetchone()[0]
        code_total = conn.execute(text("SELECT COUNT(1) FROM invoice_service_codes")).fetchone()[0]

        print(
            f"已写入/更新：一级 {l1_total}，二级 {l2_total}，三级 {l3_total}，编码 {code_total}（本次处理 {code_count} 行编码）"
        )


if __name__ == "__main__":
    seed()

