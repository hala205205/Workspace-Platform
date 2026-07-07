from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.db import get_db
from app.core.dependencies import get_current_user, require_permissions
from app.core.files import store_upload
from app.config.config import settings
from app.core.permissions import (
    ANNOUNCEMENT_CREATE, ANNOUNCEMENT_DELETE, ANNOUNCEMENT_EDIT, ANNOUNCEMENT_PIN, ANNOUNCEMENT_REPORT,
)
from app.modules.announcements import services
from app.modules.announcements.models import Announcement, AnnouncementAcknowledgement, AnnouncementAttachment, Comment
from app.modules.announcements.schemas import (
    AcknowledgementReport, AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate,
    AttachmentResponse, CommentCreate, CommentResponse, ReactionCreate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.post("", response_model=AnnouncementResponse, status_code=201)
async def create(data: AnnouncementCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_permissions(ANNOUNCEMENT_CREATE))):
    return await services.create(db, data, user.id)


@router.get("", response_model=list[AnnouncementResponse])
async def list_items(
    q: str | None = None,
    active_only: bool = True,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await services.list_visible(db, user, q, active_only, limit, offset)


@router.get("/{announcement_id}", response_model=AnnouncementResponse)
async def get_item(announcement_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    item = await services.get_visible(db, announcement_id, user)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return item


@router.patch("/{announcement_id}", response_model=AnnouncementResponse)
async def update_item(announcement_id: str, data: AnnouncementUpdate, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ANNOUNCEMENT_EDIT))):
    item = await db.get(Announcement, announcement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return await services.update(db, item, data)


@router.delete("/{announcement_id}", status_code=204)
async def delete_item(announcement_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ANNOUNCEMENT_DELETE))):
    item = await db.get(Announcement, announcement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    await services.delete_item(db, item)


@router.patch("/{announcement_id}/pin", response_model=AnnouncementResponse)
async def toggle_pin(announcement_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ANNOUNCEMENT_PIN))):
    item = await db.get(Announcement, announcement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    item.is_pinned = not item.is_pinned
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/{announcement_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_attachment(announcement_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ANNOUNCEMENT_EDIT))):
    if not await db.get(Announcement, announcement_id):
        raise HTTPException(status_code=404, detail="Announcement not found")
    original, stored, content_type, size = await store_upload(file, "announcements")
    item = AnnouncementAttachment(announcement_id=announcement_id, original_name=original, stored_name=stored, content_type=content_type, size_bytes=size)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.get("/{announcement_id}/attachments/{attachment_id}")
async def download_attachment(announcement_id: str, attachment_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not await services.get_visible(db, announcement_id, user):
        raise HTTPException(status_code=404, detail="Announcement not found")
    item = await db.get(AnnouncementAttachment, attachment_id)
    if not item or item.announcement_id != announcement_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    path = settings.upload_dir / "announcements" / item.stored_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Attachment file not found")
    return FileResponse(path, media_type=item.content_type, filename=item.original_name)


@router.post("/{announcement_id}/reactions")
async def react(announcement_id: str, data: ReactionCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not await services.get_visible(db, announcement_id, user):
        raise HTTPException(status_code=404, detail="Announcement not found")
    result = await services.set_reaction(db, announcement_id, user.id, data.reaction_type)
    return {"status": "removed" if result is None else "saved"}


@router.get("/{announcement_id}/comments", response_model=list[CommentResponse])
async def list_comments(announcement_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if not await services.get_visible(db, announcement_id, user):
        raise HTTPException(status_code=404, detail="Announcement not found")
    rows = (await db.execute(
        select(Comment, User.name)
        .join(User, User.id == Comment.user_id)
        .where(Comment.announcement_id == announcement_id)
        .order_by(Comment.created_at.asc())
    )).all()
    return [
        CommentResponse(
            id=comment.id,
            announcement_id=comment.announcement_id,
            user_id=comment.user_id,
            user_name=user_name,
            content=comment.content,
            created_at=comment.created_at,
        )
        for comment, user_name in rows
    ]


@router.post("/{announcement_id}/comments", response_model=CommentResponse, status_code=201)
async def comment(announcement_id: str, data: CommentCreate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    item = await services.get_visible(db, announcement_id, user)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if not item.comments_enabled:
        raise HTTPException(status_code=409, detail="Comments are disabled")
    comment_item = Comment(announcement_id=announcement_id, user_id=user.id, content=data.content.strip())
    db.add(comment_item)
    await db.commit()
    await db.refresh(comment_item)
    return CommentResponse(
        id=comment_item.id,
        announcement_id=comment_item.announcement_id,
        user_id=comment_item.user_id,
        user_name=user.name,
        content=comment_item.content,
        created_at=comment_item.created_at,
    )


@router.post("/{announcement_id}/acknowledgements", status_code=201)
async def acknowledge(announcement_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    item = await services.get_visible(db, announcement_id, user)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    if not item.requires_acknowledgement:
        raise HTTPException(status_code=409, detail="Announcement does not require acknowledgement")
    existing = await db.scalar(select(AnnouncementAcknowledgement.id).where(AnnouncementAcknowledgement.announcement_id == announcement_id, AnnouncementAcknowledgement.user_id == user.id))
    if not existing:
        db.add(AnnouncementAcknowledgement(announcement_id=announcement_id, user_id=user.id))
        await db.commit()
    return {"status": "acknowledged"}


@router.get("/{announcement_id}/acknowledgements/report", response_model=AcknowledgementReport)
async def report(announcement_id: str, db: AsyncSession = Depends(get_db), _: User = Depends(require_permissions(ANNOUNCEMENT_REPORT))):
    item = await db.get(Announcement, announcement_id)
    if not item:
        raise HTTPException(status_code=404, detail="Announcement not found")
    eligible, acknowledged, pending = await services.acknowledgement_report(db, item)
    return AcknowledgementReport(eligible_user_ids=eligible, acknowledged_user_ids=acknowledged, pending_user_ids=pending)
