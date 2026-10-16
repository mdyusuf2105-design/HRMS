from app.models.user import User

import calendar
from datetime import date
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

    total_deductions = money(data.deductions + lop_amount)

    net_salary = money(
        data.basic_salary + data.allowances - total_deductions
    )

    if net_salary < 0:
        raise HTTPException(
            status_code=400,
            detail="Total deductions, including LOP, exceed salary and allowances",
        )

    payroll = Payroll(
        employee_id=data.employee_id,
        pay_period=data.pay_period,
        basic_salary=data.basic_salary,
        allowances=data.allowances,
        deductions=total_deductions,
        net_salary=net_salary,
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
        ["Allowances", f"Rs. {payroll.allowances:,.2f}"],
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
