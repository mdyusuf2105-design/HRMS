from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.holiday import Holiday
from app.models.shift import EmployeeShift, Shift, DepartmentShift
from app.routers.auth import get_current_user, require_roles
from app.schemas.attendance import AttendanceCreate, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["Attendance"])

def get_shift_for_date(db: Session, employee: Employee, target_date: date):
    """Resolve the shift effective on a particular attendance date."""
    assignment = db.query(EmployeeShift).filter(
        EmployeeShift.employee_id == employee.id,
        EmployeeShift.effective_from.isnot(None),
        EmployeeShift.effective_from <= target_date,
        (EmployeeShift.effective_to.is_(None) |
         (EmployeeShift.effective_to >= target_date)),
    ).order_by(
        EmployeeShift.effective_from.desc(),
        EmployeeShift.id.desc(),
    ).first()

    if assignment:
        shift = db.query(Shift).filter(Shift.id == assignment.shift_id).first()
        if shift:
            return shift

    department = getattr(employee, "department", None)
    if department:
        assignment = db.query(DepartmentShift).filter(
            DepartmentShift.department == department,
            DepartmentShift.effective_from <= target_date,
            (DepartmentShift.effective_to.is_(None) |
             (DepartmentShift.effective_to >= target_date)),
        ).order_by(
            DepartmentShift.effective_from.desc(),
            DepartmentShift.id.desc(),
        ).first()
        if assignment:
            shift = db.query(Shift).filter(Shift.id == assignment.shift_id).first()
            if shift:
                return shift

    # Backward compatibility for assignments created before effective dates.
    assignment = db.query(EmployeeShift).filter(
        EmployeeShift.employee_id == employee.id,
        EmployeeShift.effective_from.is_(None),
    ).order_by(
        EmployeeShift.assigned_at.desc(),
        EmployeeShift.id.desc(),
    ).first()

    return db.query(Shift).filter(
        Shift.id == assignment.shift_id
    ).first() if assignment else None


def shift_end_datetime(target_date: date, shift: Shift) -> datetime:
    start = datetime.combine(target_date, shift.start_time)
    end = datetime.combine(target_date, shift.end_time)
    if end <= start:
        end += timedelta(days=1)
    return end




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

    check_in_time = datetime.now()
    status_value = "present"

    shift = get_shift_for_date(db, employee, today)

    if shift and shift.is_active:
        scheduled_start = datetime.combine(today, shift.start_time)
        late_threshold = scheduled_start + timedelta(
            minutes=shift.grace_period_minutes
        )
        if check_in_time > late_threshold:
            status_value = "late"

    record = Attendance(
        employee_id=employee.id,
        attendance_date=today,
        check_in=check_in_time,
        status=status_value,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    send_attendance_notification(
        db,
        employee,
        "Attendance checked in",
        f"Your check-in for {today.isoformat()} was recorded as {record.status}.",
    )
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
    record.early_checkout_minutes = 0
    record.overtime_minutes = 0

    shift = get_shift_for_date(db, employee, record.attendance_date)
    if shift and shift.is_active:
        scheduled_end = shift_end_datetime(record.attendance_date, shift)

        if record.check_out < scheduled_end:
            record.early_checkout_minutes = int(
                (scheduled_end - record.check_out).total_seconds() // 60
            )
        elif record.check_out > scheduled_end:
            record.overtime_minutes = int(
                (record.check_out - scheduled_end).total_seconds() // 60
            )

    db.commit()
    db.refresh(record)

    send_attendance_notification(
        db,
        employee,
        "Attendance checked out",
        (
            f"Your check-out for {record.attendance_date.isoformat()} was recorded. "
            f"Early checkout: {record.early_checkout_minutes or 0} minutes; "
            f"overtime: {record.overtime_minutes or 0} minutes."
        ),
    )
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




def send_attendance_notification(
    db: Session,
    employee: Employee,
    title: str,
    message: str,
):
    """Send an attendance notification when the employee allows it."""
    try:
        from app.models.notification import Notification
        from app.models.notification_preference import NotificationPreference

        preference = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == employee.user_id,
            NotificationPreference.notification_type == "attendance",
        ).first()

        if preference is not None and not preference.is_enabled:
            return

        db.add(Notification(
            user_id=employee.user_id,
            title=title,
            message=message,
            notification_type="attendance",
        ))
        db.commit()
    except Exception:
        # Attendance must remain saved even if notification delivery fails.
        db.rollback()


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
    elif employee_id is not None:
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

    from calendar import monthrange
    from datetime import date

    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    holiday_query = db.query(Holiday).filter(
        Holiday.is_active.is_(True),
        Holiday.holiday_date >= first_day,
        Holiday.holiday_date <= last_day,
        Holiday.holiday_type.in_(["company", "regional"]),
    )

    holidays = holiday_query.order_by(Holiday.holiday_date.asc()).all()

    summary["holidays_in_month"] = [
        {
            "id": holiday.id,
            "name": holiday.name,
            "holiday_date": holiday.holiday_date.isoformat(),
            "holiday_type": holiday.holiday_type,
            "region": holiday.region,
        }
        for holiday in holidays
    ]
    summary["holiday_count"] = len(holidays)

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