from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.food_log import FoodLog
from app.schemas.widget import WidgetData
from app.api.deps import get_current_user

router = APIRouter()

# Default calorie goal (can be made user-configurable later)
DEFAULT_CALORIE_GOAL = 2000


@router.get("/", response_model=WidgetData)
def get_widget_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get widget data for home screen widget."""
    today = date.today()

    # Get today's food logs
    food_logs = db.query(FoodLog).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.date == today
    ).all()

    # Calculate total calories consumed
    calories_consumed = sum([log.calories for log in food_logs])

    # Calculate calories remaining
    calorie_goal = DEFAULT_CALORIE_GOAL  # TODO: Make this user-configurable
    calories_remaining = calorie_goal - calories_consumed

    # Calculate percentage
    percentage = (calories_consumed / calorie_goal) * 100 if calorie_goal > 0 else 0

    return WidgetData(
        calories_consumed=round(calories_consumed, 2),
        calories_goal=calorie_goal,
        calories_remaining=round(calories_remaining, 2),
        percentage=round(percentage, 2),
        date=today.isoformat()
    )
