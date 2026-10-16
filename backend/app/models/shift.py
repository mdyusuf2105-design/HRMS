from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Integer,
    String,
    Time,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)

from sqlalchemy.orm import relationship

from app.db.session import Base


class Shift(Base):
    __tablename__ = "shifts"

    __table_args__ = (
        UniqueConstraint("name", name="uq_shift_name"),
    )

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    grace_period_minutes = Column(
        Integer,
        nullable=False,
        default=10,
    )

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )


class EmployeeShift(Base):
    __tablename__ = "employee_shifts"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    shift_id = Column(
        Integer,
        ForeignKey("shifts.id"),
        nullable=False,
        index=True,
    )

    assigned_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    assigned_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)

    shift = relationship("Shift")


class DepartmentShift(Base):
    __tablename__ = "department_shifts"

    id = Column(Integer, primary_key=True, index=True)

    department = Column(String(100), nullable=False, index=True)

    shift_id = Column(
        Integer,
        ForeignKey("shifts.id"),
        nullable=False,
        index=True,
    )

    assigned_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    assigned_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)

    shift = relationship("Shift")
