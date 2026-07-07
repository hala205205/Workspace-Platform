from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator

from app.core.types import TargetType
from app.core.time import require_timezone


class TargetInput(BaseModel):
    target_type: TargetType
    target_id: str


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10)
    is_global: bool = True
    is_pinned: bool = False
    requires_acknowledgement: bool = False
    comments_enabled: bool = True
    publish_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    targets: list[TargetInput] = []

    @model_validator(mode="after")
    def validate_dates_and_targets(self):
        require_timezone(self.publish_at, "publish_at")
        require_timezone(self.expires_at, "expires_at")
        if self.expires_at and self.expires_at <= self.publish_at:
            raise ValueError("expires_at must be later than publish_at")
        if not self.is_global and not self.targets:
            raise ValueError("Targeted announcements require at least one target")
        return self


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    content: str | None = Field(default=None, min_length=10)
    is_global: bool | None = None
    is_pinned: bool | None = None
    requires_acknowledgement: bool | None = None
    comments_enabled: bool | None = None
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    targets: list[TargetInput] | None = None

    @model_validator(mode="after")
    def validate_timezones(self):
        require_timezone(self.publish_at, "publish_at")
        require_timezone(self.expires_at, "expires_at")
        return self


class AttachmentResponse(BaseModel):
    id: str
    original_name: str
    content_type: str
    size_bytes: int
    model_config = {"from_attributes": True}


class AnnouncementResponse(BaseModel):
    id: str
    title: str
    content: str
    is_global: bool
    is_pinned: bool
    requires_acknowledgement: bool
    comments_enabled: bool
    sender_id: str
    publish_at: datetime
    expires_at: datetime | None
    created_at: datetime
    attachments: list[AttachmentResponse] = []
    model_config = {"from_attributes": True}


class ReactionCreate(BaseModel):
    reaction_type: str = Field(min_length=1, max_length=32)


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CommentResponse(BaseModel):
    id: str
    announcement_id: str
    user_id: str
    user_name: str
    content: str
    created_at: datetime


class AcknowledgementReport(BaseModel):
    eligible_user_ids: list[str]
    acknowledged_user_ids: list[str]
    pending_user_ids: list[str]
