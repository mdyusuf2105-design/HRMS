from decimal import Decimal

from app.db.session import SessionLocal
from app.models.leave import Leave
from app.models.leave_balance import LeaveBalance
from app.models.leave_ledger import LeaveLedger

db = SessionLocal()

try:
    leaves = db.query(Leave).filter(
        Leave.status == "approved"
    ).all()

    for leave in leaves:
        existing = db.query(LeaveLedger).filter(
            LeaveLedger.leave_id == leave.id
        ).first()

        if existing:
            print(f"Leave {leave.id}: already recorded; skipped.")
            continue

        total_days = Decimal(
            (leave.end_date - leave.start_date).days + 1
        )

        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == leave.employee_id,
            LeaveBalance.leave_type == leave.leave_type.lower(),
        ).with_for_update().first()

        available = Decimal("0")
        if balance:
            available = max(
                Decimal("0"),
                Decimal(str(balance.allocated_days))
                - Decimal(str(balance.used_days)),
            )

        paid = min(total_days, available)
        lop = total_days - paid

        if balance:
            balance.used_days = Decimal(
                str(balance.used_days)
            ) + paid

        db.add(
            LeaveLedger(
                leave_id=leave.id,
                paid_days=paid,
                lop_days=lop,
            )
        )

        print(
            f"Leave {leave.id}: "
            f"{paid} paid day(s), {lop} LOP day(s)"
        )

    db.commit()
    print("Repair completed successfully.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
