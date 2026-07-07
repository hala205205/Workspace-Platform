from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, model_validator

from app.core.types import LocationType, RSVPStatus, TargetType
from app.core.time import require_timezone


class EventTargetInput(BaseModel):
    target_type: TargetType
    target_id: str


class EventCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    location_type: LocationType
    physical_location: str | None = Field(default=None, max_length=255)
    meeting_link: HttpUrl | None = None
    is_global: bool = True
    announcement_id: str | None = None
    targets: list[EventTargetInput] = []

    @model_validator(mode="after")
    def validate_event(self):
        require_timezone(self.start_time, "start_time")
        require_timezone(self.end_time, "end_time")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be later than start_time")
        if not self.is_global and not self.targets:
            raise ValueError("Targeted events require at least one target")
        if self.location_type in {LocationType.ONLINE, LocationType.HYBRID} and not self.meeting_link:
            raise ValueError("meeting_link is required for online or hybrid events")
        if self.location_type in {LocationType.PHYSICAL, LocationType.HYBRID} and not self.physical_location:
            raise ValueError("physical_location is required for physical or hybrid events")
        return self


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    location_type: LocationType | None = None
    physical_location: str | None = None
    meeting_link: HttpUrl | None = None
    is_global: bool | None = None
    announcement_id: str | None = None
    targets: list[EventTargetInput] | None = None

    @model_validator(mode="after")
    def validate_timezones(self):
        require_timezone(self.start_time, "start_time")
        require_timezone(self.end_time, "end_time")
        return self


class EventAttachmentResponse(BaseModel):
    id: str
    original_name: str
    content_type: str
    size_bytes: int
    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: str
    title: str
    description: str | None
    creator_id: str
    start_time: datetime
    end_time: datetime
    location_type: LocationType
    physical_location: str | None
    meeting_link: str | None
    is_global: bool
    announcement_id: str | None
    created_at: datetime
    attachments: list[EventAttachmentResponse] = []
    model_config = {"from_attributes": True}


class RSVPCreate(BaseModel):
    status: RSVPStatus


class ReminderCreate(BaseModel):
    minutes_before: int = Field(ge=5, le=10080)
