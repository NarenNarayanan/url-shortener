from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ClickBucket(BaseModel):
    period: datetime
    count: int


class BreakdownItem(BaseModel):
    label: str
    count: int


class URLAnalytics(BaseModel):
    short_code: str
    total_clicks: int
    group_by: Literal["day", "week"]
    clicks_over_time: list[ClickBucket]
    by_browser: list[BreakdownItem]
    by_os: list[BreakdownItem]
    by_device_type: list[BreakdownItem]
