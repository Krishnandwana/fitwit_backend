from sqlalchemy import Column, Integer, Float, Date, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    weight = Column(Float, nullable=False)  # in kg
    date = Column(Date, nullable=False, index=True, server_default=func.current_date())
    method = Column(String, nullable=False, default="manual")  # "manual" or "ocr"

    # Relationship
    user = relationship("User")
