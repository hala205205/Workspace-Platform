import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config.db import Base
from app.core.types import SourceType, TargetType


def uuid_str() -> str:
    return str(uuid.uuid4())


class SystemTarget(Base):
    __tablename__ = "system_targets"
    __table_args__ = (
        UniqueConstraint("source_type", "source_id", "target_type", "target_id", name="uq_system_target"),
        Index("ix_system_targets_lookup", "source_type", "source_id"),
        Index("ix_system_targets_audience", "target_type", "target_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    source_id: Mapped[str] = mapped_column(String(36))
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType))
    target_id: Mapped[str] = mapped_column(String(36))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Announcement(Base):
    __tablename__ = "announcements"
    __table_args__ = (Index("ix_announcements_feed", "is_pinned", "publish_at", "expires_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    is_global: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_acknowledgement: Mapped[bool] = mapped_column(Boolean, default=False)
    comments_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sender_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    publish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    attachments: Mapped[list["AnnouncementAttachment"]] = relationship(cascade="all, delete-orphan", lazy="selectin")


class AnnouncementAttachment(Base):
    __tablename__ = "announcement_attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    announcement_id: Mapped[str] = mapped_column(ForeignKey("announcements.id", ondelete="CASCADE"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    stored_name: Mapped[str] = mapped_column(String(255), unique=True)
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint("announcement_id", "user_id", name="uq_reaction_user_announcement"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    announcement_id: Mapped[str] = mapped_column(ForeignKey("announcements.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    reaction_type: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AnnouncementAcknowledgement(Base):
    __tablename__ = "announcement_acknowledgements"
    __table_args__ = (UniqueConstraint("announcement_id", "user_id", name="uq_ack_user_announcement"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    announcement_id: Mapped[str] = mapped_column(ForeignKey("announcements.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Comment(Base):
    __tablename__ = "announcement_comments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    announcement_id: Mapped[str] = mapped_column(ForeignKey("announcements.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
