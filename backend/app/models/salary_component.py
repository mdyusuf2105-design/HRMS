from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, func
from app.db.session import Base

class SalaryComponent(Base):
    __tablename__ = "salary_components"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    component_type = Column(String(20), nullable=False)
    calculation_type = Column(String(20), nullable=False, default="fixed", server_default="fixed")
    is_taxable = Column(Boolean, nullable=False, default=True, server_default="1")
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

class EmployeeSalaryComponent(Base):
    __tablename__ = "employee_salary_components"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    component_id = Column(Integer, ForeignKey("salary_components.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
