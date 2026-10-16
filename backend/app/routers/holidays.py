from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.holiday import Holiday
from app.routers.auth import get_current_user, require_roles
from app.schemas.holiday import (
    HolidayCreate,
    HolidayResponse,
    HolidayUpdate,
)

router = APIRouter(prefix="/holidays", tags=["Holiday Management"])


@router.post(
    "/",
    response_model=HolidayResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_holiday(
    data: HolidayCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    holiday = Holiday(
        name=data.name.strip(),
        holiday_date=data.holiday_date,
        holiday_type=data.holiday_type,
        region=data.region.strip() if data.region else None,
        description=data.description,
        is_active=data.is_active,
        created_by=current_user.id,
    )

    if not holiday.name:
        raise HTTPException(status_code=422, detail="Holiday name is required")

    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


@router.get("/", response_model=list[HolidayResponse])
def list_holidays(
    start_date: date | None = None,
    end_date: date | None = None,
    holiday_type: str | None = Query(
        default=None,
        pattern="^(company|regional|optional)$",
    ),
    region: str | None = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Holiday)

    # Employees can only see active holidays.
    if current_user.role == "employee" or not include_inactive:
        query = query.filter(Holiday.is_active.is_(True))

    if start_date:
        query = query.filter(Holiday.holiday_date >= start_date)
    if end_date:
        query = query.filter(Holiday.holiday_date <= end_date)
    if holiday_type:
        query = query.filter(Holiday.holiday_type == holiday_type)
    if region:
        query = query.filter(Holiday.region == region)

    return query.order_by(Holiday.holiday_date.asc()).all()


@router.get("/{holiday_id}", response_model=HolidayResponse)
def get_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Holiday).filter(Holiday.id == holiday_id)

    if current_user.role == "employee":
        query = query.filter(Holiday.is_active.is_(True))

    holiday = query.first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")

    return holiday


@router.patch("/{holiday_id}", response_model=HolidayResponse)
def update_holiday(
    holiday_id: int,
    data: HolidayUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()

    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")

    updates = data.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field == "name" and value is not None:
            value = value.strip()
            if not value:
                raise HTTPException(
                    status_code=422,
                    detail="Holiday name is required",
                )
        if field == "region" and value is not None:
            value = value.strip() or None
        setattr(holiday, field, value)

    if holiday.holiday_type == "regional" and not holiday.region:
        raise HTTPException(
            status_code=422,
            detail="Region is required for a regional holiday",
        )

    db.commit()
    db.refresh(holiday)
    return holiday


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()

    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")

    holiday.is_active = False
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
