#!/usr/bin/env python3
"""插入请假和修改审批的测试数据，用于验证 houtai 请假管理和修改审批页面的操作功能

用法（在 aozhou-backend 目录下）：
  python scripts/seed_leave_correction_test_data.py

前提：数据库已初始化（运行过 main.py 或 init_db），且已安装 requirements.txt 依赖。
"""
import sys
import json
from pathlib import Path
from datetime import date, datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.database import SessionLocal
from core.auth import get_password_hash
from shared.models import (
    Employee,
    Customer,
    Task,
    TaskStatus,
    LeaveRequest,
    CorrectionRequest,
)


def seed_test_data():
    """插入测试数据"""
    db = SessionLocal()
    try:
        # 1. 获取或创建员工
        employee = db.query(Employee).first()
        if not employee:
            employee = Employee(
                name="测试员工",
                employee_number="EMP001",
                password_hash=get_password_hash("123456"),
                phone="0400000000",
                email="test@example.com",
            )
            db.add(employee)
            db.flush()
            print("已创建测试员工")

        # 2. 获取或创建客户和任务（用于修改审批）
        customer = db.query(Customer).first()
        if not customer:
            customer = Customer(
                name="测试客户",
                phone="0411111111",
                address="测试地址",
            )
            db.add(customer)
            db.flush()
            print("已创建测试客户")

        task = db.query(Task).filter(Task.assigned_employee_id == employee.id).first()
        if not task:
            task = Task(
                title="测试任务",
                customer_id=customer.id,
                service_time=datetime.utcnow(),
                status=TaskStatus.completed,
                assigned_employee_id=employee.id,
                questionnaire_data={"q1": "原答案", "q2": "原答案2"},
            )
            db.add(task)
            db.flush()
            print("已创建测试任务")

        # 3. 插入待审批的请假请求
        existing_leave = (
            db.query(LeaveRequest)
            .filter(
                LeaveRequest.employee_id == employee.id,
                LeaveRequest.status == "pending",
            )
            .first()
        )
        if not existing_leave:
            leave = LeaveRequest(
                employee_id=employee.id,
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=3),
                reason="测试请假 - 个人事务",
                status="pending",
            )
            db.add(leave)
            db.flush()
            print(f"已创建请假请求 (id={leave.id})")

        # 4. 插入待审批的修改请求
        existing_correction = (
            db.query(CorrectionRequest)
            .filter(
                CorrectionRequest.task_id == task.id,
                CorrectionRequest.status == "pending",
            )
            .first()
        )
        if not existing_correction:
            original = {"q1": "原答案", "q2": "原答案2"}
            corrected = {"q1": "修正后答案", "q2": "修正后答案2"}
            correction = CorrectionRequest(
                task_id=task.id,
                requested_by=employee.id,
                original_data=json.dumps(original, ensure_ascii=False),
                corrected_data=json.dumps(corrected, ensure_ascii=False),
                reason="测试修改申请 - 填写有误需更正",
                status="pending",
            )
            db.add(correction)
            db.flush()
            print(f"已创建修改审批请求 (id={correction.id})")

        db.commit()
        print("\n测试数据插入完成。请刷新 houtai 的请假管理和修改审批页面进行验证。")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_test_data()
