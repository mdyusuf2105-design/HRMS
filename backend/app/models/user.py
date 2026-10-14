
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(
        Enum("admin", "hr", "employee", name="user_role"),
        nullable=False,
        default="employee",
    )

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
