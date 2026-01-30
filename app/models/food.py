from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    calories_per_100g = Column(Float, nullable=False)
    protein = Column(Float, default=0.0)  # grams per 100g
    carbs = Column(Float, default=0.0)    # grams per 100g
    fat = Column(Float, default=0.0)      # grams per 100g
    barcode = Column(String, unique=True, index=True, nullable=True)
