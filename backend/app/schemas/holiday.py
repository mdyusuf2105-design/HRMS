from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


HolidayType = Literal["company", "regional", "optional"]


class HolidayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    holiday_date: date
    holiday_type: HolidayType = "company"
    region: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_region(self):
        if self.holiday_type == "regional" and not self.region:
            raise ValueError(
                "Region is required for a regional holiday"
            )
        return self


class HolidayUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    holiday_date: date | None = None
    holiday_type: HolidayType | None = None
    region: str | None = Field(default=None, max_length=100)
    description: str | None = None
    is_active: bool | None = None


class HolidayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    holiday_date: date
    holiday_type: str
    region: str | None
    description: str | None
    is_active: bool
    created_by: int
    created_at: datetime
