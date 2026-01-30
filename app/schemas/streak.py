from pydantic import BaseModel
from datetime import date
from typing import Optional


class StreakResponse(BaseModel):
    streak: int
    last_active_date: Optional[date] = None
    motivation: str
