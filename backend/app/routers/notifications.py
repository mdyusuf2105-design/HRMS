from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse
from app.routers.auth import get_current_user, require_roles

router = APIRouter(prefix="/notifications", tags=["Notifications"])

def notification_preference_enabled(db: Session, user_id: int, notification_type: str) -> bool:
    from app.models.notification_preference import NotificationPreference

    preference = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id,
        NotificationPreference.notification_type == notification_type,
    ).first()
    return preference is None or preference.is_enabled




@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Notification).filter(
        Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).count()

    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id,
    ).first()

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.patch("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    ).update({Notification.is_read: True}, synchronize_session=False)

    db.commit()
    return {"message": "All notifications marked as read"}


@router.post("/", response_model=NotificationResponse, status_code=201)
def create_notification(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "general",
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    from app.models.user import User

    recipient = db.query(User).filter(User.id == user_id).first()
    if recipient is None:
        raise HTTPException(status_code=404, detail="Recipient user not found")

    if not notification_preference_enabled(db, user_id, notification_type):
        raise HTTPException(
            status_code=409,
            detail="Recipient has disabled this notification category",
        )

    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
