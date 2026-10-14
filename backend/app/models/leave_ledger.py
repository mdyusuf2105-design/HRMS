
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, func

from app.db.session import Base


class LeaveLedger(Base):
    __tablename__ = "leave_ledger"

    id = Column(Integer, primary_key=True, index=True)

    leave_id = Column(
        Integer,
        ForeignKey("leaves.id"),
        unique=True,
        nullable=False,
    )

    paid_days = Column(Numeric(7, 2), nullable=False, default=0)
    lop_days = Column(Numeric(7, 2), nullable=False, default=0)

    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
