from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.core.dependencies import get_current_user, require_permissions
from app.core.files import store_upload
from app.config.config import settings
from app.core.permissions import EVENT_CREATE, EVENT_DELETE, EVENT_EDIT
from app.core.types import CalendarLayer
from app.modules.calendar import services
from app.modules.calendar.models import Event, EventAttachment, EventRSVP
from app.modules.calendar.schemas import EventAttachmentResponse, EventCreate, EventResponse, EventUpdate, ReminderCreate, RSVPCreate
from app.modules.users.models import User

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.post("/events", response_model=EventResponse, status_code=201)
async def create_event(data: EventCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_permissions(EVENT_CREATE))):
    return await services.create(db, data, user.id)


@router.get("/events", response_model=list[EventResponse])
async def list_events(
    start: datetime | None = None,
    end: datetime | None = None,
    q: str | None = None,
    layer: CalendarLayer | None = None,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await services.list_visible(db, user, start, end, q, layer, limit, offset)


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    event = await services.get_visible(db, event_id, user)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(event_id: str, data: EventUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(EVENT_EDIT))):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        return await services.update(db, event, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(event_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(EVENT_DELETE))):
    event = await db.get(Event, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await services.delete_item(db, event)


@router.post("/events/{event_id}/rsvp")
async def rsvp(event_id: str, data: RSVPCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not await services.get_visible(db, event_id, user):
        raise HTTPException(status_code=404, detail="Event not found")
    item = (await db.execute(select(EventRSVP).where(EventRSVP.event_id == event_id, EventRSVP.user_id == user.id))).scalar_one_or_none()
    if item:
        item.status = data.status
    else:
        item = EventRSVP(event_id=event_id, user_id=user.id, status=data.status)
        db.add(item)
    await db.commit()
    return {"status": data.status}


@router.put("/events/{event_id}/reminder")
async def set_reminder(event_id: str, data: ReminderCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    event = await services.get_visible(db, event_id, user)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    try:
        reminder = await services.set_reminder(db, event, user.id, data.minutes_before)
        return {"scheduled_for": reminder.scheduled_for, "minutes_before": reminder.reminder_interval_minutes}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/events/{event_id}/attachments", response_model=EventAttachmentResponse, status_code=201)
async def upload_attachment(event_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(EVENT_EDIT))):
    if not await db.get(Event, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
    original, stored, content_type, size = await store_upload(file, "events")
    item = EventAttachment(event_id=event_id, original_name=original, stored_name=stored, content_type=content_type, size_bytes=size)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/events/{event_id}/attachments/{attachment_id}")
async def download_attachment(event_id: str, attachment_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not await services.get_visible(db, event_id, user):
        raise HTTPException(status_code=404, detail="Event not found")
    item = await db.get(EventAttachment, attachment_id)
    if not item or item.event_id != event_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = settings.upload_dir / "events" / item.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Attachment file not found")
    return FileResponse(path, media_type=item.content_type, filename=item.original_name)
