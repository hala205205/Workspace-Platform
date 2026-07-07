from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import SourceType, TargetType
from app.modules.announcements.models import SystemTarget
from app.modules.users.models import User


def audience_condition(user: User, source_type: SourceType, source_id_column):
    clauses = [
        (SystemTarget.source_type == source_type) &
        (SystemTarget.source_id == source_id_column) &
        (SystemTarget.target_type == TargetType.USER) &
        (SystemTarget.target_id == user.id)
    ]
    if user.department_id:
        clauses.append(
            (SystemTarget.source_type == source_type) &
            (SystemTarget.source_id == source_id_column) &
            (SystemTarget.target_type == TargetType.DEPARTMENT) &
            (SystemTarget.target_id == user.department_id)
        )
    clauses.append(
        (SystemTarget.source_type == source_type) &
        (SystemTarget.source_id == source_id_column) &
        (SystemTarget.target_type == TargetType.ROLE) &
        (SystemTarget.target_id == user.role_id)
    )
    return or_(*clauses)


async def resolve_audience(
    db: AsyncSession,
    source_type: SourceType,
    source_id: str,
    is_global: bool,
    notifications_only: bool = False,
) -> list[User]:
    if is_global:
        query = select(User).where(User.is_active.is_(True))
    else:
        target_rows = list((await db.execute(
            select(SystemTarget).where(SystemTarget.source_type == source_type, SystemTarget.source_id == source_id)
        )).scalars())
        clauses = []
        for target in target_rows:
            if target.target_type == TargetType.USER:
                clauses.append(User.id == target.target_id)
            elif target.target_type == TargetType.DEPARTMENT:
                clauses.append(User.department_id == target.target_id)
            elif target.target_type == TargetType.ROLE:
                clauses.append(User.role_id == target.target_id)
        if not clauses:
            return []
        query = select(User).where(User.is_active.is_(True), or_(*clauses))
    if notifications_only:
        query = query.where(User.notifications_enabled.is_(True))
    return list((await db.execute(query)).scalars().unique())
