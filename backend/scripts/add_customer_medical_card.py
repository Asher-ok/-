#!/usr/bin/env python3
"""迁移脚本：为 customers 表添加医疗卡相关列"""
import sys
from pathlib import Path

# 添加项目根目录到 path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from core.database import engine


def migrate():
    """执行迁移：添加 has_medical_card、medical_card_number 列"""
    conn = engine.connect()
    trans = conn.begin()
    try:
        conn.execute(text("ALTER TABLE customers ADD COLUMN has_medical_card BOOLEAN"))
        conn.execute(text("ALTER TABLE customers ADD COLUMN medical_card_number VARCHAR"))
        trans.commit()
        print("迁移成功：已添加 customers.has_medical_card、medical_card_number 列")
    except Exception as e:
        trans.rollback()
        if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
            print("列已存在，跳过迁移")
        else:
            raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
