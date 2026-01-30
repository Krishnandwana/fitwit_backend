from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.food_log import FoodLog
from app.models.weight_log import WeightLog
import random


MOTIVATIONAL_MESSAGES = [
    "Go dawg!",
    "You showed up again.",
    "Consistency > talent.",
    "Keep stacking wins.",
    "Proud of you.",
    "Daily reps make legends.",
    "Keep going!",
    "Consistency beats intensity.",
    "You're building momentum.",
    "Every day counts.",
    "One day at a time.",
    "You're on fire!",
]


def calculate_streak(user_id: int, db: Session) -> dict:
    """
    Calculate user's streak based on consecutive days of logging.

    A day counts as "active" if the user has logged either:
    - Body weight OR
    - Food/calories

    Args:
        user_id: User ID
        db: Database session

    Returns:
        dict with streak count, last_active_date, and motivation message
    """
    today = date.today()
    streak = 0
    last_active_date = None

    # Check backwards from today
    current_date = today

    # Maximum days to check (prevent infinite loop)
    max_days = 365

    for _ in range(max_days):
        # Check if user has any activity on current_date
        has_food_log = db.query(FoodLog).filter(
            FoodLog.user_id == user_id,
            FoodLog.date == current_date
        ).first() is not None

        has_weight_log = db.query(WeightLog).filter(
            WeightLog.user_id == user_id,
            WeightLog.date == current_date
        ).first() is not None

        is_active = has_food_log or has_weight_log

        if is_active:
            streak += 1
            if last_active_date is None:
                last_active_date = current_date
            # Move to previous day
            current_date -= timedelta(days=1)
        else:
            # Streak broken
            break

    # Get motivational message
    motivation = get_motivational_message(streak)

    return {
        "streak": streak,
        "last_active_date": last_active_date,
        "motivation": motivation
    }


def get_motivational_message(streak: int) -> str:
    """
    Get a motivational message based on streak count.

    Args:
        streak: Current streak count

    Returns:
        Motivational message string
    """
    if streak == 0:
        return "Start your journey today!"
    elif streak == 1:
        return "Great start! Keep it up."
    elif streak >= 100:
        return "LEGENDARY! 100+ days!"
    elif streak >= 50:
        return "Unstoppable! 50+ days strong."
    elif streak >= 30:
        return "One month strong! Amazing!"
    elif streak >= 7:
        return "Full week! You're crushing it."
    else:
        # Random motivational message for 2-6 day streaks
        return random.choice(MOTIVATIONAL_MESSAGES)
