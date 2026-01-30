from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app.database import get_db
from app.models.user import User
from app.models.food_log import FoodLog
from app.models.weight_log import WeightLog
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_current_user
from app.services.gemini import chat_with_gemini
from app.core.streak import calculate_streak

router = APIRouter()


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat with AI nutrition coach."""
    # Gather user context
    user_context = {}

    # Get streak
    streak_data = calculate_streak(current_user.id, db)
    user_context["streak"] = streak_data["streak"]

    # Get recent weight
    recent_weight = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id
    ).order_by(WeightLog.date.desc()).first()

    if recent_weight:
        user_context["recent_weight"] = recent_weight.weight

    # Get weight trend (last 7 days)
    weight_logs = db.query(WeightLog).filter(
        WeightLog.user_id == current_user.id
    ).order_by(WeightLog.date.desc()).limit(7).all()

    if len(weight_logs) >= 2:
        avg_recent = sum([log.weight for log in weight_logs[:3]]) / min(3, len(weight_logs))
        avg_older = sum([log.weight for log in weight_logs[-3:]]) / min(3, len(weight_logs))
        diff = avg_recent - avg_older

        if diff < -0.5:
            user_context["weight_trend"] = "decreasing (good job!)"
        elif diff > 0.5:
            user_context["weight_trend"] = "increasing"
        else:
            user_context["weight_trend"] = "stable"

    # Get today's calories
    today_logs = db.query(FoodLog).filter(
        FoodLog.user_id == current_user.id,
        FoodLog.date == date.today()
    ).all()

    if today_logs:
        total_calories = sum([log.calories for log in today_logs])
        user_context["calories_today"] = round(total_calories, 2)

    # Get response from Gemini
    response_text = chat_with_gemini(
        message=request.message,
        history=request.history,
        user_context=user_context
    )

    return ChatResponse(response=response_text)
