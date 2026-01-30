from pydantic import BaseModel
from datetime import date
from typing import Optional


class FoodLogBase(BaseModel):
    food_id: int
    weight_grams: float
    weight_method: str = "manual"  # "manual" or "ocr"
    date: Optional[date] = None


class FoodLogCreate(FoodLogBase):
    pass


class FoodLog(FoodLogBase):
    id: int
    user_id: int
    calories: float
    date: date

    class Config:
        from_attributes = True


class FoodLogWithDetails(FoodLog):
    food_name: str
    protein: float
    carbs: float
    fat: float
