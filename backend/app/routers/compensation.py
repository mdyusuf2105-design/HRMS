from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.employee import Employee
from app.models.salary_component import SalaryComponent, EmployeeSalaryComponent
from app.models.compensation_revision import CompensationRevision
from app.routers.auth import get_current_user, require_roles

router = APIRouter(prefix="/compensation", tags=["Compensation Management"])

class ComponentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    component_type: str = Field(pattern="^(earning|deduction)$")
    is_taxable: bool = True

class EmployeeComponentCreate(BaseModel):
    employee_id: int
    component_id: int
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    effective_from: date
    effective_to: date | None = None

class RevisionCreate(BaseModel):
    employee_id: int
    basic_salary: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    allowances: Decimal = Field(default=Decimal("0"), ge=0, max_digits=12, decimal_places=2)
    effective_from: date
    reason: str | None = Field(default=None, max_length=255)

@router.post("/components", status_code=201)
def create_component(data: ComponentCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "hr"))):
    name = data.name.strip()
    if not name:
        raise HTTPException(422, "Component name is required")
    if db.query(SalaryComponent).filter(SalaryComponent.name == name).first():
        raise HTTPException(409, "Component name already exists")
    row = SalaryComponent(name=name, component_type=data.component_type, is_taxable=data.is_taxable, created_by=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "component_type": row.component_type, "is_taxable": row.is_taxable, "is_active": row.is_active}

@router.get("/components")
def list_components(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(SalaryComponent).order_by(SalaryComponent.name).all()

@router.patch("/components/{component_id}")
def update_component(component_id: int, is_active: bool, db: Session = Depends(get_db), user=Depends(require_roles("admin", "hr"))):
    row = db.query(SalaryComponent).filter(SalaryComponent.id == component_id).first()
    if not row:
        raise HTTPException(404, "Salary component not found")
    row.is_active = is_active
    db.commit()
    db.refresh(row)
    return {"id": row.id, "name": row.name, "is_active": row.is_active}

@router.post("/employee-components", status_code=201)
def assign_employee_component(data: EmployeeComponentCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "hr"))):
    if data.effective_to and data.effective_to < data.effective_from:
        raise HTTPException(422, "End date cannot precede start date")
    if not db.query(Employee).filter(Employee.id == data.employee_id).first():
        raise HTTPException(404, "Employee not found")
    component = db.query(SalaryComponent).filter(SalaryComponent.id == data.component_id, SalaryComponent.is_active.is_(True)).first()
    if not component:
        raise HTTPException(404, "Active salary component not found")
    row = EmployeeSalaryComponent(employee_id=data.employee_id, component_id=data.component_id, amount=data.amount, effective_from=data.effective_from, effective_to=data.effective_to, created_by=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "employee_id": row.employee_id, "component_id": row.component_id, "amount": row.amount, "effective_from": row.effective_from, "effective_to": row.effective_to}

@router.get("/employee-components/{employee_id}")
def list_employee_components(employee_id: int, on_date: date | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(404, "Employee not found")
    if user.role == "employee" and employee.user_id != user.id:
        raise HTTPException(403, "Access denied")
    query = db.query(EmployeeSalaryComponent).filter(EmployeeSalaryComponent.employee_id == employee_id)
    if on_date:
        query = query.filter(EmployeeSalaryComponent.effective_from <= on_date).filter((EmployeeSalaryComponent.effective_to.is_(None)) | (EmployeeSalaryComponent.effective_to >= on_date))
    return query.order_by(EmployeeSalaryComponent.effective_from.desc()).all()

@router.post("/revisions", status_code=201)
def create_compensation_revision(data: RevisionCreate, db: Session = Depends(get_db), user=Depends(require_roles("admin", "hr"))):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(404, "Employee not found")
    current = db.query(CompensationRevision).filter(CompensationRevision.employee_id == data.employee_id, CompensationRevision.effective_to.is_(None), CompensationRevision.effective_from < data.effective_from).order_by(CompensationRevision.effective_from.desc()).first()
    if current:
        current.effective_to = date.fromordinal(data.effective_from.toordinal() - 1)
    row = CompensationRevision(employee_id=data.employee_id, basic_salary=data.basic_salary, allowances=data.allowances, effective_from=data.effective_from, reason=data.reason, created_by=user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

@router.get("/revisions/{employee_id}")
def list_compensation_revisions(employee_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(404, "Employee not found")
    if user.role == "employee" and employee.user_id != user.id:
        raise HTTPException(403, "Access denied")
    return db.query(CompensationRevision).filter(CompensationRevision.employee_id == employee_id).order_by(CompensationRevision.effective_from.desc()).all()
