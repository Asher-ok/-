#!/usr/bin/env python3
import sys
import uuid
from decimal import Decimal
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from core.database import engine


def _ensure_tables(conn):
    conn.execute(text("PRAGMA foreign_keys=ON"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_item_categories (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            name TEXT NOT NULL,
            code TEXT,
            level INTEGER NOT NULL DEFAULT 1,
            path TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(parent_id) REFERENCES invoice_item_categories(id)
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_cat_parent_name ON invoice_item_categories(parent_id, name)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_cat_parent ON invoice_item_categories(parent_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_cat_path ON invoice_item_categories(path)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_cat_active ON invoice_item_categories(is_active)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_item_dict (
            id TEXT PRIMARY KEY,
            category_id TEXT NOT NULL,
            item_code TEXT NOT NULL,
            item_name TEXT NOT NULL,
            spec_default TEXT,
            unit_default TEXT,
            price_default NUMERIC,
            tax_rate_default NUMERIC NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_from_invoice_id TEXT,
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            FOREIGN KEY(category_id) REFERENCES invoice_item_categories(id)
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_item_code ON invoice_item_dict(item_code)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_cat ON invoice_item_dict(category_id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_active ON invoice_item_dict(is_active)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_name ON invoice_item_dict(item_name)"))

    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS invoice_item_dict_versions (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            version_no INTEGER NOT NULL,
            item_code TEXT NOT NULL,
            item_name TEXT NOT NULL,
            spec_default TEXT,
            unit_default TEXT,
            price_default NUMERIC,
            tax_rate_default NUMERIC NOT NULL,
            changed_by TEXT,
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES invoice_item_dict(id)
        )
    """))
    conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uidx_inv_item_ver ON invoice_item_dict_versions(item_id, version_no)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_inv_item_ver_item ON invoice_item_dict_versions(item_id)"))


def _get_or_create_category(conn, parent_id, name: str, sort_order: int = 0, code: str | None = None):
    row = conn.execute(
        text("""
            SELECT id, path, level
            FROM invoice_item_categories
            WHERE name = :name
              AND ((parent_id = :pid) OR (parent_id IS NULL AND :pid IS NULL))
            LIMIT 1
        """),
        {"pid": parent_id, "name": name},
    ).fetchone()
    if row:
        return row[0]

    new_id = str(uuid.uuid4())
    if parent_id:
        parent = conn.execute(
            text("SELECT path, level FROM invoice_item_categories WHERE id = :id LIMIT 1"),
            {"id": parent_id},
        ).fetchone()
        parent_path = parent[0] if parent else "/"
        parent_level = parent[1] if parent else 0
    else:
        parent_path = "/"
        parent_level = 0

    path = f"{parent_path}{new_id}/"
    level = parent_level + 1
    conn.execute(
        text("""
            INSERT INTO invoice_item_categories (
                id, parent_id, name, code, level, path, sort_order, is_active, created_at
            ) VALUES (
                :id, :parent_id, :name, :code, :level, :path, :sort_order, 1, CURRENT_TIMESTAMP
            )
        """),
        {
            "id": new_id,
            "parent_id": parent_id,
            "name": name,
            "code": code,
            "level": level,
            "path": path,
            "sort_order": sort_order,
        },
    )
    return new_id


def _upsert_item(conn, category_id: str, item_code: str, item_name: str, price_default, unit_default: str | None, spec_default: str | None):
    existing = conn.execute(
        text("SELECT id FROM invoice_item_dict WHERE item_code = :code LIMIT 1"),
        {"code": item_code},
    ).fetchone()

    if existing:
        item_id = existing[0]
        conn.execute(
            text("""
                UPDATE invoice_item_dict
                SET
                    category_id = :category_id,
                    item_name = :item_name,
                    spec_default = :spec_default,
                    unit_default = :unit_default,
                    price_default = :price_default,
                    tax_rate_default = 0,
                    is_active = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
            """),
            {
                "id": item_id,
                "category_id": category_id,
                "item_name": item_name,
                "spec_default": spec_default,
                "unit_default": unit_default,
                "price_default": str(price_default) if price_default is not None else None,
            },
        )
    else:
        item_id = str(uuid.uuid4())
        conn.execute(
            text("""
                INSERT INTO invoice_item_dict (
                    id, category_id, item_code, item_name, spec_default, unit_default,
                    price_default, tax_rate_default, is_active, created_at
                ) VALUES (
                    :id, :category_id, :item_code, :item_name, :spec_default, :unit_default,
                    :price_default, 0, 1, CURRENT_TIMESTAMP
                )
            """),
            {
                "id": item_id,
                "category_id": category_id,
                "item_code": item_code,
                "item_name": item_name,
                "spec_default": spec_default,
                "unit_default": unit_default,
                "price_default": str(price_default) if price_default is not None else None,
            },
        )

    ver = conn.execute(
        text("SELECT MAX(version_no) FROM invoice_item_dict_versions WHERE item_id = :item_id"),
        {"item_id": item_id},
    ).fetchone()
    max_ver = ver[0] if ver and ver[0] is not None else 0
    if max_ver == 0:
        conn.execute(
            text("""
                INSERT INTO invoice_item_dict_versions (
                    id, item_id, version_no, item_code, item_name, spec_default, unit_default,
                    price_default, tax_rate_default, changed_at
                ) VALUES (
                    :id, :item_id, 1, :item_code, :item_name, :spec_default, :unit_default,
                    :price_default, 0, CURRENT_TIMESTAMP
                )
            """),
            {
                "id": str(uuid.uuid4()),
                "item_id": item_id,
                "item_code": item_code,
                "item_name": item_name,
                "spec_default": spec_default,
                "unit_default": unit_default,
                "price_default": str(price_default) if price_default is not None else None,
            },
        )


def build_seed_groups():
    return [
        {
            "path": ["ASSISTANCE TO ACCESS COMMUNITY, SOCIAL & RECREATIONAL ACTIVITIES", "Assistance to access community-based social & recreational activities - Standard"],
            "rows": [
                ("04_104_0125_6_1", "Weekday Daytime (6am to 8pm)", Decimal("70.23"), "Hour"),
                ("04_103_0125_6_1", "Weekday Evening (8pm - midnight)", Decimal("77.38"), "Hour"),
                ("04_105_0125_6_1", "Saturday", Decimal("98.83"), "Hour"),
                ("04_106_0125_6_1", "Sunday", Decimal("127.43"), "Hour"),
                ("04_102_0125_6_1", "Public Holiday", Decimal("156.03"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE TO ACCESS COMMUNITY, SOCIAL & RECREATIONAL ACTIVITIES", "Assistance to access community-based social & recreational activities - High Intensity"],
            "rows": [
                ("04_400_0104_1_1", "Weekday Daytime (6am to 8pm)", Decimal("75.98"), "Hour"),
                ("04_401_0104_1_1", "Weekday Evening (8pm - midnight)", Decimal("83.72"), "Hour"),
                ("04_402_0104_1_1", "Saturday", Decimal("106.93"), "Hour"),
                ("04_403_0104_1_1", "Sunday", Decimal("137.87"), "Hour"),
                ("04_404_0104_1_1", "Public Holiday", Decimal("168.81"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE TO ACCESS COMMUNITY, SOCIAL & RECREATIONAL ACTIVITIES", "Intensive and Complex Behaviour Supports"],
            "rows": [
                ("04_450_0125_1_1", "Weekday Daytime (6am to 8pm)", Decimal("75.98"), "Hour"),
                ("04_451_0125_1_1", "Weekday Evening (8pm - midnight)", Decimal("83.72"), "Hour"),
                ("04_452_0125_1_1", "Saturday", Decimal("106.93"), "Hour"),
                ("04_453_0125_1_1", "Sunday", Decimal("137.87"), "Hour"),
                ("04_454_0125_1_1", "Public Holiday", Decimal("168.81"), "Hour"),
            ],
        },
        {
            "path": ["ACTIVITY BASED TRANSPORT"],
            "rows": [
                ("ACTIVITY_TRANSPORT_NOT_MODIFIED", "Activity Based Transport (Not Modified Vehicle)", Decimal("0.99"), "KM"),
                ("ACTIVITY_TRANSPORT_MODIFIED", "Activity Based Transport (Modified Vehicle)", Decimal("2.76"), "KM"),
                ("04_590_0125_6_1", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("04_591_0136_6_1", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("04_592_0104_6_1", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("04_821_0133_6_1", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("07_501_0106_6_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("08_590_0106_2_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("09_590_0106_6_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("09_591_0117_6_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("10_590_0102_5_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("10_590_0133_5_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("11_590_0117_7_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
                ("13_590_0102_4_3", "Activity Based Transport - claimable item", Decimal("0.99"), "KM"),
            ],
            "spec_note": "Not Modified Vehicle: 0.99 per km; Modified Vehicle: 2.76 per km",
        },
        {
            "path": ["CENTRE CAPITAL COSTS"],
            "rows": [
                ("04_599_0104_6_1", "Centre Capital Cost", Decimal("2.59"), "Hour"),
                ("10_599_0133_5_3", "Centre Capital Cost", Decimal("2.59"), "Hour"),
            ],
        },
        {
            "path": ["EMPLOYMENT SUPPORTS", "Supports in Employment"],
            "rows": [
                ("04_801_0133_5_1", "Supports in Employment - Weekday Daytime", Decimal("70.23"), "Hour"),
                ("04_802_0133_5_1", "Supports in Employment - Weekday Evening", Decimal("77.38"), "Hour"),
                ("04_803_0133_5_1", "Supports in Employment - Saturday", Decimal("98.83"), "Hour"),
                ("04_804_0133_5_1", "Supports in Employment - Sunday", Decimal("127.43"), "Hour"),
                ("04_805_0133_5_1", "Supports in Employment - Public Holiday", Decimal("156.03"), "Hour"),
            ],
        },
        {
            "path": ["ESTABLISHMENT FEE FOR PERSONAL CARE/PARTICIPATION"],
            "rows": [
                ("01_049_0104_1_1", "Establishment Fee for Personal Care/Participation", Decimal("702.30"), "Each"),
                ("04_049_0104_1_1", "Establishment Fee for Personal Care/Participation", Decimal("702.30"), "Each"),
            ],
        },
        {
            "path": ["DISABILITY RELATED HEALTH SUPPORTS BY A NURSE", "CB Daily Activity"],
            "rows": [
                ("15_400_0114_1_3", "Enrolled Nurse - Weekday Daytime", Decimal("99.88"), "Hour"),
                ("15_401_0114_1_3", "Enrolled Nurse - Evening", Decimal("110.18"), "Hour"),
                ("15_405_0114_1_3", "Enrolled Nurse - Night", Decimal("112.22"), "Hour"),
                ("15_402_0114_1_3", "Enrolled Nurse - Saturday", Decimal("142.48"), "Hour"),
                ("15_403_0114_1_3", "Enrolled Nurse - Sunday", Decimal("163.79"), "Hour"),
                ("15_404_0114_1_3", "Enrolled Nurse - Public Holiday", Decimal("185.08"), "Hour"),
                ("15_406_0114_1_3", "Registered Nurse - Weekday Daytime", Decimal("123.65"), "Hour"),
                ("15_407_0114_1_3", "Registered Nurse - Evening", Decimal("136.41"), "Hour"),
                ("15_411_0114_1_3", "Registered Nurse - Night", Decimal("138.95"), "Hour"),
                ("15_408_0114_1_3", "Registered Nurse - Saturday", Decimal("176.47"), "Hour"),
                ("15_409_0114_1_3", "Registered Nurse - Sunday", Decimal("202.87"), "Hour"),
                ("15_410_0114_1_3", "Registered Nurse - Public Holiday", Decimal("229.27"), "Hour"),
                ("15_412_0114_1_3", "Clinical Nurse - Weekday Daytime", Decimal("143.04"), "Hour"),
                ("15_413_0114_1_3", "Clinical Nurse - Evening", Decimal("157.77"), "Hour"),
                ("15_417_0114_1_3", "Clinical Nurse - Night", Decimal("160.73"), "Hour"),
                ("15_414_0114_1_3", "Clinical Nurse - Saturday", Decimal("204.12"), "Hour"),
                ("15_415_0114_1_3", "Clinical Nurse - Sunday", Decimal("234.67"), "Hour"),
                ("15_416_0114_1_3", "Clinical Nurse - Public Holiday", Decimal("265.20"), "Hour"),
                ("15_418_0114_1_3", "Clinical Nurse Consultant - Weekday Daytime", Decimal("169.16"), "Hour"),
                ("15_419_0114_1_3", "Clinical Nurse Consultant - Evening", Decimal("186.63"), "Hour"),
                ("15_423_0114_1_3", "Clinical Nurse Consultant - Night", Decimal("190.12"), "Hour"),
                ("15_420_0114_1_3", "Clinical Nurse Consultant - Saturday", Decimal("241.52"), "Hour"),
                ("15_421_0114_1_3", "Clinical Nurse Consultant - Sunday", Decimal("277.69"), "Hour"),
                ("15_422_0114_1_3", "Clinical Nurse Consultant - Public Holiday", Decimal("313.86"), "Hour"),
                ("15_424_0114_1_3", "Nurse Practitioner - Weekday Daytime", Decimal("176.85"), "Hour"),
                ("15_425_0114_1_3", "Nurse Practitioner - Evening", Decimal("195.09"), "Hour"),
                ("15_429_0114_1_3", "Nurse Practitioner - Night", Decimal("198.75"), "Hour"),
                ("15_426_0114_1_3", "Nurse Practitioner - Saturday", Decimal("252.51"), "Hour"),
                ("15_427_0114_1_3", "Nurse Practitioner - Sunday", Decimal("293.20"), "Hour"),
                ("15_428_0114_1_3", "Nurse Practitioner - Public Holiday", Decimal("328.16"), "Hour"),
            ],
        },
        {
            "path": ["DISABILITY RELATED HEALTH SUPPORTS BY A NURSE", "Daily Activities"],
            "rows": [
                ("01_600_0114_1_1", "Enrolled Nurse - Weekday Daytime", Decimal("99.88"), "Hour"),
                ("01_601_0114_1_1", "Enrolled Nurse - Evening", Decimal("110.18"), "Hour"),
                ("01_605_0114_1_1", "Enrolled Nurse - Night", Decimal("112.22"), "Hour"),
                ("01_602_0114_1_1", "Enrolled Nurse - Saturday", Decimal("142.48"), "Hour"),
                ("01_603_0114_1_1", "Enrolled Nurse - Sunday", Decimal("163.79"), "Hour"),
                ("01_604_0114_1_1", "Enrolled Nurse - Public Holiday", Decimal("185.08"), "Hour"),
                ("01_606_0114_1_1", "Registered Nurse - Weekday Daytime", Decimal("123.65"), "Hour"),
                ("01_607_0114_1_1", "Registered Nurse - Evening", Decimal("136.41"), "Hour"),
                ("01_611_0114_1_1", "Registered Nurse - Night", Decimal("138.95"), "Hour"),
                ("01_608_0114_1_1", "Registered Nurse - Saturday", Decimal("176.47"), "Hour"),
                ("01_609_0114_1_1", "Registered Nurse - Sunday", Decimal("202.87"), "Hour"),
                ("01_610_0114_1_1", "Registered Nurse - Public Holiday", Decimal("229.27"), "Hour"),
                ("01_612_0114_1_1", "Clinical Nurse - Weekday Daytime", Decimal("143.04"), "Hour"),
                ("01_613_0114_1_1", "Clinical Nurse - Evening", Decimal("157.77"), "Hour"),
                ("01_617_0114_1_1", "Clinical Nurse - Night", Decimal("160.73"), "Hour"),
                ("01_614_0114_1_1", "Clinical Nurse - Saturday", Decimal("204.12"), "Hour"),
                ("01_615_0114_1_1", "Clinical Nurse - Sunday", Decimal("234.67"), "Hour"),
                ("01_616_0114_1_1", "Clinical Nurse - Public Holiday", Decimal("265.20"), "Hour"),
                ("01_618_0114_1_1", "Clinical Nurse Consultant - Weekday Daytime", Decimal("169.16"), "Hour"),
                ("01_619_0114_1_1", "Clinical Nurse Consultant - Evening", Decimal("186.63"), "Hour"),
                ("01_623_0114_1_1", "Clinical Nurse Consultant - Night", Decimal("190.12"), "Hour"),
                ("01_620_0114_1_1", "Clinical Nurse Consultant - Saturday", Decimal("241.52"), "Hour"),
                ("01_621_0114_1_1", "Clinical Nurse Consultant - Sunday", Decimal("277.69"), "Hour"),
                ("01_622_0114_1_1", "Clinical Nurse Consultant - Public Holiday", Decimal("313.86"), "Hour"),
                ("01_624_0114_1_1", "Nurse Practitioner - Weekday Daytime", Decimal("176.85"), "Hour"),
                ("01_625_0114_1_1", "Nurse Practitioner - Evening", Decimal("195.09"), "Hour"),
                ("01_629_0114_1_1", "Nurse Practitioner - Night", Decimal("198.75"), "Hour"),
                ("01_626_0114_1_1", "Nurse Practitioner - Saturday", Decimal("252.51"), "Hour"),
                ("01_627_0114_1_1", "Nurse Practitioner - Sunday", Decimal("293.20"), "Hour"),
                ("01_628_0114_1_1", "Nurse Practitioner - Public Holiday", Decimal("328.16"), "Hour"),
            ],
        },
        {
            "path": ["SUPPORT COORDINATION"],
            "rows": [
                ("07_001_0106_8_3", "Level 1: Support Connection", Decimal("80.06"), "Hour"),
                ("07_002_0106_8_3", "Level 2: Coordination of Supports", Decimal("100.14"), "Hour"),
                ("07_004_0132_8_3", "Level 3: Specialist Support Coordination", Decimal("190.54"), "Hour"),
            ],
        },
        {
            "path": ["PSYCHOSOCIAL RECOVERY COACHING"],
            "rows": [
                ("07_101_0106_6_3", "Psychosocial Recovery Coaching - Weekday Daytime", Decimal("105.43"), "Hour"),
                ("07_102_0106_6_3", "Psychosocial Recovery Coaching - Evening", Decimal("116.16"), "Hour"),
                ("07_103_0106_6_3", "Psychosocial Recovery Coaching - Night", Decimal("118.31"), "Hour"),
                ("07_104_0106_6_3", "Psychosocial Recovery Coaching - Saturday", Decimal("148.36"), "Hour"),
                ("07_105_0106_6_3", "Psychosocial Recovery Coaching - Sunday", Decimal("191.29"), "Hour"),
                ("07_106_0106_6_3", "Psychosocial Recovery Coaching - Public Holiday", Decimal("234.23"), "Hour"),
            ],
        },
        {
            "path": ["IMPROVED LIVING ARRANGEMENTS"],
            "rows": [
                ("08_005_0106_2_3", "Assistance With Accommodation and Tenancy Obligations", Decimal("80.06"), "Hour"),
            ],
        },
        {
            "path": ["INCREASED SOCIAL AND COMMUNITY PARTICIPATION"],
            "rows": [
                ("09_006_0106_6_3", "Life Transition Planning", Decimal("80.06"), "Hour"),
                ("09_009_0117_6_3", "Skills Development and Training", Decimal("80.06"), "Hour"),
            ],
        },
        {
            "path": ["FINDING AND KEEPING A JOB"],
            "rows": [
                ("10_011_0128_5_3", "Employment Related Assessment, Counselling and Advice", Decimal("193.99"), "Hour"),
                ("10_016_0102_5_3", "Employment Assistance", Decimal("80.06"), "Hour"),
                ("10_002_0106_8_3", "Level 2: Coordination of Supports", Decimal("100.14"), "Hour"),
                ("10_101_0106_6_3", "Psychosocial Recovery Coaching – Weekday Daytime", Decimal("105.43"), "Hour"),
                ("10_806_0133_5_1", "Supports in Employment - Weekday Daytime", Decimal("70.23"), "Hour"),
            ],
        },
        {
            "path": ["IMPROVED HEALTH AND WELLBEING"],
            "rows": [
                ("12_025_0128_3_3", "Dietitian on managing diet for health and well-being", Decimal("188.99"), "Hour"),
                ("12_027_0126_3_3", "Exercise Physiologist", Decimal("166.99"), "Hour"),
                ("12_029_0126_3_3", "Personal Trainer", Decimal("67.00"), "Hour"),
            ],
        },
        {
            "path": ["IMPROVED LEARNING"],
            "rows": [
                ("13_030_0102_4_3", "Transition Through School and To Further Education", Decimal("80.06"), "Hour"),
            ],
        },
        {
            "path": ["IMPROVED LIFE CHOICES"],
            "rows": [
                ("14_034_0127_8_3", "Plan Management - Monthly Fee (per month)", Decimal("104.45"), "Each"),
            ],
        },
        {
            "path": ["IMPROVED RELATIONSHIPS"],
            "rows": [
                ("11_022_0110_7_3", "Specialist Behavioural Intervention Support", Decimal("232.99"), "Hour"),
                ("11_023_0110_7_3", "Behaviour Management Plan Including Training In Behaviour Management", Decimal("232.99"), "Hour"),
                ("11_024_0117_7_3", "Individual Social Skills Development", Decimal("80.06"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE WITH SELF-CARE ACTIVITIES", "Assistance with self-care activities - Standard needs"],
            "rows": [
                ("01_011_0107_1_1", "Weekday Daytime (6am to 8pm)", Decimal("70.23"), "Hour"),
                ("01_015_0107_1_1", "Weekday Evening (8pm - midnight)", Decimal("77.38"), "Hour"),
                ("01_013_0107_1_1", "Saturday", Decimal("98.83"), "Hour"),
                ("01_014_0107_1_1", "Sunday", Decimal("127.43"), "Hour"),
                ("01_012_0107_1_1", "Public Holiday", Decimal("156.03"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE WITH SELF-CARE ACTIVITIES", "Assistance with self-care activities - High Intensity"],
            "rows": [
                ("01_400_0104_1_1", "Weekday Daytime (6am to 8pm)", Decimal("75.98"), "Hour"),
                ("01_401_0104_1_1", "Weekday Evening (8pm - midnight)", Decimal("83.72"), "Hour"),
                ("01_402_0104_1_1", "Saturday", Decimal("106.93"), "Hour"),
                ("01_403_0104_1_1", "Sunday", Decimal("137.87"), "Hour"),
                ("01_404_0104_1_1", "Public Holiday", Decimal("168.81"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE WITH SELF-CARE ACTIVITIES", "Intensive and Complex Behaviour Supports"],
            "rows": [
                ("01_450_0107_1_1", "Weekday Daytime (6am to 8pm)", Decimal("75.98"), "Hour"),
                ("01_451_0107_1_1", "Weekday Evening (8pm - midnight)", Decimal("83.72"), "Hour"),
                ("01_452_0107_1_1", "Saturday", Decimal("106.93"), "Hour"),
                ("01_453_0107_1_1", "Sunday", Decimal("137.87"), "Hour"),
                ("01_454_0107_1_1", "Public Holiday", Decimal("168.81"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE WITH SELF-CARE ACTIVITIES", "Assistance with self-care activities - Night"],
            "rows": [
                ("01_010_0107_1_1", "Night-Time Sleepover (per night)", Decimal("297.60"), "Night"),
                ("01_002_0107_1_1", "Weekday night - Standard", Decimal("78.81"), "Hour"),
                ("01_405_0104_1_1", "Weekday night - High Intensity", Decimal("85.27"), "Hour"),
                ("01_455_0107_1_1", "Weekday night - Intensive and Complex Behaviour Supports", Decimal("85.27"), "Hour"),
            ],
        },
        {
            "path": ["ASSISTANCE WITH DAILY LIFE"],
            "rows": [
                ("01_004_0107_1_1", "Assistance With Personal Domestic Activities", Decimal("59.06"), "Hour"),
                ("01_016_0104_1_1", "Specialised Home Based Assistance For A Child", Decimal("59.06"), "Hour"),
                ("01_019_0120_1_1", "House And/Or Yard Maintenance", Decimal("56.98"), "Hour"),
                ("01_020_0120_1_1", "House Cleaning And Other Household Activities", Decimal("58.03"), "Hour"),
                ("01_134_0117_8_1", "Capacity Building and Training in Self-Management and Plan Management", Decimal("80.06"), "Hour"),
            ],
        },
        {
            "path": ["SHORT TERM ACCOMMODATION (STA) INC RESPITE", "Ratio 1:1"],
            "rows": [
                ("01_058_0115_1_1", "STA 1:1 - Weekday", Decimal("2178.57"), "Day"),
                ("01_059_0115_1_1", "STA 1:1 - Saturday", Decimal("2785.13"), "Day"),
                ("01_060_0115_1_1", "STA 1:1 - Sunday", Decimal("3527.69"), "Day"),
                ("01_061_0115_1_1", "STA 1:1 - Public Holiday", Decimal("4270.25"), "Day"),
            ],
        },
        {
            "path": ["SHORT TERM ACCOMMODATION (STA) INC RESPITE", "Ratio 1:2"],
            "rows": [
                ("01_054_0115_1_1", "STA 1:2 - Weekday", Decimal("1198.69"), "Day"),
                ("01_055_0115_1_1", "STA 1:2 - Saturday", Decimal("1501.97"), "Day"),
                ("01_056_0115_1_1", "STA 1:2 - Sunday", Decimal("1873.25"), "Day"),
                ("01_057_0115_1_1", "STA 1:2 - Public Holiday", Decimal("2244.53"), "Day"),
            ],
        },
        {
            "path": ["SHORT TERM ACCOMMODATION (STA) INC RESPITE", "Ratio 1:3"],
            "rows": [
                ("01_062_0115_1_1", "STA 1:3 - Weekday", Decimal("872.06"), "Day"),
                ("01_063_0115_1_1", "STA 1:3 - Saturday", Decimal("1074.25"), "Day"),
                ("01_064_0115_1_1", "STA 1:3 - Sunday", Decimal("1321.77"), "Day"),
                ("01_065_0115_1_1", "STA 1:3 - Public Holiday", Decimal("1569.29"), "Day"),
            ],
        },
        {
            "path": ["SHORT TERM ACCOMMODATION (STA) INC RESPITE", "Ratio 1:4"],
            "rows": [
                ("01_045_0115_1_1", "STA 1:4 - Weekday", Decimal("708.75"), "Day"),
                ("01_051_0115_1_1", "STA 1:4 - Saturday", Decimal("860.39"), "Day"),
                ("01_052_0115_1_1", "STA 1:4 - Sunday", Decimal("1046.03"), "Day"),
                ("01_053_0115_1_1", "STA 1:4 - Public Holiday", Decimal("1231.67"), "Day"),
            ],
        },
        {
            "path": ["MEDIUM TERM ACCOMMODATION"],
            "rows": [
                ("01_082_0115_1_1", "Medium Term Accommodation", Decimal("155.68"), "Day"),
            ],
        },
        {
            "path": ["PROVIDER TRAVEL", "Non-Labour Costs (examples only)"],
            "rows": [
                ("01_799_0104_1_1", "Non-Labour Travel Cost code", None, None),
                ("01_799_0126_1_1", "Non-Labour Travel Cost code", None, None),
                ("04_799_0104_6_1", "Non-Labour Travel Cost code", None, None),
                ("07_799_0106_6_3", "Non-Labour Travel Cost code", None, None),
                ("08_799_0106_2_3", "Non-Labour Travel Cost code", None, None),
                ("09_799_0106_6_3", "Non-Labour Travel Cost code", None, None),
                ("10_799_0102_5_3", "Non-Labour Travel Cost code", None, None),
                ("11_799_0110_7_3", "Non-Labour Travel Cost code", None, None),
                ("12_799_0126_3_3", "Non-Labour Travel Cost code", None, None),
                ("13_799_0102_4_3", "Non-Labour Travel Cost code", None, None),
                ("14_799_0127_8_3", "Non-Labour Travel Cost code", None, None),
                ("15_799_0103_6_3", "Non-Labour Travel Cost code", None, None),
            ],
        },
        {
            "path": ["IMPROVED DAILY LIVING SKILLS", "Under 9 years old"],
            "rows": [
                ("01_700_0118_1_3", "Psychologist (Under 9)", Decimal("232.99"), "Hour"),
                ("15_001_0118_1_3", "Psychologist (Under 9)", Decimal("232.99"), "Hour"),
                ("01_720_0118_1_3", "Physiotherapy (Under 9)", Decimal("183.99"), "Hour"),
                ("15_003_0118_1_3", "Physiotherapy (Under 9)", Decimal("183.99"), "Hour"),
                ("01_650_0118_1_3", "Occupational Therapist (Under 9)", Decimal("193.99"), "Hour"),
                ("15_617_0118_1_3", "Occupational Therapist (Under 9)", Decimal("193.99"), "Hour"),
                ("01_653_0118_1_3", "Speech Pathologist (Under 9)", Decimal("193.99"), "Hour"),
                ("15_622_0118_1_3", "Speech Pathologist (Under 9)", Decimal("193.99"), "Hour"),
                ("01_663_0118_1_3", "Podiatrist (Under 9)", Decimal("188.99"), "Hour"),
                ("15_619_0118_1_3", "Podiatrist (Under 9)", Decimal("188.99"), "Hour"),
                ("15_008_0118_1_3", "Therapy Assistant Level 1 (Under 9)", Decimal("56.16"), "Hour"),
                ("15_009_0118_1_3", "Therapy Assistant Level 2 (Under 9)", Decimal("86.79"), "Hour"),
                ("15_610_0118_1_3", "Art Therapist (Under 9)", Decimal("193.99"), "Hour"),
                ("15_611_0118_1_3", "Audiologist (Under 9)", Decimal("193.99"), "Hour"),
                ("15_621_0118_1_3", "Social Worker (Under 9)", Decimal("193.99"), "Hour"),
                ("15_606_0118_1_3", "Counsellor (Under 9)", Decimal("156.16"), "Hour"),
                ("15_613_0118_1_3", "Developmental Educator (Under 9)", Decimal("193.99"), "Hour"),
                ("15_609_0118_1_3", "Exercise Physiologist (Under 9)", Decimal("166.99"), "Hour"),
                ("15_618_0118_1_3", "Orthoptist (Under 9)", Decimal("193.99"), "Hour"),
                ("15_620_0118_1_3", "Rehabilitation Counsellor (Under 9)", Decimal("193.99"), "Hour"),
                ("15_615_0118_1_3", "Music Therapist (Under 9)", Decimal("193.99"), "Hour"),
                ("01_760_0118_1_3", "Dietitian (Under 9)", Decimal("188.99"), "Hour"),
                ("15_062_0118_1_3", "Dietitian (Under 9)", Decimal("188.99"), "Hour"),
                ("15_501_0119_1_3", "Provision of Hearing Services by an Audiologist (Under 9)", Decimal("193.99"), "Hour"),
                ("01_740_0118_1_3", "Other Professional (Under 9)", Decimal("193.99"), "Hour"),
                ("15_005_0118_1_3", "Other Professional (Under 9)", Decimal("193.99"), "Hour"),
            ],
        },
        {
            "path": ["IMPROVED DAILY LIVING SKILLS", "Over 9 years old"],
            "rows": [
                ("01_701_0128_1_3", "Psychologist (Over 9)", Decimal("232.99"), "Hour"),
                ("15_054_0128_1_3", "Psychologist (Over 9)", Decimal("232.99"), "Hour"),
                ("01_721_0128_1_3", "Physiotherapy (Over 9)", Decimal("183.99"), "Hour"),
                ("15_055_0128_1_3", "Physiotherapy (Over 9)", Decimal("183.99"), "Hour"),
                ("01_661_0128_1_3", "Occupational Therapist (Over 9)", Decimal("193.99"), "Hour"),
                ("15_617_0128_1_3", "Occupational Therapist (Over 9)", Decimal("193.99"), "Hour"),
                ("01_665_0128_1_3", "Speech Pathologist (Over 9)", Decimal("193.99"), "Hour"),
                ("15_622_0128_1_3", "Speech Pathologist (Over 9)", Decimal("193.99"), "Hour"),
                ("01_663_0128_1_3", "Podiatrist (Over 9)", Decimal("188.99"), "Hour"),
                ("15_619_0128_1_3", "Podiatrist (Over 9)", Decimal("188.99"), "Hour"),
                ("15_052_0128_1_3", "Therapy Assistant Level 1 (Over 9)", Decimal("56.16"), "Hour"),
                ("15_053_0128_1_3", "Therapy Assistant Level 2 (Over 9)", Decimal("86.79"), "Hour"),
                ("15_610_0128_1_3", "Art Therapist (Over 9)", Decimal("193.99"), "Hour"),
                ("15_611_0128_1_3", "Audiologist (Over 9)", Decimal("193.99"), "Hour"),
                ("15_621_0128_1_3", "Social Worker (Over 9)", Decimal("193.99"), "Hour"),
                ("15_043_0128_1_3", "Counsellor (Over 9)", Decimal("156.16"), "Hour"),
                ("15_613_0128_1_3", "Developmental Educator (Over 9)", Decimal("193.99"), "Hour"),
                ("15_200_0126_1_3", "Exercise Physiologist (Over 9)", Decimal("166.99"), "Hour"),
                ("15_618_0128_1_3", "Orthoptist (Over 9)", Decimal("193.99"), "Hour"),
                ("15_620_0128_1_3", "Rehabilitation Counsellor (Over 9)", Decimal("193.99"), "Hour"),
                ("15_615_0128_1_3", "Music Therapist (Over 9)", Decimal("193.99"), "Hour"),
                ("01_760_0128_3_3", "Dietitian (Over 9)", Decimal("188.99"), "Hour"),
                ("15_062_0128_1_3", "Dietitian (Over 9)", Decimal("188.99"), "Hour"),
                ("15_502_0134_1_3", "Provision of Hearing Services by an Audiologist (Over 9)", Decimal("193.99"), "Hour"),
                ("15_503_0134_1_3", "Provision of Hearing Services by an Audiologist", Decimal("166.83"), "Hour"),
                ("01_741_0128_1_3", "Other Professional (Over 9)", Decimal("193.99"), "Hour"),
                ("15_056_0128_1_3", "Other Professional (Over 9)", Decimal("193.99"), "Hour"),
            ],
        },
    ]


def seed():
    items = build_seed_groups()

    with engine.begin() as conn:
        _ensure_tables(conn)

        inserted_or_updated = 0
        for group in items:
            parent_id = None
            for idx, name in enumerate(group["path"], start=1):
                parent_id = _get_or_create_category(conn, parent_id, name, sort_order=idx)

            spec_note = group.get("spec_note")
            for item_code, title, price, unit in group["rows"]:
                spec_default = spec_note
                if spec_note and "claimable item" not in title:
                    spec_default = spec_note
                elif spec_note and "claimable item" in title:
                    spec_default = spec_note
                _upsert_item(
                    conn=conn,
                    category_id=parent_id,
                    item_code=item_code,
                    item_name=title,
                    price_default=price,
                    unit_default=unit,
                    spec_default=spec_default,
                )
                inserted_or_updated += 1

        print(f"已写入/更新 {inserted_or_updated} 条发票项目字典数据。")


if __name__ == "__main__":
    seed()
