from app.models.user import User

import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.audit import log_action
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.leave_ledger import LeaveLedger
from app.models.payroll import Payroll
from app.routers.auth import get_current_user, require_roles
from app.schemas.payroll import PayrollCreate, PayrollResponse


from app.models.payroll_enhancements import (
    SalaryComponent,
    EmployeeSalaryComponent,
    CompensationRevision,
)
from app.schemas.payroll_enhancement import (
    SalaryComponentCreate,
    SalaryComponentResponse,
    EmployeeSalaryComponentCreate,
    EmployeeSalaryComponentResponse,
    CompensationRevisionCreate,
    CompensationRevisionResponse,
)

router = APIRouter(prefix="/payroll", tags=["Payroll"])

CENT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def get_month_dates(pay_period: date):
    last_day = calendar.monthrange(
        pay_period.year,
        pay_period.month,
    )[1]

    return date(
        pay_period.year,
        pay_period.month,
        1,
    ), date(
        pay_period.year,
        pay_period.month,
        last_day,
    ), last_day


def calculate_monthly_lop(
    db: Session,
    employee_id: int,
    pay_period: date,
    basic_salary: Decimal,
):
    month_start, month_end, days_in_month = get_month_dates(pay_period)

    records = (
        db.query(Leave, LeaveLedger)
        .join(LeaveLedger, LeaveLedger.leave_id == Leave.id)
        .filter(
            Leave.employee_id == employee_id,
            Leave.status == "approved",
            Leave.start_date <= month_end,
            Leave.end_date >= month_start,
            LeaveLedger.lop_days > 0,
        )
        .all()
    )

    total_lop_days = Decimal("0")

    for leave, ledger in records:
        overlap_start = max(leave.start_date, month_start)
        overlap_end = min(leave.end_date, month_end)

        overlap_days = Decimal(
            (overlap_end - overlap_start).days + 1
        )
        full_leave_days = Decimal(
            (leave.end_date - leave.start_date).days + 1
        )

        # Allocate LOP proportionally when a leave spans months.
        monthly_lop_days = (
            Decimal(str(ledger.lop_days))
            * overlap_days
            / full_leave_days
        )

        total_lop_days += monthly_lop_days

    daily_basic_salary = basic_salary / Decimal(days_in_month)
    lop_amount = money(daily_basic_salary * total_lop_days)

    return total_lop_days, lop_amount


@router.post(
    "/",
    response_model=PayrollResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payroll(
    data: PayrollCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    employee = db.query(Employee).filter(
        Employee.id == data.employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    if data.pay_period.day != 1:
        raise HTTPException(
            status_code=400,
            detail="pay_period must be the first day of the month",
        )

    existing = db.query(Payroll).filter(
        Payroll.employee_id == data.employee_id,
        Payroll.pay_period == data.pay_period,
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Payroll already exists for this employee and period",
        )

    _, lop_days, lop_amount = (
        *get_month_dates(data.pay_period)[:0],
        None,
        None,
    ) if False else (None, None, None)

    # Calculate LOP from approved leave ledger entries.
    monthly_lop_days, lop_amount = calculate_monthly_lop(
        db=db,
        employee_id=data.employee_id,
        pay_period=data.pay_period,
        basic_salary=data.basic_salary,
    )

    # Apply the latest compensation revision effective for this pay period,
    # if one exists. Otherwise retain the values supplied in the request.
    revision = db.query(CompensationRevision).filter(
        CompensationRevision.employee_id == data.employee_id,
        CompensationRevision.effective_from <= data.pay_period,
    ).order_by(
        CompensationRevision.effective_from.desc(),
        CompensationRevision.id.desc(),
    ).first()

    basic_salary = Decimal(str(revision.basic_salary)) if revision else data.basic_salary
    base_allowances = Decimal(str(revision.allowances)) if revision else data.allowances

    # Apply employee salary components effective during the payroll month.
    _, month_end, _ = get_month_dates(data.pay_period)
    component_assignments = (
        db.query(EmployeeSalaryComponent, SalaryComponent)
        .join(SalaryComponent, EmployeeSalaryComponent.component_id == SalaryComponent.id)
        .filter(
            EmployeeSalaryComponent.employee_id == data.employee_id,
            EmployeeSalaryComponent.effective_from <= month_end,
            (EmployeeSalaryComponent.effective_to.is_(None) |
             (EmployeeSalaryComponent.effective_to >= data.pay_period)),
            SalaryComponent.is_active.is_(True),
        )
        .all()
    )

    component_earnings = Decimal("0.00")
    component_deductions = Decimal("0.00")

    for assignment, component in component_assignments:
        amount = Decimal(str(assignment.amount))
        if component.calculation_type == "percentage":
            amount = money(basic_salary * amount / Decimal("100"))
        else:
            amount = money(amount)

        if component.component_type == "earning":
            component_earnings += amount
        else:
            component_deductions += amount

    component_earnings = money(component_earnings)
    component_deductions = money(component_deductions)

    # Overtime is calculated from recorded minutes for this payroll month.
    overtime_minutes = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id == data.employee_id,
            Attendance.attendance_date >= data.pay_period,
            Attendance.attendance_date <= month_end,
        )
        .with_entities(Attendance.overtime_minutes)
        .all()
    )
    total_overtime_minutes = sum(int(row[0] or 0) for row in overtime_minutes)
    overtime_pay = money(
        Decimal(total_overtime_minutes)
        * data.overtime_rate_per_hour
        / Decimal("60")
    )

    total_allowances = money(base_allowances + component_earnings)
    total_deductions = money(
        data.deductions + component_deductions + lop_amount
    )
    bonus = money(data.bonus)

    net_salary = money(
        basic_salary + total_allowances + bonus + overtime_pay - total_deductions
    )

    if net_salary < 0:
        raise HTTPException(
            status_code=400,
            detail="Total deductions, including LOP, exceed salary and allowances",
        )

    payroll = Payroll(
        employee_id=data.employee_id,
        pay_period=data.pay_period,
        basic_salary=basic_salary,
        allowances=total_allowances,
        deductions=total_deductions,
        net_salary=net_salary,
        bonus=bonus,
        overtime_pay=overtime_pay,
        created_by=current_user.id,
    )

    try:
        db.add(payroll)
        db.flush()
        log_action(
            db=db,
            user_id=current_user.id,
            action="payroll.created",
            entity_type="payroll",
            entity_id=payroll.id,
            details={
                "employee_id": payroll.employee_id,
                "pay_period": str(payroll.pay_period),
                "net_salary": str(payroll.net_salary),
            },
        )
        db.commit()
        db.refresh(payroll)
    except Exception:
        db.rollback()
        raise

    # payroll.in_app_notification: notify after payroll creation succeeds.
    try:
        from app.models.notification import Notification
        from app.models.notification_preference import NotificationPreference
        from app.models.user import User

        employee = db.query(Employee).filter(
            Employee.id == payroll.employee_id
        ).first()

        if employee:
            recipient = db.query(User).filter(
                User.id == employee.user_id,
                User.is_active.is_(True),
            ).first()

            if recipient:
                preference = db.query(NotificationPreference).filter(
                    NotificationPreference.user_id == recipient.id,
                    NotificationPreference.notification_type == "payroll",
                ).first()

                if preference is None or preference.is_enabled:
                    db.add(Notification(
                        user_id=recipient.id,
                        title="Payroll generated",
                        message=(
                            f"Your payroll for "
                            f"{payroll.pay_period.strftime('%B %Y')} "
                            f"has been generated. Net salary: "
                            f"Rs. {payroll.net_salary:,.2f}."
                        ),
                        notification_type="payroll",
                    ))
                    db.commit()
    except Exception:
        db.rollback()

    return payroll


@router.get("/", response_model=list[PayrollResponse])
def list_payroll(
    employee_id: int | None = None,
    pay_period: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Payroll)

    if current_user.role == "employee":
        employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()

        if not employee:
            return []

        query = query.filter(Payroll.employee_id == employee.id)

    elif employee_id is not None:
        query = query.filter(Payroll.employee_id == employee_id)

    if pay_period is not None:
        query = query.filter(Payroll.pay_period == pay_period)

    return query.order_by(Payroll.pay_period.desc()).all()




@router.post("/components", response_model=SalaryComponentResponse, status_code=201)
def create_salary_component(
    data: SalaryComponentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Component name is required")

    if db.query(SalaryComponent).filter(SalaryComponent.name == name).first():
        raise HTTPException(status_code=409, detail="Salary component already exists")

    component = SalaryComponent(
        name=name,
        component_type=data.component_type,
        calculation_type=data.calculation_type,
        created_by=current_user.id,
    )
    db.add(component)
    db.commit()
    db.refresh(component)
    return component


@router.get("/components", response_model=list[SalaryComponentResponse])
def list_salary_components(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    query = db.query(SalaryComponent)
    if not include_inactive:
        query = query.filter(SalaryComponent.is_active.is_(True))
    return query.order_by(SalaryComponent.name.asc()).all()


@router.patch("/components/{component_id}/deactivate")
def deactivate_salary_component(
    component_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    component = db.query(SalaryComponent).filter(
        SalaryComponent.id == component_id
    ).first()
    if not component:
        raise HTTPException(status_code=404, detail="Salary component not found")
    component.is_active = False
    db.commit()
    return {"message": "Salary component deactivated", "component_id": component.id}


@router.post(
    "/employee-components",
    response_model=EmployeeSalaryComponentResponse,
    status_code=201,
)
def assign_employee_salary_component(
    data: EmployeeSalaryComponentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    if not db.query(Employee).filter(Employee.id == data.employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")

    component = db.query(SalaryComponent).filter(
        SalaryComponent.id == data.component_id,
        SalaryComponent.is_active.is_(True),
    ).first()
    if not component:
        raise HTTPException(status_code=404, detail="Active salary component not found")

    assignment = EmployeeSalaryComponent(
        employee_id=data.employee_id,
        component_id=data.component_id,
        amount=data.amount,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get(
    "/employee-components/{employee_id}",
    response_model=list[EmployeeSalaryComponentResponse],
)
def list_employee_salary_components(
    employee_id: int,
    as_of: date | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if current_user.role == "employee" and employee.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    query = db.query(EmployeeSalaryComponent).filter(
        EmployeeSalaryComponent.employee_id == employee_id
    )
    if as_of:
        query = query.filter(
            EmployeeSalaryComponent.effective_from <= as_of,
            (EmployeeSalaryComponent.effective_to.is_(None) |
             (EmployeeSalaryComponent.effective_to >= as_of)),
        )
    return query.order_by(
        EmployeeSalaryComponent.effective_from.desc(),
        EmployeeSalaryComponent.id.desc(),
    ).all()


@router.post(
    "/compensation/{employee_id}/revisions",
    response_model=CompensationRevisionResponse,
    status_code=201,
)
def create_compensation_revision(
    employee_id: int,
    data: CompensationRevisionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    if not db.query(Employee).filter(Employee.id == employee_id).first():
        raise HTTPException(status_code=404, detail="Employee not found")

    previous = db.query(CompensationRevision).filter(
        CompensationRevision.employee_id == employee_id,
        CompensationRevision.effective_from >= data.effective_from,
    ).order_by(
        CompensationRevision.effective_from.asc(),
        CompensationRevision.id.asc(),
    ).first()

    if previous and previous.effective_from == data.effective_from:
        raise HTTPException(
            status_code=409,
            detail="A compensation revision already exists for this effective date",
        )

    current = db.query(CompensationRevision).filter(
        CompensationRevision.employee_id == employee_id,
        CompensationRevision.effective_from < data.effective_from,
        (CompensationRevision.effective_to.is_(None)) |
        (CompensationRevision.effective_to >= data.effective_from),
    ).order_by(
        CompensationRevision.effective_from.desc(),
        CompensationRevision.id.desc(),
    ).first()

    if current:
        from datetime import timedelta
        current.effective_to = data.effective_from - timedelta(days=1)

    revision = CompensationRevision(
        employee_id=employee_id,
        basic_salary=data.basic_salary,
        allowances=data.allowances,
        effective_from=data.effective_from,
        reason=data.reason.strip(),
        created_by=current_user.id,
    )
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return revision


@router.get(
    "/compensation/{employee_id}/history",
    response_model=list[CompensationRevisionResponse],
)
def compensation_history(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    if current_user.role == "employee" and employee.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return db.query(CompensationRevision).filter(
        CompensationRevision.employee_id == employee_id
    ).order_by(
        CompensationRevision.effective_from.desc(),
        CompensationRevision.id.desc(),
    ).all()


@router.get("/{payroll_id}", response_model=PayrollResponse)
def get_payroll(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payroll = db.query(Payroll).filter(
        Payroll.id == payroll_id
    ).first()

    if not payroll:
        raise HTTPException(
            status_code=404,
            detail="Payroll record not found",
        )

    if current_user.role == "employee":
        employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()

        if not employee or payroll.employee_id != employee.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied",
            )

    return payroll


@router.patch("/{payroll_id}/lock")
def lock_payroll(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    payroll = (
        db.query(Payroll)
        .filter(Payroll.id == payroll_id)
        .with_for_update()
        .first()
    )

    if not payroll:
        raise HTTPException(
            status_code=404,
            detail="Payroll record not found",
        )

    if payroll.is_locked:
        raise HTTPException(
            status_code=409,
            detail="Payroll is already locked",
        )

    payroll.is_locked = True
    log_action(
        db=db,
        user_id=current_user.id,
        action="payroll.locked",
        entity_type="payroll",
        entity_id=payroll.id,
        details={
            "employee_id": payroll.employee_id,
            "pay_period": str(payroll.pay_period),
        },
    )
    db.commit()

    return {
        "message": "Payroll locked successfully",
        "payroll_id": payroll.id,
        "is_locked": True,
    }


from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from fastapi.responses import StreamingResponse


@router.get("/{payroll_id}/salary-slip")
def download_salary_slip(
    payroll_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payroll = db.query(Payroll).filter(
        Payroll.id == payroll_id
    ).first()

    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    employee = db.query(Employee).filter(
        Employee.id == payroll.employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if current_user.role == "employee":
        if employee.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
    elif current_user.role not in {"admin", "hr"}:
        raise HTTPException(status_code=403, detail="Access denied")

    user = db.query(User).filter(User.id == employee.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Employee user not found")

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = [
        Paragraph("SALARY SLIP", styles["Title"]),
        Spacer(1, 18),
        Paragraph(f"Employee: {user.full_name}", styles["Normal"]),
        Paragraph(f"Employee Code: {employee.employee_code}", styles["Normal"]),
        Paragraph(f"Department: {employee.department}", styles["Normal"]),
        Paragraph(
            f"Pay Period: {payroll.pay_period.strftime('%B %Y')}",
            styles["Normal"],
        ),
        Paragraph(
            f"Payroll Status: {'Locked' if payroll.is_locked else 'Unlocked'}",
            styles["Normal"],
        ),
        Spacer(1, 18),
    ]

    table = Table([
        ["Description", "Amount (INR)"],
        ["Basic Salary", f"Rs. {payroll.basic_salary:,.2f}"],
        ["Allowances and component earnings", f"Rs. {payroll.allowances:,.2f}"],
        ["Bonus", f"Rs. {payroll.bonus:,.2f}"],
        ["Overtime Pay", f"Rs. {payroll.overtime_pay:,.2f}"],
        ["Total Deductions (including LOP)", f"Rs. {payroll.deductions:,.2f}"],
        ["NET SALARY", f"Rs. {payroll.net_salary:,.2f}"],
    ], colWidths=[310, 150])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243447")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8F5E9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ("PADDING", (0, 0), (-1, -1), 9),
    ]))

    elements.extend([
        table,
        Spacer(1, 20),
        Paragraph("System-generated salary slip.", styles["Normal"]),
    ])

    pdf.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="salary_slip_{payroll.id}.pdf"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/preview/{employee_id}")
def payroll_preview(
    employee_id: int,
    year: int,
    month: int,
    basic_salary: Decimal,
    allowances: Decimal = Decimal("0.00"),
    deductions: Decimal = Decimal("0.00"),
    region: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    from datetime import date
    from app.models.attendance import Attendance
    from app.models.holiday import Holiday
    from app.services.working_days import count_working_days

    if month < 1 or month > 12:
        raise HTTPException(
            status_code=422,
            detail="Month must be between 1 and 12",
        )

    if basic_salary < 0 or allowances < 0 or deductions < 0:
        raise HTTPException(
            status_code=422,
            detail="Salary, allowances, and deductions cannot be negative",
        )

    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    month_start = date(year, month, 1)
    _, month_end, days_in_month = get_month_dates(month_start)

    working_days = count_working_days(
        db=db,
        start_date=month_start,
        end_date=month_end,
        region=region.strip() if region else None,
    )

    attendance_records = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.attendance_date >= month_start,
        Attendance.attendance_date <= month_end,
    ).all()

    attendance_summary = {
        "total_records": len(attendance_records),
        "present": 0,
        "absent": 0,
        "late": 0,
        "half_day": 0,
        "total_working_hours": 0.0,
    }

    for record in attendance_records:
        status_value = record.status.lower()
        if status_value in attendance_summary:
            attendance_summary[status_value] += 1

        if record.check_in and record.check_out:
            seconds = (
                record.check_out - record.check_in
            ).total_seconds()
            if seconds > 0:
                attendance_summary["total_working_hours"] += seconds / 3600

    attendance_summary["total_working_hours"] = round(
        attendance_summary["total_working_hours"], 2
    )

    # Read-only attendance reconciliation; never changes salary calculations.
    from app.models.leave import Leave

    today = date.today()
    reconciliation_end = min(today, month_end)
    reconciliation_start = month_start

    expected_working_dates = set()
    approved_leave_working_dates = set()

    if reconciliation_end >= reconciliation_start:
        current_date = reconciliation_start
        while current_date <= reconciliation_end:
            day_result = count_working_days(
                db=db,
                start_date=current_date,
                end_date=current_date,
                region=region.strip() if region else None,
            )
            if day_result["working_days"] == 1:
                expected_working_dates.add(current_date)
            current_date += timedelta(days=1)

        approved_leaves = db.query(Leave).filter(
            Leave.employee_id == employee_id,
            Leave.status == "approved",
            Leave.start_date <= reconciliation_end,
            Leave.end_date >= reconciliation_start,
        ).all()

        for leave in approved_leaves:
            leave_start = max(leave.start_date, reconciliation_start)
            leave_end = min(leave.end_date, reconciliation_end)
            leave_date = leave_start

            while leave_date <= leave_end:
                if leave_date in expected_working_dates:
                    approved_leave_working_dates.add(leave_date)
                leave_date += timedelta(days=1)

    expected_attendance_dates = (
        expected_working_dates - approved_leave_working_dates
    )

    recorded_working_dates = {
        record.attendance_date
        for record in attendance_records
        if record.attendance_date in expected_working_dates
    }

    leave_attendance_overlap_dates = (
        recorded_working_dates & approved_leave_working_dates
    )

    missing_attendance_dates = (
        expected_attendance_dates - recorded_working_dates
    )

    reconciliation_warnings = []
    if missing_attendance_dates:
        reconciliation_warnings.append(
            "Some past working days have no attendance record. "
            "Review attendance and approved leave before payroll finalization."
        )

    if leave_attendance_overlap_dates:
        reconciliation_warnings.append(
            "Attendance records overlap approved leave dates. "
            "Review these dates before payroll finalization."
        )

    attendance_reconciliation = {
        "as_of_date": (
            reconciliation_end.isoformat()
            if reconciliation_end >= reconciliation_start else None
        ),
        "expected_working_days_to_date": len(expected_working_dates),
        "approved_leave_working_days_to_date": len(
            approved_leave_working_dates
        ),
        "expected_attendance_days_to_date": len(expected_attendance_dates),
        "recorded_attendance_days_on_working_days": len(
            recorded_working_dates
        ),
        "possible_missing_attendance_days": len(missing_attendance_dates),
        "missing_dates_for_review": [
            day.isoformat() for day in sorted(missing_attendance_dates)
        ],
        "warnings": reconciliation_warnings,
        "note": (
            "Missing records are review flags, not confirmed absences. "
            "No salary deduction is calculated from these flags."
        ),
    }

    lop_days, lop_amount = calculate_monthly_lop(
        db=db,
        employee_id=employee_id,
        pay_period=month_start,
        basic_salary=basic_salary,
    )

    total_deductions = money(deductions + lop_amount)
    net_salary = money(basic_salary + allowances - total_deductions)

    return {
        "employee_id": employee_id,
        "pay_period": month_start.isoformat(),
        "currency": "INR",
        "preview_only": True,
        "saved_payroll_changed": False,
        "working_days": working_days,
        "attendance_reconciliation": attendance_reconciliation,
        "attendance": attendance_summary,
        "approved_leave_lop_days": str(lop_days.quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )),
        "estimated_lop_deduction": str(lop_amount),
        "basic_salary": str(money(basic_salary)),
        "allowances": str(money(allowances)),
        "manual_deductions": str(money(deductions)),
        "total_deductions_including_lop": str(total_deductions),
        "estimated_net_salary": str(net_salary),
        "payroll_warnings": (
            ["Estimated net salary is negative; review deductions."]
            if net_salary < 0 else []
        ),
        "note": (
            "Attendance and working days are shown for review. "
            "Absent, late, and half-day statuses do not add deductions "
            "automatically. Approved leave LOP is calculated using the "
            "existing leave-ledger rules."
        ),
    }
