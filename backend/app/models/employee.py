
from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)

from app.db.session import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    employee_code = Column(String(20), unique=True, nullable=False)
    department = Column(String(100), nullable=False)
    designation = Column(String(100), nullable=False)
    joining_date = Column(Date, nullable=False)
    salary = Column(Numeric(12, 2), nullable=False, default=0)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
