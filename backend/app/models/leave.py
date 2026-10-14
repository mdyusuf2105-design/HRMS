from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func

from app.db.session import Base


class Leave(Base):
    __tablename__ = "leaves"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    leave_type = Column(String(30), nullable=False)
    reason = Column(Text, nullable=False)

    status = Column(
        String(20),
        nullable=False,
        default="pending",
    )

    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
