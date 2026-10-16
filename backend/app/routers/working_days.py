from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.routers.auth import get_current_user
from app.services.working_days import count_working_days

router = APIRouter(
    prefix="/working-days",
    tags=["Working Day Calculation"],
)


@router.get("/")
def get_working_days(
    start_date: date,
    end_date: date,
    region: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if end_date < start_date:
        raise HTTPException(
            status_code=422,
            detail="end_date cannot be before start_date",
        )

    result = count_working_days(
        db=db,
        start_date=start_date,
        end_date=end_date,
        region=region.strip() if region else None,
    )

    return result
