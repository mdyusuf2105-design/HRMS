from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from app.db.session import Base


class Attendance(Base):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint("employee_id", "attendance_date", name="uq_employee_attendance_date"),
    )

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    attendance_date = Column(Date, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)

    early_checkout_minutes = Column(Integer, nullable=True, default=0)
    overtime_minutes = Column(Integer, nullable=True, default=0)

    status = Column(
        String(20),
        nullable=False,
        default="present",
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

