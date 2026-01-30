from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class WeightLogBase(BaseModel):
    weight: float  # in kg
    method: str = "manual"  # "manual" or "ocr"
    date: Optional[date] = None


class WeightLogCreate(WeightLogBase):
    pass


class WeightLog(WeightLogBase):
    id: int
    user_id: int
    date: date

    class Config:
        from_attributes = True


class WeightOCRResponse(BaseModel):
    weight: float  # in kg
    confidence: str  # "high", "medium", "low"
    message: Optional[str] = None


class WeightStats(BaseModel):
    lowest: float
    highest: float
    average: float
    current: Optional[float] = None
    change_from_start: Optional[float] = None
    trend: str  # "increasing", "decreasing", "stable"


class WeightHistory(BaseModel):
    logs: List[WeightLog]
    stats: WeightStats
