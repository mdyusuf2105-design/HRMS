from calendar import monthrange
from datetime import date

from sqlalchemy.orm import Session

from app.models.holiday import Holiday


def count_working_days(
    db: Session,
    start_date: date,
    end_date: date,
    region: str | None = None,
) -> dict:
    if end_date < start_date:
        raise ValueError("end_date cannot be before start_date")

    holidays = (
        db.query(Holiday)
        .filter(
            Holiday.is_active.is_(True),
            Holiday.holiday_date >= start_date,
            Holiday.holiday_date <= end_date,
            Holiday.holiday_type.in_(["company", "regional"]),
        )
        .all()
    )

    holiday_dates = set()

    for holiday in holidays:
        if holiday.holiday_type == "company":
            holiday_dates.add(holiday.holiday_date)
        elif holiday.holiday_type == "regional":
            if region and holiday.region == region:
                holiday_dates.add(holiday.holiday_date)

    total_days = (end_date - start_date).days + 1
    weekend_days = 0
    working_days = 0

    current_date = start_date

    while current_date <= end_date:
        if current_date.weekday() >= 5:
            weekend_days += 1
        elif current_date not in holiday_dates:
            working_days += 1

        current_date = date.fromordinal(current_date.toordinal() + 1)

    return {
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "total_calendar_days": total_days,
        "weekend_days": weekend_days,
        "applicable_holiday_days": len(holiday_dates),
        "working_days": working_days,
    }
