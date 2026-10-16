from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SalaryComponentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    component_type: Literal["earning", "deduction"]
    calculation_type: Literal["fixed", "percentage"] = "fixed"


class SalaryComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    component_type: str
    calculation_type: str
    is_active: bool
    created_by: int
    created_at: datetime


class EmployeeSalaryComponentCreate(BaseModel):
    employee_id: int = Field(gt=0)
    component_id: int = Field(gt=0)
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    effective_from: date
    effective_to: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.effective_to and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        return self


class EmployeeSalaryComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    component_id: int
    amount: Decimal
    effective_from: date
    effective_to: date | None
    assigned_by: int
    created_at: datetime


class CompensationRevisionCreate(BaseModel):
    basic_salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    allowances: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    effective_from: date
    reason: str = Field(min_length=3, max_length=1000)


class CompensationRevisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    basic_salary: Decimal
    allowances: Decimal
    effective_from: date
    reason: str
    created_by: int
    created_at: datetime
