import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.config.db import async_session
from app.modules.calendar.models import Event, UserEventReminder
from app.modules.notifications.models import Notification


async def dispatch_due_reminders() -> int:
    async with async_session() as db:
        query = (
            select(UserEventReminder, Event)
            .join(Event, Event.id == UserEventReminder.event_id)
            .where(UserEventReminder.is_sent.is_(False), UserEventReminder.scheduled_for <= datetime.now(timezone.utc))
        )
        rows = (await db.execute(query)).all()
        for reminder, event in rows:
            db.add(Notification(
                user_id=reminder.user_id,
                kind="event.reminder",
                title=event.title,
                body=f"Event starts at {event.start_time.isoformat()}",
                payload={"event_id": event.id},
                delivered_at=datetime.now(timezone.utc),
            ))
            reminder.is_sent = True
        await db.commit()
        return len(rows)


if __name__ == "__main__":
    print(asyncio.run(dispatch_due_reminders()))
