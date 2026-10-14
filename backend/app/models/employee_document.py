from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.db.session import Base


class EmployeeDocument(Base):
    __tablename__ = "employee_documents"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    uploaded_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(100), unique=True, nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)

    uploaded_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )