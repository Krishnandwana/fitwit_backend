from pydantic import BaseModel
from typing import Optional


class FoodItemBase(BaseModel):
    name: str
    calories_per_100g: float
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    barcode: Optional[str] = None


class FoodItemCreate(FoodItemBase):
    pass


class FoodItem(FoodItemBase):
    id: int

    class Config:
        from_attributes = True


class FoodSearch(BaseModel):
    query: str


class BarcodeSearch(BaseModel):
    barcode: str


class FoodWeightOCRResponse(BaseModel):
    weight_grams: float
    confidence: str  # "high", "medium", "low"
    message: Optional[str] = None
