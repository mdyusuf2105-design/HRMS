
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)

from app.db.session import Base


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    leave_type = Column(String(30), nullable=False)
    allocated_days = Column(Numeric(7, 2), nullable=False, default=0)
    used_days = Column(Numeric(7, 2), nullable=False, default=0)

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type",
            name="uq_leave_balance_employee_type",
        ),
    )
