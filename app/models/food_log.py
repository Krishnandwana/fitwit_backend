from sqlalchemy import Column, Integer, Float, Date, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    food_id = Column(Integer, ForeignKey("food_items.id"), nullable=False)
    weight_grams = Column(Float, nullable=False)
    calories = Column(Float, nullable=False)
    date = Column(Date, nullable=False, index=True, server_default=func.current_date())
    weight_method = Column(String, nullable=False, default="manual")  # "manual" or "ocr"

    # Relationships
    user = relationship("User")
    food = relationship("FoodItem")
