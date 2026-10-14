from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.routers.auth import get_current_user, require_roles
from app.schemas.attendance import AttendanceCreate, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/check-in", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "employee":
        employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee record not found")
        if data.employee_id is not None and data.employee_id != employee.id:
            raise HTTPException(status_code=403, detail="You can only check in for yourself")
    else:
        if data.employee_id is None:
            raise HTTPException(status_code=422, detail="employee_id is required")
        employee = db.query(Employee).filter(
            Employee.id == data.employee_id
        ).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

    if not employee_is_active(db, employee):
        raise HTTPException(status_code=400, detail="Employee is inactive")

    today = date.today()
    if data.attendance_date != today:
        raise HTTPException(status_code=400, detail="Check-in is only allowed for today")

    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee.id,
        Attendance.attendance_date == today,
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="Attendance already exists for today")

    record = Attendance(
        employee_id=employee.id,
        attendance_date=today,
        check_in=datetime.now(),
        status="present",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.patch("/{attendance_id}/check-out", response_model=AttendanceResponse)
def check_out(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    record = db.query(Attendance).filter(
        Attendance.id == attendance_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    employee = db.query(Employee).filter(
        Employee.id == record.employee_id
    ).first()

    if current_user.role == "employee" and employee.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only check out for yourself")

    if record.check_out is not None:
        raise HTTPException(status_code=409, detail="Already checked out")

    record.check_out = datetime.now()
    db.commit()
    db.refresh(record)
    return record


@router.get("/", response_model=list[AttendanceResponse])
def list_attendance(
    employee_id: int | None = None,
    attendance_date: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Attendance)

    if current_user.role == "employee":
        employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()
        if not employee:
            return []
        query = query.filter(Attendance.employee_id == employee.id)
    else:
        query = query.join(Employee, Attendance.employee_id == Employee.id)

    if employee_id is not None:
        query = query.filter(Attendance.employee_id == employee_id)

    if attendance_date is not None:
        query = query.filter(Attendance.attendance_date == attendance_date)

    return query.order_by(Attendance.attendance_date.desc()).all()


def employee_is_active(db: Session, employee: Employee) -> bool:
    from app.models.user import User

    user = db.query(User).filter(User.id == employee.user_id).first()
    return user is not None and user.is_active


from calendar import monthrange
from datetime import time
from sqlalchemy import extract


@router.get("/monthly-summary")
def monthly_attendance_summary(
    year: int,
    month: int,
    employee_id: int | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if month < 1 or month > 12:
        raise HTTPException(status_code=422, detail="Month must be between 1 and 12")

    query = db.query(Attendance)

    if current_user.role == "employee":
        employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee record not found")

        if employee_id is not None and employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Access denied")

        query = query.filter(Attendance.employee_id == employee.id)
    else:
        if employee_id is not None:
            query = query.filter(Attendance.employee_id == employee_id)

    records = query.filter(
        extract("year", Attendance.attendance_date) == year,
        extract("month", Attendance.attendance_date) == month,
    ).all()

    summary = {
        "year": year,
        "month": month,
        "total_records": len(records),
        "present": 0,
        "absent": 0,
        "late": 0,
        "half_day": 0,
        "total_working_hours": 0.0,
    }

    for record in records:
        status_value = record.status.lower()
        if status_value in summary:
            summary[status_value] += 1

        if record.check_in and record.check_out:
            seconds = (
                record.check_out - record.check_in
            ).total_seconds()

            if seconds > 0:
                summary["total_working_hours"] += seconds / 3600

    summary["total_working_hours"] = round(
        summary["total_working_hours"], 2
    )

    return summary


@router.patch("/{attendance_id}/override")
def override_attendance(
    attendance_id: int,
    status_value: str | None = None,
    check_in: datetime | None = None,
    check_out: datetime | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    allowed_statuses = {"present", "absent", "late", "half_day"}

    if status_value is not None and status_value not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail="Invalid attendance status",
        )

    record = db.query(Attendance).filter(
        Attendance.id == attendance_id
    ).first()

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Attendance record not found",
        )

    if check_in is not None and check_out is not None and check_out < check_in:
        raise HTTPException(
            status_code=422,
            detail="Check-out cannot be before check-in",
        )

    if status_value is not None:
        record.status = status_value

    if check_in is not None:
        record.check_in = check_in

    if check_out is not None:
        record.check_out = check_out

    db.commit()
    db.refresh(record)

    return {
        "message": "Attendance updated successfully",
        "attendance": {
            "id": record.id,
            "employee_id": record.employee_id,
            "attendance_date": record.attendance_date,
            "check_in": record.check_in,
            "check_out": record.check_out,
            "status": record.status,
        },
    }