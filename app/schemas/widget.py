from pydantic import BaseModel
from typing import Optional


class WidgetData(BaseModel):
    calories_consumed: float
    calories_goal: float
    calories_remaining: float
    percentage: float
    date: str
