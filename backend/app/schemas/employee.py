from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EmployeeCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    employee_code: str = Field(min_length=2, max_length=20)
    department: str = Field(min_length=2, max_length=100)
    designation: str = Field(min_length=2, max_length=100)
    joining_date: date
    salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class EmployeeUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=2, max_length=100)
    designation: str | None = Field(default=None, min_length=2, max_length=100)
    joining_date: date | None = None
    salary: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2
    )


class EmployeeResponse(BaseModel):
    id: int
    user_id: int
    employee_code: str
    department: str
    designation: str
    joining_date: date
    salary: Decimal
    full_name: str
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)