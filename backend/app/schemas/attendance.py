from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AttendanceCreate(BaseModel):
    employee_id: int | None = None
    attendance_date: date


class AttendanceResponse(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in: datetime | None
    check_out: datetime | None
    early_checkout_minutes: int | None = 0
    overtime_minutes: int | None = 0
    status: Literal["present", "absent", "late", "half_day"]

    model_config = ConfigDict(from_attributes=True)
