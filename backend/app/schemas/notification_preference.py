from pydantic import BaseModel, ConfigDict, Field


class NotificationPreferenceUpdate(BaseModel):
    notification_type: str = Field(min_length=1, max_length=50)
    is_enabled: bool


class NotificationPreferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    notification_type: str
    is_enabled: bool
