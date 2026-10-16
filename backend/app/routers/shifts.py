from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.employee import Employee
from app.models.shift import DepartmentShift, EmployeeShift, Shift
from app.routers.auth import get_current_user, require_roles
from app.schemas.shift import (
    DepartmentShiftCreate,\n    DepartmentShiftResponse,\n    DepartmentShiftCreate,\n    DepartmentShiftResponse,\n    EmployeeShiftCreate,
    EmployeeShiftResponse,
    ShiftCreate,
    ShiftResponse,
    ShiftUpdate,
)

router = APIRouter(prefix="/shifts", tags=["Shift Management"])


@router.post("/", response_model=ShiftResponse, status_code=status.HTTP_201_CREATED)
def create_shift(
    data: ShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    name = data.name.strip()

    if db.query(Shift).filter(Shift.name == name).first():
        raise HTTPException(status_code=409, detail="Shift name already exists")

    shift = Shift(
        name=name,
        start_time=data.start_time,
        end_time=data.end_time,
        grace_period_minutes=data.grace_period_minutes,
        is_active=data.is_active,
        created_by=current_user.id,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


@router.get("/", response_model=list[ShiftResponse])
def list_shifts(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Shift)

    if current_user.role == "employee" or not include_inactive:
        query = query.filter(Shift.is_active.is_(True))

    return query.order_by(Shift.start_time.asc()).all()


@router.get("/{shift_id}", response_model=ShiftResponse)
def get_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Shift).filter(Shift.id == shift_id)

    if current_user.role == "employee":
        query = query.filter(Shift.is_active.is_(True))

    shift = query.first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift


@router.patch("/{shift_id}", response_model=ShiftResponse)
def update_shift(
    shift_id: int,
    data: ShiftUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    changes = data.model_dump(exclude_unset=True)

    if "name" in changes and changes["name"] is not None:
        changes["name"] = changes["name"].strip()
        if not changes["name"]:
            raise HTTPException(status_code=422, detail="Shift name is required")
        duplicate = db.query(Shift).filter(
            Shift.name == changes["name"],
            Shift.id != shift_id,
        ).first()
        if duplicate:
            raise HTTPException(status_code=409, detail="Shift name already exists")

    start_time = changes.get("start_time", shift.start_time)
    end_time = changes.get("end_time", shift.end_time)
    if start_time is not None and end_time is not None and start_time == end_time:
        raise HTTPException(
            status_code=422,
            detail="Shift start and end times cannot be equal",
        )

    for field, value in changes.items():
        setattr(shift, field, value)

    db.commit()
    db.refresh(shift)
    return shift


@router.delete("/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_shift(
    shift_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    shift.is_active = False
    db.commit()


@router.post(
    "/assignments",
    response_model=EmployeeShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_shift(
    data: EmployeeShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    employee = db.query(Employee).filter(Employee.id == data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    shift = db.query(Shift).filter(
        Shift.id == data.shift_id,
        Shift.is_active.is_(True),
    ).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Active shift not found")

    assignment = EmployeeShift(
        employee_id=data.employee_id,
        shift_id=data.shift_id,
        assigned_by=current_user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get(
    "/assignments/employee/{employee_id}",
    response_model=list[EmployeeShiftResponse],
)
def get_employee_shifts(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role == "employee":
        own_employee = db.query(Employee).filter(
            Employee.user_id == current_user.id
        ).first()
        if not own_employee or own_employee.id != employee_id:
            raise HTTPException(status_code=403, detail="Access denied")

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    return (
        db.query(EmployeeShift)
        .filter(EmployeeShift.employee_id == employee_id)
        .order_by(EmployeeShift.assigned_at.desc())
        .all()
    )


@router.post(
    "/department-assignments",
    response_model=DepartmentShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_department_shift(
    data: DepartmentShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    department = data.department.strip()
    if not department:
        raise HTTPException(status_code=422, detail="Department is required")
    if data.effective_to and data.effective_to < data.effective_from:
        raise HTTPException(status_code=422, detail="End date cannot precede start date")

    shift = db.query(Shift).filter(
        Shift.id == data.shift_id,
        Shift.is_active.is_(True),
    ).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Active shift not found")

    assignment = DepartmentShift(
        department=department,
        shift_id=data.shift_id,
        assigned_by=current_user.id,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get(
    "/department-assignments",
    response_model=list[DepartmentShiftResponse],
)
def list_department_shift_assignments(
    department: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(DepartmentShift)
    if department:
        query = query.filter(DepartmentShift.department == department.strip())
    return query.order_by(
        DepartmentShift.effective_from.desc(),
        DepartmentShift.assigned_at.desc(),
    ).all()


@router.post(
    "/department-assignments",
    response_model=DepartmentShiftResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_department_shift(
    data: DepartmentShiftCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    department = data.department.strip()
    if not department:
        raise HTTPException(status_code=422, detail="Department is required")
    if data.effective_to and data.effective_to < data.effective_from:
        raise HTTPException(status_code=422, detail="End date cannot precede start date")

    shift = db.query(Shift).filter(
        Shift.id == data.shift_id,
        Shift.is_active.is_(True),
    ).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Active shift not found")

    assignment = DepartmentShift(
        department=department,
        shift_id=data.shift_id,
        assigned_by=current_user.id,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get(
    "/department-assignments",
    response_model=list[DepartmentShiftResponse],
)
def list_department_shift_assignments(
    department: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(DepartmentShift)
    if department:
        query = query.filter(DepartmentShift.department == department.strip())
    return query.order_by(
        DepartmentShift.effective_from.desc(),
        DepartmentShift.assigned_at.desc(),
    ).all()
