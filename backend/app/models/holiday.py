from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from app.db.session import Base


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    holiday_date = Column(Date, nullable=False, index=True)

    # Supported types: company, regional, optional
    holiday_type = Column(String(20), nullable=False, default="company")

    # Used for regional holidays, such as Tamil Nadu.
    region = Column(String(100), nullable=True)

    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

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
