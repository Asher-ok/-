import uuid
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

import sys
from pathlib import Path
# 使脚本可独立运行：将项目根目录加入模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import SessionLocal
from shared.models import InvoiceItemCategory, InvoiceItemDict
from modules.houtai.services.invoice_service import normalize_item_code


def _get_or_create_category(
    db: Session,
    name: str,
    parent: Optional[InvoiceItemCategory] = None,
    code: Optional[str] = None,
    sort_order: int = 0,
) -> InvoiceItemCategory:
    existing = (
        db.query(InvoiceItemCategory)
        .filter(InvoiceItemCategory.parent_id == (parent.id if parent else None))
        .filter(InvoiceItemCategory.name == name)
        .first()
    )
    if existing:
        # 更新可变字段
        existing.code = code
        existing.sort_order = sort_order
        db.add(existing)
        return existing

    level = (parent.level + 1) if parent else 1
    path = f"{parent.path}/{name}" if parent else f"/{name}"
    cat = InvoiceItemCategory(
        id=str(uuid.uuid4()),
        parent_id=parent.id if parent else None,
        name=name,
        code=code,
        level=level,
        path=path,
        sort_order=sort_order,
        is_active=True,
    )
    db.add(cat)
    return cat


def _upsert_item(
    db: Session,
    category: InvoiceItemCategory,
    item_name: str,
    item_code: str,
    price: Optional[Decimal],
    unit: Optional[str] = None,
    tax_rate: Decimal = Decimal("0"),
    reference_code: Optional[str] = None,
) -> InvoiceItemDict:
    code_full = normalize_item_code(item_code, reference_code)
    if not code_full:
        raise ValueError(f"无法解析项目编码: {item_code}")

    existing = db.query(InvoiceItemDict).filter(InvoiceItemDict.item_code == code_full).first()
    if existing:
        existing.item_name = item_name
        existing.category_id = category.id
        existing.price_default = price
        if unit:
            existing.unit_default = unit
        if tax_rate is not None:
            existing.tax_rate_default = tax_rate
        existing.is_active = True
        db.add(existing)
        return existing

    it = InvoiceItemDict(
        id=str(uuid.uuid4()),
        category_id=category.id,
        item_code=code_full,
        item_name=item_name,
        unit_default=unit,
        price_default=price,
        tax_rate_default=tax_rate if tax_rate is not None else Decimal("0"),
        is_active=True,
    )
    db.add(it)
    return it


def _dec(x: str) -> Decimal:
    return Decimal(x)


def seed(db: Session):
    # 一级分类
    cat_self_care = _get_or_create_category(db, "ASSISTANCE WITH SELF-CARE ACTIVITIES", sort_order=10)
    cat_daily_life = _get_or_create_category(db, "ASSISTANCE WITH DAILY LIFE", sort_order=20)
    cat_sta = _get_or_create_category(db, "SHORT TERM ACCOMMODATION (STA) INC RESPITE", sort_order=30)
    cat_mta = _get_or_create_category(db, "MEDIUM TERM ACCOMMODATION", sort_order=40)
    cat_access_comm = _get_or_create_category(db, "ASSISTANCE TO ACCESS COMMUNITY, SOCIAL & RECREATIONAL ACTIVITIES", sort_order=50)
    cat_transport = _get_or_create_category(db, "ACTIVITY BASED TRANSPORT", sort_order=60)
    cat_capital = _get_or_create_category(db, "CENTRE CAPITAL COSTS", sort_order=70)
    cat_provider_travel = _get_or_create_category(db, "PROVIDER TRAVEL", sort_order=80)
    cat_employment_supports = _get_or_create_category(db, "EMPLOYMENT SUPPORTS", sort_order=90)
    cat_establishment_fee = _get_or_create_category(db, "ESTABLISHMENT FEE FOR PERSONAL CARE/PARTICIPATION", sort_order=100)
    cat_nurse_supports = _get_or_create_category(db, "DISABILITY RELATED HEALTH SUPPORTS BY A NURSE", sort_order=110)
    cat_support_coordination = _get_or_create_category(db, "SUPPORT COORDINATION", sort_order=120)
    cat_psychosocial = _get_or_create_category(db, "PSYCHOSOCIAL RECOVERY COACHING", sort_order=130)
    cat_improved_living = _get_or_create_category(db, "IMPROVED LIVING ARRANGEMENTS", sort_order=140)
    cat_increased_social = _get_or_create_category(db, "INCREASED SOCIAL AND COMMUNITY PARTICIPATION", sort_order=150)
    cat_job = _get_or_create_category(db, "FINDING AND KEEPING A JOB", sort_order=160)
    cat_health = _get_or_create_category(db, "IMPROVED HEALTH AND WELLBEING", sort_order=170)
    cat_learning = _get_or_create_category(db, "IMPROVED LEARNING", sort_order=180)
    cat_life_choices = _get_or_create_category(db, "IMPROVED LIFE CHOICES", sort_order=190)
    cat_relationships = _get_or_create_category(db, "IMPROVED RELATIONSHIPS", sort_order=200)
    cat_daily_living_skills = _get_or_create_category(db, "IMPROVED DAILY LIVING SKILLS", sort_order=210)

    # 二级分类（自理相关）
    sc_standard = _get_or_create_category(db, "Assistance with self-care activities - Standard needs", parent=cat_self_care, sort_order=1)
    sc_high = _get_or_create_category(db, "Assistance with self-care activities - High Intensity", parent=cat_self_care, sort_order=2)
    sc_complex = _get_or_create_category(db, "Intensive and Complex Behaviour Supports", parent=cat_self_care, sort_order=3)
    sc_night = _get_or_create_category(db, "Assistance with self-care activities - Night", parent=cat_self_care, sort_order=4)

    # 自理-标准
    _upsert_item(db, sc_standard, "Weekday Daytime (6am to 8pm)", "01_011_0107_1_1", _dec("70.23"), "hour")
    _upsert_item(db, sc_standard, "Weekday Evening (8pm - midnight)", "01_015_0107_1_1", _dec("77.38"), "hour")
    _upsert_item(db, sc_standard, "Saturday", "01_013_0107_1_1", _dec("98.83"), "hour")
    _upsert_item(db, sc_standard, "Sunday", "01_014_0107_1_1", _dec("127.43"), "hour")
    _upsert_item(db, sc_standard, "Public Holiday", "01_012_0107_1_1", _dec("156.03"), "hour")

    # 自理-高强度
    _upsert_item(db, sc_high, "Weekday Daytime (6am to 8pm)", "01_400_0104_1_1", _dec("75.98"), "hour")
    _upsert_item(db, sc_high, "Weekday Evening (8pm - midnight)", "01_401_0104_1_1", _dec("83.72"), "hour")
    _upsert_item(db, sc_high, "Saturday", "01_402_0104_1_1", _dec("106.93"), "hour")
    _upsert_item(db, sc_high, "Sunday", "01_403_0104_1_1", _dec("137.87"), "hour")
    _upsert_item(db, sc_high, "Public Holiday", "01_404_0104_1_1", _dec("168.81"), "hour")

    # 自理-复杂行为
    _upsert_item(db, sc_complex, "Weekday Daytime (6am to 8pm)", "01_450_0107_1_1", _dec("75.98"), "hour")
    _upsert_item(db, sc_complex, "Weekday Evening (8pm - midnight)", "01_451_0107_1_1", _dec("83.72"), "hour")
    _upsert_item(db, sc_complex, "Saturday", "01_452_0107_1_1", _dec("106.93"), "hour")
    _upsert_item(db, sc_complex, "Sunday", "01_453_0107_1_1", _dec("137.87"), "hour")
    _upsert_item(db, sc_complex, "Public Holiday", "01_454_0107_1_1", _dec("168.81"), "hour")

    # 自理-夜间
    _upsert_item(db, sc_night, "Night-Time Sleepover (per night)", "01_010_0107_1_1", _dec("297.60"), "night")
    _upsert_item(db, sc_night, "Weekday night - Standard", "01_002_0107_1_1", _dec("78.81"), "hour")
    _upsert_item(db, sc_night, "Weekday night - High Intensity", "01_405_0104_1_1", _dec("85.27"), "hour")
    _upsert_item(db, sc_night, "Weekday night - Intensive and Complex Behaviour Supports", "01_455_0107_1_1", _dec("85.27"), "hour")

    # 每日生活（无二级分类）
    _upsert_item(db, cat_daily_life, "Assistance With Personal Domestic Activities", "01_004_0107_1_1", _dec("59.06"), "hour")
    _upsert_item(db, cat_daily_life, "Specialised Home Based Assistance For A Child", "01_016_0104_1_1", _dec("59.06"), "hour")
    _upsert_item(db, cat_daily_life, "House And/Or Yard Maintenance", "01_019_0120_1_1", _dec("56.98"), "hour")
    _upsert_item(db, cat_daily_life, "House Cleaning And Other Household Activities", "01_020_0120_1_1", _dec("58.03"), "hour")
    _upsert_item(db, cat_daily_life, "Capacity Building and Training in Self-Management and Plan Management", "01_134_0117_8_1", _dec("80.06"), "hour")

    # STA
    sta_1_1 = _get_or_create_category(db, "Ratio 1:1", parent=cat_sta, sort_order=1)
    sta_1_2 = _get_or_create_category(db, "Ratio 1:2", parent=cat_sta, sort_order=2)
    sta_1_3 = _get_or_create_category(db, "Ratio 1:3", parent=cat_sta, sort_order=3)
    sta_1_4 = _get_or_create_category(db, "Ratio 1:4", parent=cat_sta, sort_order=4)
    # Ratio 1:1
    ref = _upsert_item(db, sta_1_1, "Weekday", "01_058_0115_1_1", _dec("2178.57"), "day").item_code
    _upsert_item(db, sta_1_1, "Saturday", "01_059...", _dec("2785.13"), "day", reference_code=ref)
    _upsert_item(db, sta_1_1, "Sunday", "01_060...", _dec("3527.69"), "day", reference_code=ref)
    _upsert_item(db, sta_1_1, "Public Holiday", "01_061...", _dec("4270.25"), "day", reference_code=ref)
    # Ratio 1:2
    ref = _upsert_item(db, sta_1_2, "Weekday", "01_054_0115_1_1", _dec("1198.69"), "day").item_code
    _upsert_item(db, sta_1_2, "Saturday", "01_055...", _dec("1501.97"), "day", reference_code=ref)
    _upsert_item(db, sta_1_2, "Sunday", "01_056...", _dec("1873.25"), "day", reference_code=ref)
    _upsert_item(db, sta_1_2, "Public Holiday", "01_057...", _dec("2244.53"), "day", reference_code=ref)
    # Ratio 1:3
    ref = _upsert_item(db, sta_1_3, "Weekday", "01_062_0115_1_1", _dec("872.06"), "day").item_code
    _upsert_item(db, sta_1_3, "Saturday", "01_063...", _dec("1074.25"), "day", reference_code=ref)
    _upsert_item(db, sta_1_3, "Sunday", "01_064...", _dec("1321.77"), "day", reference_code=ref)
    _upsert_item(db, sta_1_3, "Public Holiday", "01_065...", _dec("1569.29"), "day", reference_code=ref)
    # Ratio 1:4
    ref = _upsert_item(db, sta_1_4, "Weekday", "01_045_0115_1_1", _dec("708.75"), "day").item_code
    _upsert_item(db, sta_1_4, "Saturday", "01_051...", _dec("860.39"), "day", reference_code=ref)
    _upsert_item(db, sta_1_4, "Sunday", "01_052...", _dec("1046.03"), "day", reference_code=ref)
    _upsert_item(db, sta_1_4, "Public Holiday", "01_053...", _dec("1231.67"), "day", reference_code=ref)

    # MTA
    _upsert_item(db, cat_mta, "Medium Term Accommodation", "01_082_0115_1_1", _dec("155.68"), "day")

    # 社交与娱乐
    acc_standard = _get_or_create_category(db, "Assistance to access community-based social & recreational activities - Standard", parent=cat_access_comm, sort_order=1)
    acc_high = _get_or_create_category(db, "Assistance to access community-based social & recreational activities - High Intensity", parent=cat_access_comm, sort_order=2)
    acc_complex = _get_or_create_category(db, "Intensive and Complex Behaviour Supports", parent=cat_access_comm, sort_order=3)
    # Standard
    _upsert_item(db, acc_standard, "Weekday Daytime (6am to 8pm)", "04_104_0125_6_1", _dec("70.23"), "hour")
    _upsert_item(db, acc_standard, "Weekday Evening (8pm - midnight)", "04_103_0125_6_1", _dec("77.38"), "hour")
    _upsert_item(db, acc_standard, "Saturday", "04_105_0125_6_1", _dec("98.83"), "hour")
    _upsert_item(db, acc_standard, "Sunday", "04_106_0125_6_1", _dec("127.43"), "hour")
    _upsert_item(db, acc_standard, "Public Holiday", "04_102_0125_6_1", _dec("156.03"), "hour")
    # High intensity
    _upsert_item(db, acc_high, "Weekday Daytime (6am to 8pm)", "04_400_0104_1_1", _dec("75.98"), "hour")
    _upsert_item(db, acc_high, "Weekday Evening (8pm - midnight)", "04_401_0104_1_1", _dec("83.72"), "hour")
    _upsert_item(db, acc_high, "Saturday", "04_402_0104_1_1", _dec("106.93"), "hour")
    _upsert_item(db, acc_high, "Sunday", "04_403_0104_1_1", _dec("137.87"), "hour")
    _upsert_item(db, acc_high, "Public Holiday", "04_404_0104_1_1", _dec("168.81"), "hour")
    # Complex
    _upsert_item(db, acc_complex, "Weekday Daytime (6am to 8pm)", "04_450_0125_1_1", _dec("75.98"), "hour")
    _upsert_item(db, acc_complex, "Weekday Evening (8pm - midnight)", "04_451_0125_1_1", _dec("83.72"), "hour")
    _upsert_item(db, acc_complex, "Saturday", "04_452_0125_1_1", _dec("106.93"), "hour")
    _upsert_item(db, acc_complex, "Sunday", "04_453_0125_1_1", _dec("137.87"), "hour")
    _upsert_item(db, acc_complex, "Public Holiday", "04_454_0125_1_1", _dec("168.81"), "hour")

    # 交通（每公里价格 & 可用编码）
    _upsert_item(db, cat_transport, "Activity Based Transport - Not Modified Vehicle (per km)", "transport_not_modified", _dec("0.99"), "km")
    _upsert_item(db, cat_transport, "Activity Based Transport - Modified Vehicle (per km)", "transport_modified", _dec("2.76"), "km")
    for code in [
        "04_590_0125_6_1",
        "04_591_0136_6_1",
        "04_592_0104_6_1",
        "04_821_0133_6_1",
        "07_501_0106_6_3",
        "08_590_0106_2_3",
        "09_590_0106_6_3",
        "09_591_0117_6_3",
        "10_590_0133_5_3",
        "10_590_0102_5_3",
        "11_590_0117_7_3",
        "13_590_0102_4_3",
    ]:
        _upsert_item(db, cat_transport, f"Transport claimable code {code}", code, None, None)

    # 场地资本成本
    _upsert_item(db, cat_capital, "Centre Capital Cost", "04_599_0104_6_1", _dec("2.59"), "unit")
    _upsert_item(db, cat_capital, "Centre Capital Cost", "10_599_0133_5_3", _dec("2.59"), "unit")

    # 提供者差旅 非劳务（示例编码）
    for code in [
        "01_799_0104_1_1",
        "01_799_0126_1_1",
        "04_799_0104_6_1",
        "07_799_0106_6_3",
        "08_799_0106_2_3",
        "09_799_0106_6_3",
        "10_799_0102_5_3",
        "11_799_0110_7_3",
        "12_799_0126_3_3",
        "13_799_0102_4_3",
        "14_799_0127_8_3",
        "15_799_0103_6_3",
    ]:
        _upsert_item(db, cat_provider_travel, f"Non-Labour Travel cost code {code}", code, None, None)

    # 就业支持（常规价格）
    emp_codes = [
        ("Weekday Daytime", "04_801_0133_5_1", _dec("70.23")),
        ("Evening", "04_802_0133_5_1", _dec("77.38")),
        ("Saturday", "04_803_0133_5_1", _dec("98.83")),
        ("Sunday", "04_804_0133_5_1", _dec("127.43")),
        ("Public Holiday", "04_805_0133_5_1", _dec("156.03")),
    ]
    for n, c, p in emp_codes:
        _upsert_item(db, cat_employment_supports, f"Employment Supports - {n}", c, p, "hour")

    # 建立费
    _upsert_item(db, cat_establishment_fee, "Establishment Fee for Personal Care/Participation", "01_049_0104_1_1", _dec("702.30"), "each")
    _upsert_item(db, cat_establishment_fee, "Establishment Fee for Personal Care/Participation", "04_049_0104_1_1", _dec("702.30"), "each")

    # 护士相关支持（Capacity Building Daily Activity）
    nurse_cb = _get_or_create_category(db, "CB Daily Activity (Nurse)", parent=cat_nurse_supports, sort_order=1)
    for base, price in [
        ("15_400_0114_1_3", "99.88"),   # Enrolled Nurse Daytime
        ("15_401_0114_1_3", "110.18"),  # Evening
        ("15_405_0114_1_3", "112.22"),  # Night
        ("15_402_0114_1_3", "142.48"),  # Saturday
        ("15_403_0114_1_3", "163.79"),  # Sunday
        ("15_404_0114_1_3", "185.08"),  # Public Holiday
        ("15_406_0114_1_3", "123.65"),  # Registered Nurse Daytime
        ("15_407_0114_1_3", "136.41"),  # Evening
        ("15_411_0114_1_3", "138.95"),  # Night
        ("15_408_0114_1_3", "176.47"),  # Saturday
        ("15_409_0114_1_3", "202.87"),  # Sunday
        ("15_410_0114_1_3", "229.27"),  # Public Holiday
        ("15_412_0114_1_3", "143.04"),  # Clinical Nurse Daytime
        ("15_413_0114_1_3", "157.77"),  # Evening
        ("15_417_0114_1_3", "160.73"),  # Night
        ("15_414_0114_1_3", "204.12"),  # Saturday
        ("15_415_0114_1_3", "234.67"),  # Sunday
        ("15_416_0114_1_3", "265.20"),  # Public Holiday
        ("15_418_0114_1_3", "169.16"),  # Clinical Nurse Consultant Daytime
        ("15_419_0114_1_3", "186.63"),  # Evening
        ("15_423_0114_1_3", "190.12"),  # Night
        ("15_420_0114_1_3", "241.52"),  # Saturday
        ("15_421_0114_1_3", "277.69"),  # Sunday
        ("15_422_0114_1_3", "313.86"),  # Public Holiday
        ("15_424_0114_1_3", "176.85"),  # Nurse Practitioner Daytime
        ("15_425_0114_1_3", "195.09"),  # Evening
        ("15_429_0114_1_3", "198.75"),  # Night
        ("15_426_0114_1_3", "252.51"),  # Saturday
        ("15_427_0114_1_3", "293.20"),  # Sunday
        ("15_428_0114_1_3", "328.16"),  # Public Holiday
    ]:
        _upsert_item(db, nurse_cb, f"Nurse support {base}", base, _dec(price), "hour")

    # 护士相关支持（Daily Activities）
    nurse_da = _get_or_create_category(db, "Daily Activities (Nurse)", parent=cat_nurse_supports, sort_order=2)
    for base, price in [
        ("01_600_0114_1_1", "99.88"),
        ("01_601_0114_1_1", "110.18"),
        ("01_605_0114_1_1", "112.22"),
        ("01_602_0114_1_1", "142.48"),
        ("01_603_0114_1_1", "163.79"),
        ("01_604_0114_1_1", "185.08"),
        ("01_606_0114_1_1", "123.65"),
        ("01_607_0114_1_1", "136.41"),
        ("01_611_0114_1_1", "138.95"),
        ("01_608_0114_1_1", "176.47"),
        ("01_609_0114_1_1", "202.87"),
        ("01_610_0114_1_1", "229.27"),
        ("01_612_0114_1_1", "143.04"),
        ("01_613_0114_1_1", "157.77"),
        ("01_617_0114_1_1", "160.73"),
        ("01_614_0114_1_1", "204.12"),
        ("01_615_0114_1_1", "234.67"),
        ("01_616_0114_1_1", "265.20"),
        ("01_618_0114_1_1", "169.16"),
        ("01_619_0114_1_1", "186.63"),
        ("01_623_0114_1_1", "190.12"),
        ("01_620_0114_1_1", "241.52"),
        ("01_621_0114_1_1", "277.69"),
        ("01_622_0114_1_1", "313.86"),
        ("01_624_0114_1_1", "176.85"),
        ("01_625_0114_1_1", "195.09"),
        ("01_629_0114_1_1", "198.75"),
        ("01_626_0114_1_1", "252.51"),
        ("01_627_0114_1_1", "293.20"),
        ("01_628_0114_1_1", "328.16"),
    ]:
        _upsert_item(db, nurse_da, f"Nurse support {base}", base, _dec(price), "hour")

    # 支持协调
    _upsert_item(db, cat_support_coordination, "Level 1: Support Connection", "07_001_0106_8_3", _dec("80.06"), "hour")
    _upsert_item(db, cat_support_coordination, "Level 2: Coordination of Supports", "07_002_0106_8_3", _dec("100.14"), "hour")
    _upsert_item(db, cat_support_coordination, "Level 3: Specialist Support Coordination", "07_004_0132_8_3", _dec("190.54"), "hour")

    # 心理社会康复教练
    _upsert_item(db, cat_psychosocial, "Weekday Daytime", "07_101_0106_6_3", _dec("105.43"), "hour")
    _upsert_item(db, cat_psychosocial, "Evening", "07_102...", _dec("116.16"), "hour", reference_code="07_101_0106_6_3")
    _upsert_item(db, cat_psychosocial, "Night", "07_103...", _dec("118.31"), "hour", reference_code="07_101_0106_6_3")
    _upsert_item(db, cat_psychosocial, "Saturday", "07_104...", _dec("148.36"), "hour", reference_code="07_101_0106_6_3")
    _upsert_item(db, cat_psychosocial, "Sunday", "07_105...", _dec("191.29"), "hour", reference_code="07_101_0106_6_3")
    _upsert_item(db, cat_psychosocial, "Public Holiday", "07_106...", _dec("234.23"), "hour", reference_code="07_101_0106_6_3")

    # 改善居住安排
    _upsert_item(db, cat_improved_living, "Assistance With Accommodation and Tenancy Obligations", "08_005_0106_2_3", _dec("80.06"), "hour")

    # 增强社会与社区参与
    _upsert_item(db, cat_increased_social, "Life Transition Planning", "09_006_0106_6_3", _dec("80.06"), "hour")
    _upsert_item(db, cat_increased_social, "Skills Development and Training", "09_009_0117_6_3", _dec("80.06"), "hour")

    # 找到并保持工作
    _upsert_item(db, cat_job, "Employment Related Assessment, Counselling and Advice", "10_011_0128_5_3", _dec("193.99"), "hour")
    _upsert_item(db, cat_job, "Employment Assistance", "10_016_0102_5_3", _dec("80.06"), "hour")
    _upsert_item(db, cat_job, "Level 2: Coordination of Supports", "10_002_0106_8_3", _dec("100.14"), "hour")
    _upsert_item(db, cat_job, "Psychosocial Recovery Coaching – Weekday Daytime", "10_101_0106_6_3", _dec("105.43"), "hour")
    _upsert_item(db, cat_job, "Supports in Employment - Weekday Daytime", "10_806_0133_5_1", _dec("70.23"), "hour")

    # 改善健康与福祉
    _upsert_item(db, cat_health, "Dietitian on managing diet for health and well-being", "12_025_0128_3_3", _dec("188.99"), "hour")
    _upsert_item(db, cat_health, "Exercise Physiologist", "12_027_0126_3_3", _dec("166.99"), "hour")
    _upsert_item(db, cat_health, "Personal Trainer", "12_029_0126_3_3", _dec("67.00"), "hour")

    # 改善学习
    _upsert_item(db, cat_learning, "Transition Through School and To Further Education", "13_030_0102_4_3", _dec("80.06"), "hour")

    # 改善生活选择
    _upsert_item(db, cat_life_choices, "Plan Management - Monthly Fee (per month)", "14_034_0127_8_3", _dec("104.45"), "month")

    # 改善人际关系
    _upsert_item(db, cat_relationships, "Specialist Behavioural Intervention Support", "11_022_0110_7_3", _dec("232.99"), "hour")
    _upsert_item(db, cat_relationships, "Behaviour Management Plan Including Training In Behaviour Management", "11_023_0110_7_3", _dec("232.99"), "hour")
    _upsert_item(db, cat_relationships, "Individual Social Skills Development", "11_024_0117_7_3", _dec("80.06"), "hour")

    # 改善日常生活技能（按年龄）
    daily_under9 = _get_or_create_category(db, "Under 9 years old", parent=cat_daily_living_skills, sort_order=1)
    daily_over9 = _get_or_create_category(db, "Over 9 years old", parent=cat_daily_living_skills, sort_order=2)
    # 主要职业
    pairs = [
        ("Psychologist", ("01_700_0118_1_3", "15_001_0118_1_3"), ("01_701_0128_1_3", "15_054_0128_1_3"), "232.99"),
        ("Physiotherapy", ("01_720_0118_1_3", "15_003_0118_1_3"), ("01_721_0128_1_3", "15_055_0128_1_3"), "183.99"),
        ("Occupational Therapist", ("01_650_0118_1_3", "15_617_0118_1_3"), ("01_661_0128_1_3", "15_617_0128_1_3"), "193.99"),
        ("Speech Pathologist", ("01_653_0118_1_3", "15_622_0118_1_3"), ("01_665_0128_1_3", "15_622_0128_1_3"), "193.99"),
        ("Podiatrist", ("01_663_0118_1_3", "15_619_0118_1_3"), ("01_663_0128_1_3", "15_619_0128_1_3"), "188.99"),
        ("Therapy Assistant Level 1", ("15_008_0118_1_3",), ("15_052_0128_1_3",), "56.16"),
        ("Therapy Assistant Level 2", ("15_009_0118_1_3",), ("15_053_0128_1_3",), "86.79"),
        ("Art Therapist", ("15_610_0118_1_3",), ("15_610_0128_1_3",), "193.99"),
        ("Audiologist", ("15_611_0118_1_3",), ("15_611_0128_1_3",), "193.99"),
        ("Social Worker", ("15_621_0118_1_3",), ("15_621_0128_1_3",), "193.99"),
        ("Counsellor", ("15_606_0118_1_3",), ("15_043_0128_1_3",), "156.16"),
        ("Developmental Educator", ("15_613_0118_1_3",), ("15_613_0128_1_3",), "193.99"),
        ("Exercise Physiologist", ("15_609_0118_1_3",), ("15_200_0126_1_3",), "166.99"),
        ("Orthoptist", ("15_618_0118_1_3",), ("15_618_0128_1_3",), "193.99"),
        ("Rehabilitation Counsellor", ("15_620_0118_1_3",), ("15_620_0128_1_3",), "193.99"),
        ("Music Therapist", ("15_615_0118_1_3",), ("15_615_0128_1_3",), "193.99"),
        ("Dietitian", ("01_760_0118_1_3", "15_062_0118_1_3"), ("01_760_0128_3_3", "15_062_0128_1_3"), "188.99"),
        ("Provision of Hearing Services by an Audiologist", ("15_501_0119_1_3",), ("15_502_0134_1_3",), "193.99"),
        ("Other Professional", ("01_740_0118_1_3", "15_005_0118_1_3"), ("01_741_0128_1_3", "15_056_0128_1_3"), "193.99"),
    ]
    for name, under_codes, over_codes, price in pairs:
        for c in under_codes:
            _upsert_item(db, daily_under9, f"{name} (Under 9)", c, _dec(price), "hour")
        for c in over_codes:
            _upsert_item(db, daily_over9, f"{name} (Over 9)", c, _dec(price), "hour")
    # 其它单项
    _upsert_item(db, cat_daily_living_skills, "Assistance With Decision Making, Daily Planning and Budgeting", "15_035_0106_1_3", _dec("70.23"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Individual Skill Development and Training Including Public Transport Training", "15_037_0117_1_3", _dec("70.23"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Training For Carers/Parents", "15_038_0117_1_3", _dec("80.06"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Community Engagement Assistance", "15_045_0128_1_3", _dec("51.20"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Selection/Manufacture of Customised Wearable Technology (Customised Prosthetics)", "15_047_0135_1_3", _dec("193.99"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Provision of Hearing Services by an Audiologist", "15_503_0134_1_3", _dec("166.83"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Assistive Technology Mentoring", "15_300_0103_1_3", _dec("105.43"), "hour")
    _upsert_item(db, cat_daily_living_skills, "Early Childhood Teacher or Educator", "15_625_0118_1_3", _dec("193.99"), "hour")

    # 提交
    db.commit()


def main():
    db = SessionLocal()
    try:
        seed(db)
        print("Invoice item categories and items seeded successfully.")
    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
