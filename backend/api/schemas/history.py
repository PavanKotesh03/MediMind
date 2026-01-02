from pydantic import BaseModel
from typing import List
from datetime import datetime


class SessionSummary(BaseModel):
    session_id: str
    title: str
    status: str
    created_at: datetime
    message_count: int


class GroupedHistory(BaseModel):
    today: List[SessionSummary]
    yesterday: List[SessionSummary]
    this_week: List[SessionSummary]
    this_month: List[SessionSummary]
    older: List[SessionSummary]
