from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.streak import StreakResponse
from app.api.deps import get_current_user
from app.core.streak import calculate_streak

router = APIRouter()


@router.get("/", response_model=StreakResponse)
def get_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's current streak."""
    streak_data = calculate_streak(current_user.id, db)

    return StreakResponse(
        streak=streak_data["streak"],
        last_active_date=streak_data["last_active_date"],
        motivation=streak_data["motivation"]
    )
