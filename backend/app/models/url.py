"""
URL model — a shortened link owned by a user.
"""
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    short_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Denormalized for fast dashboard reads — see Milestone 1 design notes.
    # Must be updated via an atomic SQL increment, never read-modify-write in Python.
    click_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    last_clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped["User"] = relationship(back_populates="urls")
    clicks: Mapped[list["Click"]] = relationship(back_populates="url", cascade="all, delete-orphan")

    @property
    def is_expired(self) -> bool:
        """
        Expiration is computed on read, not stored as a flag — there's no
        background job that has to run correctly to keep a status column in sync.
        """
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
