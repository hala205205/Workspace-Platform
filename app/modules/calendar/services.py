from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, exists, false, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ROLE_MANAGE, USER_MANAGE
from app.core.targeting import audience_condition, resolve_audience
from app.core.time import ensure_utc
from app.core.types import CalendarLayer, SourceType, TargetType
from app.modules.announcements.models import SystemTarget
from app.modules.calendar.models import Event, EventRSVP, UserEventReminder
from app.modules.calendar.schemas import EventCreate, EventTargetInput, EventUpdate
from app.modules.notifications.models import Notification
from app.modules.users.models import User


async def replace_targets(db: AsyncSession, event_id: str, targets: list[EventTargetInput]) -> None:
    await db.execute(delete(SystemTarget).where(SystemTarget.source_type == SourceType.EVENT, SystemTarget.source_id == event_id))
    db.add_all([SystemTarget(source_type=SourceType.EVENT, source_id=event_id, target_type=t.target_type, target_id=t.target_id) for t in targets])


async def notify(db: AsyncSession, event: Event, kind: str) -> None:
    users = await resolve_audience(db, SourceType.EVENT, event.id, event.is_global, notifications_only=True)
    db.add_all([
        Notification(user_id=user.id, kind=kind, title=event.title, body=event.description or "", payload={"event_id": event.id})
        for user in users if user.id != event.creator_id
    ])


async def create(db: AsyncSession, data: EventCreate, creator_id: str) -> Event:
    values = data.model_dump(exclude={"targets"})
    if values.get("meeting_link") is not None:
        values["meeting_link"] = str(values["meeting_link"])
    event = Event(**values, creator_id=creator_id)
    db.add(event)
    await db.flush()
    await replace_targets(db, event.id, data.targets)
    await notify(db, event, "event.created")
    await db.commit()
    await db.refresh(event)
    return event


def visible_query(user: User):
    targeted = exists(select(SystemTarget.id).where(audience_condition(user, SourceType.EVENT, Event.id)))
    if {USER_MANAGE, ROLE_MANAGE} & user.permission_keys:
        return select(Event).where(true())
    return select(Event).where(or_(Event.is_global.is_(True), targeted, Event.creator_id == user.id))


async def get_visible(db: AsyncSession, event_id: str, user: User) -> Event | None:
    return (await db.execute(visible_query(user).where(Event.id == event_id))).scalar_one_or_none()


async def list_visible(db: AsyncSession, user: User, start: datetime | None, end: datetime | None, q: str | None, layer: CalendarLayer | None, limit: int, offset: int):
    query = visible_query(user)
    if start:
        query = query.where(Event.end_time >= start)
    if end:
        query = query.where(Event.start_time <= end)
    if q:
        query = query.where(or_(Event.title.ilike(f"%{q}%"), Event.description.ilike(f"%{q}%")))
    if layer == CalendarLayer.COMPANY:
        query = query.where(Event.is_global.is_(True))
    elif layer == CalendarLayer.TEAM and ({USER_MANAGE, ROLE_MANAGE} & user.permission_keys):
        department_target = exists(select(SystemTarget.id).where(
            SystemTarget.source_type == SourceType.EVENT,
            SystemTarget.source_id == Event.id,
            SystemTarget.target_type == TargetType.DEPARTMENT,
        ))
        query = query.where(department_target)
    elif layer == CalendarLayer.TEAM and user.department_id:
        team_target = exists(select(SystemTarget.id).where(
            SystemTarget.source_type == SourceType.EVENT,
            SystemTarget.source_id == Event.id,
            SystemTarget.target_type == TargetType.DEPARTMENT,
            SystemTarget.target_id == user.department_id,
        ))
        query = query.where(team_target)
    elif layer == CalendarLayer.TEAM:
        query = query.where(false())
    elif layer == CalendarLayer.MINE:
        rsvp = exists(select(EventRSVP.event_id).where(EventRSVP.event_id == Event.id, EventRSVP.user_id == user.id))
        query = query.where(or_(Event.creator_id == user.id, rsvp))
    return list((await db.execute(query.order_by(Event.start_time).limit(limit).offset(offset))).scalars().unique())


async def update(db: AsyncSession, event: Event, data: EventUpdate) -> Event:
    old_start = event.start_time
    values = data.model_dump(exclude_unset=True, exclude={"targets"})
    if values.get("meeting_link") is not None:
        values["meeting_link"] = str(values["meeting_link"])
    for key, value in values.items():
        setattr(event, key, value)
    if event.end_time <= event.start_time:
        raise ValueError("end_time must be later than start_time")
    if data.targets is not None:
        await replace_targets(db, event.id, data.targets)
    if event.start_time != old_start:
        reminders = list((await db.execute(select(UserEventReminder).where(UserEventReminder.event_id == event.id))).scalars())
        for reminder in reminders:
            reminder.scheduled_for = event.start_time - timedelta(minutes=reminder.reminder_interval_minutes)
            reminder.is_sent = False
    await notify(db, event, "event.updated")
    await db.commit()
    await db.refresh(event)
    return event


async def delete_item(db: AsyncSession, event: Event) -> None:
    await notify(db, event, "event.cancelled")
    await db.execute(delete(SystemTarget).where(SystemTarget.source_type == SourceType.EVENT, SystemTarget.source_id == event.id))
    await db.delete(event)
    await db.commit()


async def set_reminder(db: AsyncSession, event: Event, user_id: str, minutes: int) -> UserEventReminder:
    scheduled = ensure_utc(event.start_time) - timedelta(minutes=minutes)
    if scheduled <= datetime.now(timezone.utc):
        raise ValueError("Reminder time must be in the future")
    result = await db.execute(select(UserEventReminder).where(UserEventReminder.event_id == event.id, UserEventReminder.user_id == user_id))
    reminder = result.scalar_one_or_none()
    if reminder:
        reminder.reminder_interval_minutes = minutes
        reminder.scheduled_for = scheduled
        reminder.is_sent = False
    else:
        reminder = UserEventReminder(event_id=event.id, user_id=user_id, reminder_interval_minutes=minutes, scheduled_for=scheduled)
        db.add(reminder)
    await db.commit()
    await db.refresh(reminder)
    return reminder
