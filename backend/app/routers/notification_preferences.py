from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.employee import Employee
from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.schemas.notification_preference import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

router = APIRouter(
    prefix="/notification-preferences",
    tags=["Notification Preferences and Broadcasts"],
)


def preference_enabled(db: Session, user_id: int, notification_type: str) -> bool:
    preference = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id,
        NotificationPreference.notification_type == notification_type,
    ).first()
    return preference is None or preference.is_enabled


@router.get("/", response_model=list[NotificationPreferenceResponse])
def list_preferences(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id
    ).order_by(NotificationPreference.notification_type.asc()).all()


@router.put("/", response_model=NotificationPreferenceResponse)
def update_preference(
    data: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    preference = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == current_user.id,
        NotificationPreference.notification_type == data.notification_type,
    ).first()

    if preference is None:
        preference = NotificationPreference(
            user_id=current_user.id,
            notification_type=data.notification_type,
            is_enabled=data.is_enabled,
        )
        db.add(preference)
    else:
        preference.is_enabled = data.is_enabled

    db.commit()
    db.refresh(preference)
    return preference


@router.post("/broadcast")
def broadcast_notification(
    title: str = Query(min_length=1, max_length=200),
    message: str = Query(min_length=1),
    notification_type: str = Query(default="announcement", max_length=50),
    department: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    if department is not None:
        employees = db.query(Employee).filter(
            Employee.department == department
        ).all()
        user_ids = {employee.user_id for employee in employees}
    else:
        user_ids = {
            user.id
            for user in db.query(User).filter(User.is_active.is_(True)).all()
        }

    if not user_ids:
        raise HTTPException(
            status_code=404,
            detail="No active recipients found for the selected target",
        )

    users = db.query(User).filter(
        User.id.in_(user_ids),
        User.is_active.is_(True),
    ).all()

    notifications = []
    skipped = 0

    for user in users:
        if not preference_enabled(db, user.id, notification_type):
            skipped += 1
            continue

        notifications.append(
            Notification(
                user_id=user.id,
                title=title,
                message=message,
                notification_type=notification_type,
            )
        )

    if notifications:
        db.add_all(notifications)

    db.commit()

    return {
        "message": "Broadcast processed",
        "target": "department" if department else "organization",
        "department": department,
        "recipient_count": len(notifications),
        "skipped_by_preferences": skipped,
    }
