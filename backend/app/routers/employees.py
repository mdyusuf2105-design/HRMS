
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.audit import log_action
from app.db.session import get_db
from app.models.employee import Employee
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.models.user import User
from app.routers.auth import require_roles
from app.models.employee import Employee

router = APIRouter(prefix="/employees", tags=["Employees"])


def employee_response(employee, user):
    return {
        "id": employee.id,
        "user_id": user.id,
        "employee_code": employee.employee_code,
        "department": employee.department,
        "designation": employee.designation,
        "joining_date": employee.joining_date,
        "salary": employee.salary,
        "full_name": user.full_name,
        "email": user.email,
        "is_active": user.is_active,
    }


@router.post(
    "/",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    email = str(data.email).lower()

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    if db.query(Employee).filter(
        Employee.employee_code == data.employee_code
    ).first():
        raise HTTPException(status_code=409, detail="Employee code already exists")

    user = User(
        full_name=data.full_name,
        email=email,
        hashed_password=hash_password(data.password),
        role="employee",
    )
    db.add(user)
    db.flush()

    employee = Employee(
        user_id=user.id,
        employee_code=data.employee_code,
        department=data.department,
        designation=data.designation,
        joining_date=data.joining_date,
        salary=data.salary,
    )
    db.add(employee)
    db.flush()

    log_action(
        db=db,
        user_id=current_user.id,
        action="employee.created",
        entity_type="employee",
        entity_id=employee.id,
        details={
            "employee_code": employee.employee_code,
            "department": employee.department,
        },
    )

    try:
        db.commit()
        db.refresh(employee)
        db.refresh(user)
    except Exception:
        db.rollback()
        raise

    return employee_response(employee, user)


@router.get("/", response_model=list[EmployeeResponse])
def list_employees(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    rows = (
        db.query(Employee, User)
        .join(User, Employee.user_id == User.id)
        .order_by(Employee.id)
        .all()
    )
    return [employee_response(employee, user) for employee, user in rows]


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    row = (
        db.query(Employee, User)
        .join(User, Employee.user_id == User.id)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")

    return employee_response(*row)


@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(
    employee_id: int,
    data: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    row = (
        db.query(Employee, User)
        .join(User, Employee.user_id == User.id)
        .filter(Employee.id == employee_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Employee not found")

    employee, user = row
    changes = data.model_dump(exclude_unset=True)
    changed_fields = sorted(changes.keys())

    if "full_name" in changes:
        if changes["full_name"] is None:
            raise HTTPException(status_code=422, detail="Name cannot be null")
        user.full_name = changes.pop("full_name")

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null",
            )
        setattr(employee, field, value)

    log_action(
        db=db,
        user_id=current_user.id,
        action="employee.updated",
        entity_type="employee",
        entity_id=employee.id,
        details={"changed_fields": changed_fields},
    )
    db.commit()
    db.refresh(employee)
    db.refresh(user)

    return employee_response(employee, user)


@router.patch("/{employee_id}/deactivate")
def deactivate_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    user = db.query(User).filter(User.id == employee.user_id).first()
    was_active = user.is_active
    user.is_active = False
    if was_active:
        log_action(
            db=db,
            user_id=current_user.id,
            action="employee.deactivated",
            entity_type="employee",
            entity_id=employee.id,
            details={"user_id": user.id},
        )
    db.commit()

    return {"message": "Employee deactivated successfully"}
