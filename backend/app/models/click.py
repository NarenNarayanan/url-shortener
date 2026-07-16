"""
Click model — one row per redirect event. This is the highest-volume table
in the system, so every column here earns its place: browser/os/device_type
are parsed from the user_agent ONCE, at write time (see the click-logging
background task in a later milestone), so analytics queries never need to
re-parse a UA string.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Click(Base):
    __tablename__ = "clicks"
    __table_args__ = (
        # Composite index: analytics queries filter by url_id and a timestamp
        # range (daily/weekly aggregation, "clicks over the last N days").
        Index("ix_clicks_url_id_timestamp", "url_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("urls.id", ondelete="CASCADE"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)  # raw string, kept for future re-parsing
    referrer: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Parsed at write time from user_agent:
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)
    os: Mapped[str | None] = mapped_column(String(50), nullable=True)
    device_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # desktop | mobile | tablet | other

    # Optional — populated later via GeoIP lookup if/when we wire that in.
    country: Mapped[str | None] = mapped_column(String(2), nullable=True)  # ISO 3166-1 alpha-2

    url: Mapped["URL"] = relationship(back_populates="clicks")
