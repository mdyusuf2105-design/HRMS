from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PayrollCreate(BaseModel):
    employee_id: int = Field(gt=0)
    pay_period: date
    basic_salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    allowances: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)
    deductions: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)


class PayrollResponse(BaseModel):
    id: int
    employee_id: int
    pay_period: date
    basic_salary: Decimal
    allowances: Decimal
    deductions: Decimal
    net_salary: Decimal
    created_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
