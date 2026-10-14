import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.payroll import Payroll
from app.models.user import User
from app.routers.auth import require_roles

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def csv_response(filename: str, headers: list[str], rows: list[list]):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )


@router.get("/attendance.csv")
def attendance_report(
    start_date: date | None = None,
    end_date: date | None = None,
    department: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    query = (
        db.query(Attendance, Employee, User)
        .join(Employee, Attendance.employee_id == Employee.id)
        .join(User, Employee.user_id == User.id)
    )

    if start_date and end_date and end_date < start_date:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=422,
            detail="end_date cannot be before start_date",
        )

    if start_date:
        query = query.filter(Attendance.attendance_date >= start_date)
    if end_date:
        query = query.filter(Attendance.attendance_date <= end_date)
    if department:
        query = query.filter(Employee.department == department)

    records = query.order_by(
        Attendance.attendance_date,
        Employee.id,
    ).all()

    rows = [
        [
            attendance.id,
            employee.id,
            user.full_name,
            user.email,
            employee.department,
            attendance.attendance_date,
            attendance.check_in,
            attendance.check_out,
            attendance.status,
        ]
        for attendance, employee, user in records
    ]

    return csv_response(
        "attendance_report.csv",
        [
            "attendance_id", "employee_id", "employee_name", "email",
            "department", "date", "check_in", "check_out", "status",
        ],
        rows,
    )


@router.get("/payroll.csv")
def payroll_report(
    pay_period: date | None = None,
    department: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    query = (
        db.query(Payroll, Employee, User)
        .join(Employee, Payroll.employee_id == Employee.id)
        .join(User, Employee.user_id == User.id)
    )

    if pay_period:
        query = query.filter(Payroll.pay_period == pay_period)
    if department:
        query = query.filter(Employee.department == department)

    records = query.order_by(
        Payroll.pay_period.desc(),
        Employee.id,
    ).all()

    rows = [
        [
            payroll.id,
            employee.id,
            user.full_name,
            employee.department,
            payroll.pay_period,
            payroll.basic_salary,
            payroll.allowances,
            payroll.deductions,
            payroll.net_salary,
            payroll.is_locked,
        ]
        for payroll, employee, user in records
    ]

    return csv_response(
        "payroll_report.csv",
        [
            "payroll_id", "employee_id", "employee_name", "department",
            "pay_period", "basic_salary", "allowances", "deductions",
            "net_salary", "is_locked",
        ],
        rows,
    )
