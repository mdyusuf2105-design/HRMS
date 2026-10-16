from datetime import datetime, time
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ShiftCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    start_time: time
    end_time: time
    grace_period_minutes: int = Field(default=10, ge=0, le=180)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_shift(self):
        if not self.name.strip():
            raise ValueError("Shift name is required")
        if self.start_time == self.end_time:
            raise ValueError("Shift start and end times cannot be equal")
        return self


class ShiftUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    start_time: time | None = None
    end_time: time | None = None
    grace_period_minutes: int | None = Field(default=None, ge=0, le=180)
    is_active: bool | None = None


class ShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int
    is_active: bool
    created_by: int
    created_at: datetime


class EmployeeShiftCreate(BaseModel):
    employee_id: int = Field(gt=0)
    shift_id: int = Field(gt=0)


class EmployeeShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    shift_id: int
    assigned_by: int
    assigned_at: datetime


class EmployeeShiftAssignmentCreate(BaseModel):
    employee_id: int = Field(gt=0)
    shift_id: int = Field(gt=0)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self


class DepartmentShiftCreate(BaseModel):
    department: str = Field(min_length=1, max_length=100)
    shift_id: int = Field(gt=0)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if not self.department.strip():
            raise ValueError("Department is required")
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self


class DepartmentShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    department: str
    shift_id: int
    assigned_by: int
    assigned_at: datetime
    effective_from: date
    effective_to: date | None


from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class DepartmentShiftCreate(BaseModel):
    department: str = Field(min_length=1, max_length=100)
    shift_id: int
    effective_from: date
    effective_to: date | None = None

class DepartmentShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    department: str
    shift_id: int
    assigned_by: int
    assigned_at: object
    effective_from: date
    effective_to: date | None


from datetime import date
from pydantic import BaseModel, ConfigDict, Field

class DepartmentShiftCreate(BaseModel):
    department: str = Field(min_length=1, max_length=100)
    shift_id: int
    effective_from: date
    effective_to: date | None = None

class DepartmentShiftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    department: str
    shift_id: int
    assigned_by: int
    assigned_at: object
    effective_from: date
    effective_to: date | None
