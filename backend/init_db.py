"""初始化数据库"""
from core.database import engine, Base
from shared.models import *  # 导入所有模型以注册表
from shared.models import User, Employee
from core.auth import get_password_hash


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表创建成功！")

    # 创建默认管理员账户（如果不存在）
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("默认管理员账户已创建：用户名=admin, 密码=admin123")

        # 为已有员工设置默认密码（如果没有密码）
        employees_without_password = db.query(Employee).filter(Employee.password_hash.is_(None)).all()
        if employees_without_password:
            print(f"发现 {len(employees_without_password)} 个员工没有密码，为他们设置默认密码...")
            default_password = "123456"  # 默认密码
            for employee in employees_without_password:
                employee.password_hash = get_password_hash(default_password)
                print(f"为员工 {employee.name}({employee.employee_number}) 设置默认密码")
            db.commit()
            print(f"已为 {len(employees_without_password)} 个员工设置默认密码为: {default_password}")

    finally:
        db.close()


def migrate_employees():
    """专门用于迁移已有员工密码的函数"""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        employees_without_password = db.query(Employee).filter(Employee.password_hash.is_(None)).all()
        if not employees_without_password:
            print("所有员工都有密码，无需迁移")
            return

        print(f"发现 {len(employees_without_password)} 个员工需要设置密码")
        default_password = "123456"  # 默认密码

        for employee in employees_without_password:
            employee.password_hash = get_password_hash(default_password)
            print(f"为员工 {employee.name}({employee.employee_number}) 设置默认密码")

        db.commit()
        print(f"迁移完成！已为 {len(employees_without_password)} 个员工设置默认密码: {default_password}")
        print("请通知员工尽快修改密码")

    except Exception as e:
        print(f"迁移过程中出错: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_employees()
    else:
        init_db()
