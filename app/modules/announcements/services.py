from datetime import datetime, timezone

from sqlalchemy import delete, exists, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import ROLE_MANAGE, USER_MANAGE
from app.core.targeting import audience_condition, resolve_audience
from app.core.types import SourceType
from app.modules.announcements.models import (
    Announcement, AnnouncementAcknowledgement, Comment, Reaction, SystemTarget,
)
from app.modules.announcements.schemas import AnnouncementCreate, AnnouncementUpdate, TargetInput
from app.modules.notifications.models import Notification
from app.modules.users.models import User


async def replace_targets(db: AsyncSession, source_id: str, targets: list[TargetInput]) -> None:
    await db.execute(delete(SystemTarget).where(SystemTarget.source_type == SourceType.ANNOUNCEMENT, SystemTarget.source_id == source_id))
    db.add_all([SystemTarget(source_type=SourceType.ANNOUNCEMENT, source_id=source_id, target_type=t.target_type, target_id=t.target_id) for t in targets])


async def notify_audience(db: AsyncSession, announcement: Announcement, kind: str) -> None:
    users = await resolve_audience(db, SourceType.ANNOUNCEMENT, announcement.id, announcement.is_global, notifications_only=True)
    db.add_all([
        Notification(user_id=user.id, kind=kind, title=announcement.title, body=announcement.content[:500], payload={"announcement_id": announcement.id})
        for user in users if user.id != announcement.sender_id
    ])


async def create(db: AsyncSession, data: AnnouncementCreate, sender_id: str) -> Announcement:
    values = data.model_dump(exclude={"targets"})
    item = Announcement(**values, sender_id=sender_id)
    db.add(item)
    await db.flush()
    await replace_targets(db, item.id, data.targets)
    await notify_audience(db, item, "announcement.created")
    await db.commit()
    await db.refresh(item)
    return item


def visible_query(user: User):
    now = datetime.now(timezone.utc)
    targeted = exists(select(SystemTarget.id).where(audience_condition(user, SourceType.ANNOUNCEMENT, Announcement.id)))
    audience_clause = true() if {USER_MANAGE, ROLE_MANAGE} & user.permission_keys else or_(
        Announcement.is_global.is_(True),
        targeted,
        Announcement.sender_id == user.id,
    )
    return select(Announcement).where(
        Announcement.publish_at <= now,
        or_(Announcement.expires_at.is_(None), Announcement.expires_at > now),
        audience_clause,
    )


async def get_visible(db: AsyncSession, announcement_id: str, user: User) -> Announcement | None:
    return (await db.execute(visible_query(user).where(Announcement.id == announcement_id))).scalar_one_or_none()


async def list_visible(db: AsyncSession, user: User, q: str | None, active_only: bool, limit: int, offset: int):
    query = visible_query(user)
    if q:
        query = query.where(or_(Announcement.title.ilike(f"%{q}%"), Announcement.content.ilike(f"%{q}%")))
    if not active_only:
        targeted = exists(select(SystemTarget.id).where(audience_condition(user, SourceType.ANNOUNCEMENT, Announcement.id)))
        audience_clause = true() if {USER_MANAGE, ROLE_MANAGE} & user.permission_keys else or_(
            Announcement.is_global.is_(True),
            targeted,
            Announcement.sender_id == user.id,
        )
        query = select(Announcement).where(
            Announcement.publish_at <= datetime.now(timezone.utc),
            audience_clause,
        )
    query = query.order_by(Announcement.is_pinned.desc(), Announcement.publish_at.desc()).limit(limit).offset(offset)
    return list((await db.execute(query)).scalars().unique())


async def update(db: AsyncSession, item: Announcement, data: AnnouncementUpdate) -> Announcement:
    values = data.model_dump(exclude_unset=True, exclude={"targets"})
    for key, value in values.items():
        setattr(item, key, value)
    if item.expires_at and item.expires_at <= item.publish_at:
        raise ValueError("expires_at must be later than publish_at")
    if data.targets is not None:
        await replace_targets(db, item.id, data.targets)
    await notify_audience(db, item, "announcement.updated")
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: Announcement) -> None:
    await db.execute(delete(SystemTarget).where(SystemTarget.source_type == SourceType.ANNOUNCEMENT, SystemTarget.source_id == item.id))
    await db.delete(item)
    await db.commit()


async def set_reaction(db: AsyncSession, announcement_id: str, user_id: str, value: str):
    result = await db.execute(select(Reaction).where(Reaction.announcement_id == announcement_id, Reaction.user_id == user_id))
    reaction = result.scalar_one_or_none()
    if reaction and reaction.reaction_type == value:
        await db.delete(reaction)
        await db.commit()
        return None
    if reaction:
        reaction.reaction_type = value
    else:
        reaction = Reaction(announcement_id=announcement_id, user_id=user_id, reaction_type=value)
        db.add(reaction)
    await db.commit()
    await db.refresh(reaction)
    return reaction


async def acknowledgement_report(db: AsyncSession, item: Announcement):
    eligible = await resolve_audience(db, SourceType.ANNOUNCEMENT, item.id, item.is_global)
    acknowledged = list((await db.execute(select(AnnouncementAcknowledgement.user_id).where(AnnouncementAcknowledgement.announcement_id == item.id))).scalars())
    eligible_ids = {user.id for user in eligible}
    acknowledged_ids = set(acknowledged)
    return sorted(eligible_ids), sorted(acknowledged_ids), sorted(eligible_ids - acknowledged_ids)
