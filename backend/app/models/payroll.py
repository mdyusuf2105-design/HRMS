
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)

from app.db.session import Base


class Payroll(Base):
    __tablename__ = "payroll"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "pay_period",
            name="uq_employee_pay_period",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    pay_period = Column(Date, nullable=False)
    basic_salary = Column(Numeric(12, 2), nullable=False)
    allowances = Column(Numeric(12, 2), nullable=False, default=0)
    deductions = Column(Numeric(12, 2), nullable=False, default=0)
    net_salary = Column(Numeric(12, 2), nullable=False)
    bonus = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    overtime_pay = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")

    is_locked = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
